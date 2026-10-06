"""Hand-authored neofetch-style info card -> info-card.svg

    python scripts/make_info_card.py
    STATIC=1 python scripts/make_info_card.py   # frozen frame for previews

Edit INFO below - it's the story your contribution graph can't tell.
Rows with an empty key continue the row above.
"""
import os
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

USER, HOST = "mohammad", "hamarsheh"
INFO = [
    ("Name",     "Mohammad Hamarsheh"),
    ("Location", "Sweden"),
    ("Bio",      "Creating impact, changing perspectives"),
    ("Stack",    "Python, TypeScript, Dart, Java, Swift, Rust"),
    ("Projects", "Promptly: QGIS plugin, LLM prompt -> Python"),
    ("",         "Traffic Surveillance: IoT, Flask, Docker, K8s"),
    ("",         "backend-challenge: Google Workspace events"),
    ("",         "one-shoter: a better way to one-shot a task"),
    ("Web",      "mhamarsheh.com"),
    ("LinkedIn", "in/mohhamarsheh"),
]

W, H = 735, 539                 # displays at 490 wide -> same height as the portrait
FS, LH = 17, 30
X, KEY_W, TOP = 30, 112, 92
BG, BORDER, FG, DIM = "#0d1117", "#30363d", "#c9d1d9", "#7d8590"
KEY = "#39d353"
SWATCHES = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0",
            "#ff7b72", "#d2a8ff", "#79c0ff", "#e3b341"]
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
STAGGER = 0.12


def line(i: int, inner: str) -> str:
    style = "" if STATIC else f' style="animation-delay:{0.3 + i * STAGGER:.2f}s"'
    return f'<g class="l"{style}>{inner}</g>'


def main() -> None:
    out, i = [], 0
    title = (f'<text x="{X}" y="{TOP}"><tspan class="k b">{USER}</tspan>'
             f'<tspan class="d">@</tspan><tspan class="k b">{HOST}</tspan></text>')
    out.append(line(i, title)); i += 1
    rule = "-" * (len(USER) + 1 + len(HOST))
    out.append(line(i, f'<text x="{X}" y="{TOP + LH * 0.8:.0f}" class="d">{rule}</text>')); i += 1

    y = TOP + LH * 1.8
    for key, val in INFO:
        k = f'<text x="{X}" y="{y:.0f}" class="k b">{escape(key)}</text>' if key else ""
        v = f'<text x="{X + KEY_W}" y="{y:.0f}">{escape(val)}</text>'
        out.append(line(i, k + v)); i += 1
        y += LH

    y += LH * 0.3
    sw = "".join(
        f'<rect x="{X + n * 30}" y="{y:.0f}" width="26" height="16" rx="3" fill="{c}"/>'
        for n, c in enumerate(SWATCHES)
    )
    out.append(line(i, sw))

    anim = "" if STATIC else """
  .l{opacity:0;animation:in .4s ease-out forwards}
  @keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"""

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
  text{{font-family:{FONT};font-size:{FS}px;fill:{FG}}}
  .k{{fill:{KEY}}} .b{{font-weight:700}} .d{{fill:{DIM}}}
  .t{{font-size:18px;fill:{DIM}}}{anim}
</style>
<rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="15" fill="{BG}" stroke="{BORDER}" stroke-width="1.5"/>
<circle cx="30" cy="27" r="7.5" fill="#ff5f56"/><circle cx="55" cy="27" r="7.5" fill="#ffbd2e"/><circle cx="80" cy="27" r="7.5" fill="#27c93f"/>
<text x="{W / 2}" y="33.5" class="t" text-anchor="middle">neofetch</text>
{"".join(out)}
</svg>'''
    OUT.write_text(svg)
    print(f"-> {OUT.name}")


if __name__ == "__main__":
    main()
