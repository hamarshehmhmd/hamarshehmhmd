"""source-prepped.png -> ascii-portrait.svg (monochrome ASCII that types itself in, SMIL)

    python scripts/make_ascii_svg.py [image]      # default: source-prepped.png
    STATIC=1 python scripts/make_ascii_svg.py     # frozen frame for previews
"""
import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "source-prepped.png"
OUT = ROOT / "ascii-portrait.svg"
STATIC = os.environ.get("STATIC") == "1"

RAMP = " .`:-=+*cs#%@"   # sparse -> dense; leading space = background only
MAX_COLS, MAX_ROWS = 120, 64
FS = 9.2                 # font size
CW, LH = FS * 0.6, FS    # monospace cell: 0.6em wide, 1em tall
W_EST = 20 * 2 + MAX_COLS * CW
PAD_X, PAD_TOP, PAD_BOT = 20, 72, 22
S = W_EST / 370          # displayed at 370px: scale window chrome to match the other panels
FILL = "#c9d1d9"
BG, BORDER, DIM = "#0d1117", "#30363d", "#7d8590"
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
ROW_DELAY, ROW_DUR = 0.055, 0.3


def to_rows(path: Path) -> list[str]:
    src = Image.open(path)
    if src.mode in ("LA", "RGBA", "PA"):
        alpha = src.getchannel("A")
    else:                                   # no mask: treat pure white as background
        alpha = ImageOps.grayscale(src).point(lambda v: 0 if v > 245 else 255)
    img = ImageOps.grayscale(src.convert("RGB") if src.mode == "PA" else src.convert("LA").convert("L"))
    w, h = img.size
    # fit inside MAX_COLS x MAX_ROWS while correcting for the tall character cell
    cols = MAX_COLS
    rows = round(h / w * cols * CW / LH)
    if rows > MAX_ROWS:
        rows = MAX_ROWS
        cols = round(w / h * rows * LH / CW)
    px = np.asarray(img.resize((cols, rows), Image.LANCZOS), dtype=np.float32) / 255.0
    mask = np.asarray(alpha.resize((cols, rows), Image.LANCZOS), dtype=np.float32) / 255.0

    # light glyphs on a dark terminal: bright pixels get dense glyphs, so the
    # portrait reads as a positive image; outside the subject everything is blank
    inside = mask > 0.5
    lo, hi = np.percentile(px[inside], [2, 98]) if inside.any() else (0.0, 1.0)
    px = np.clip((px - lo) / max(hi - lo, 1e-3), 0, 1) ** 0.9
    idx = (px * (len(RAMP) - 2) + 1.5).astype(int).clip(1, len(RAMP) - 1)
    idx[~inside] = 0
    lines = ["".join(RAMP[i] for i in row) for row in idx]

    # center the subject horizontally in the full-width grid
    used = [i for i in range(cols) if inside[:, i].any()] or [0, cols - 1]
    shift = (MAX_COLS - (used[0] + used[-1] + 1)) // 2
    out = []
    for ln in lines:
        ln = " " * shift + ln if shift >= 0 else ln[-shift:]
        out.append(ln[:MAX_COLS].rstrip())
    return out


def main() -> None:
    if not SRC.exists():
        sys.exit(f"{SRC} not found - run scripts/prep_photo.py <photo> first")
    rows = to_rows(SRC)
    W = int(PAD_X * 2 + MAX_COLS * CW)
    H = int(PAD_TOP + MAX_ROWS * LH + PAD_BOT)
    y0 = PAD_TOP + (MAX_ROWS - len(rows)) * LH / 2

    defs, body = [], []
    for i, line in enumerate(rows):
        if not line.strip():
            continue
        y = y0 + i * LH
        full = len(line) * CW
        text = (f'<text x="{PAD_X}" y="{y + FS * 0.82:.1f}" textLength="{full:.1f}" '
                f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{escape(line)}</text>')
        if STATIC:
            body.append(text)
            continue
        b = f"{i * ROW_DELAY:.2f}s"
        defs.append(
            f'<clipPath id="r{i}"><rect x="{PAD_X}" y="{y:.1f}" width="0" height="{LH}">'
            f'<animate attributeName="width" from="0" to="{full:.1f}" begin="{b}" dur="{ROW_DUR}s" fill="freeze"/>'
            f'</rect></clipPath>'
        )
        body.append(f'<g clip-path="url(#r{i})">{text}</g>')
        # block cursor riding the wipe edge, hidden once the row is done
        body.append(
            f'<rect x="{PAD_X}" y="{y:.1f}" width="{CW:.1f}" height="{LH}" fill="{FILL}" opacity="0">'
            f'<set attributeName="opacity" to="0.85" begin="{b}"/>'
            f'<animate attributeName="x" from="{PAD_X}" to="{PAD_X + full:.1f}" begin="{b}" dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{i * ROW_DELAY + ROW_DUR:.2f}s"/>'
            f'</rect>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>text{{font-family:{FONT};font-size:{FS}px;fill:{FILL}}} .t{{font-size:{12 * S:.1f}px;fill:{DIM}}}</style>
<rect x="{S / 2:.2f}" y="{S / 2:.2f}" width="{W - S:.2f}" height="{H - S:.2f}" rx="{10 * S:.1f}" fill="{BG}" stroke="{BORDER}" stroke-width="{S:.2f}"/>
<circle cx="{20 * S:.1f}" cy="{18 * S:.1f}" r="{5 * S:.1f}" fill="#ff5f56"/><circle cx="{37 * S:.1f}" cy="{18 * S:.1f}" r="{5 * S:.1f}" fill="#ffbd2e"/><circle cx="{54 * S:.1f}" cy="{18 * S:.1f}" r="{5 * S:.1f}" fill="#27c93f"/>
<text x="{W / 2}" y="{22 * S:.1f}" class="t" text-anchor="middle">cat portrait.txt</text>
<defs>{"".join(defs)}</defs>
{"".join(body)}
</svg>'''
    OUT.write_text(svg)
    print(f"{len(rows)} rows -> {OUT.name} ({W}x{H})")


if __name__ == "__main__":
    main()
