"""Prep a photo for ASCII conversion -> source-prepped.png

    python scripts/prep_photo.py path/to/photo.jpg

1. remove the background (rembg) so only the subject remains
2. boost local contrast with CLAHE so a flatly-lit face gets real shadows/highlights
3. composite onto pure white (alpha kept as a 2nd channel) so the background maps to blanks
"""
import os
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source-prepped.png"
CROP_WIDTH = float(os.environ.get("CROP_WIDTH", "0.62"))   # crop width / subject height; larger = more shoulders


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python scripts/prep_photo.py <photo>")
    img = Image.open(sys.argv[1]).convert("RGB")
    img.thumbnail((2000, 2000))   # bound the long side; keep tall phone shots sharp

    try:
        from rembg import new_session, remove
        # u2net = salient-object model (~170 MB): it isolates the main subject and
        # ignores most bystanders. rembg's newest default is ~1 GB and can run out of memory.
        rgba = remove(img, session=new_session(os.environ.get("REMBG_MODEL", "u2net")))
    except ImportError:
        print("rembg not installed - skipping background removal")
        rgba = img.convert("RGBA")

    rgba = np.array(rgba)
    gray = cv2.cvtColor(rgba[..., :3], cv2.COLOR_RGB2GRAY)
    alpha = rgba[..., 3].astype(np.float32) / 255.0

    # keep only the main subject: a morphological opening detaches blobs that hang
    # on by a narrow neck (e.g. a bystander's head peeking over a shoulder). Big
    # detached pieces get erased; small ones (cap brim, ears, fingers) are kept.
    solid = (alpha > 0.5).astype(np.uint8)
    k = max(9, min(alpha.shape) // 14) | 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    opened = cv2.morphologyEx(solid, cv2.MORPH_OPEN, kernel)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(opened)
    if n > 1:
        biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        body = (labels == biggest).astype(np.uint8)
        cut = solid & (1 - body)
        m, clabels, cstats, _ = cv2.connectedComponentsWithStats(cut)
        erase = np.zeros_like(solid)
        for j in range(1, m):
            if cstats[j, cv2.CC_STAT_AREA] > 0.012 * body.sum():
                erase |= (clabels == j).astype(np.uint8)
        erase = cv2.dilate(erase, np.ones((5, 5), np.uint8)) & (1 - body)
        alpha *= 1.0 - cv2.GaussianBlur(erase.astype(np.float32), (7, 7), 0)
        alpha[(labels != biggest) & (alpha < 0.5)] = 0   # faint halo from other stuff

    clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray).astype(np.float32)

    # white background, then crop to the subject's bounding box.
    # The alpha mask rides along as a second channel so the ASCII step knows
    # exactly where the subject is (white highlights != background).
    out = gray * alpha + 255.0 * (1.0 - alpha)
    a8 = alpha * 255.0
    ys, xs = np.where(alpha > 0.5)
    if len(xs):
        # head-and-shoulders crop centred on the head (the top ~18% of the subject)
        top = ys.min()
        subj_h = ys.max() - top
        head_x = int(xs[ys < top + 0.18 * subj_h].mean())
        width = int(min(xs.max() - xs.min(), CROP_WIDTH * subj_h))
        left = int(np.clip(head_x - width // 2, 0, out.shape[1] - width))
        top = max(top - 12, 0)
        bottom = min(top + int(width * 0.95), out.shape[0])   # ~ the ASCII grid's shape
        out, a8 = out[top:bottom, left:left + width], a8[top:bottom, left:left + width]

    la = np.dstack([out, a8]).clip(0, 255).astype(np.uint8)
    Image.fromarray(la, "LA").save(OUT)
    print(f"-> {OUT.name}")


if __name__ == "__main__":
    main()
