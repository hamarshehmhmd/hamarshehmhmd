"""data/contributions.json -> contrib-heatmap.svg (animated with CSS keyframes, no JS)"""
import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"   # STATIC=1 -> frozen frame for previews

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#          none -> brightest (level 5 = neon top end, top 5% of active days)
BG, BORDER, FG, DIM = "#0d1117", "#30363d", "#c9d1d9", "#7d8590"
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"

CELL, GAP = 12, 3
PITCH = CELL + GAP
W = 860
LEFT, TOP = 46, 64


def main() -> None:
    d = json.loads(DATA.read_text())
    days = d["days"]
    first = date.fromisoformat(days[0]["date"])
    start_offset = (first.weekday() + 1) % 7          # Sunday = row 0

    counts = sorted(x["count"] for x in days if x["count"] > 0)
    neon = counts[int(len(counts) * 0.95)] if len(counts) >= 20 else 10**9

    cells, months, last_month = [], [], None
    for i, day in enumerate(days):
        wk, wd = divmod(i + start_offset, 7)
        lvl = 5 if 0 < day["count"] >= neon else day["level"]
        x, y = LEFT + wk * PITCH, TOP + wd * PITCH
        delay = (wk + wd) * 0.018                     # diagonal sweep
        style = "" if STATIC else f' style="animation-delay:{delay:.3f}s"'
        cells.append(
            f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{PALETTE[lvl]}"{style}><title>{day["count"]} on {day["date"]}</title></rect>'
        )
        dt = date.fromisoformat(day["date"])
        if wd == 0 and dt.day <= 7 and dt.month != last_month:
            months.append(f'<text x="{x}" y="{TOP - 8}" class="m">{dt.strftime("%b")}</text>')
            last_month = dt.month

    grid_bottom = TOP + 7 * PITCH
    H = grid_bottom + 62
    wdays = "".join(
        f'<text x="{LEFT - 8}" y="{TOP + r * PITCH + 10}" class="m" text-anchor="end">{n}</text>'
        for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )

    ly = grid_bottom + 14
    lx = W - 52 - len(PALETTE) * PITCH
    legend = f'<text x="{lx - 8}" y="{ly + 10}" class="m" text-anchor="end">Less</text>'
    legend += "".join(
        f'<rect x="{lx + i * PITCH}" y="{ly}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(PALETTE)
    )
    legend += f'<text x="{lx + len(PALETTE) * PITCH + 4}" y="{ly + 10}" class="m">More</text>'

    best = d["best_day"]
    stats = (
        f'<text x="{LEFT}" y="{ly + 10}" class="s"><tspan class="g">{d["total"]:,}</tspan>'
        f' contributions in the last year</text>'
        f'<text x="{LEFT}" y="{ly + 30}" class="m" xml:space="preserve">current streak {d["current_streak"]}d   '
        f'longest {d["longest_streak"]}d   best day {best["count"]} ({best["date"]})   '
        f'updated {d["generated"]}</text>'
    )

    anim = "" if STATIC else """
  .c{opacity:0;transform-box:fill-box;transform-origin:center;
     animation:drop .45s cubic-bezier(.2,.8,.3,1) forwards}
  @keyframes drop{from{opacity:0;transform:translateY(-6px) scale(.6)}
                  to{opacity:1;transform:none}}"""

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
  text{{font-family:{FONT}}}
  .m{{font-size:10.5px;fill:{DIM}}}
  .s{{font-size:12.5px;fill:{FG}}}
  .g{{fill:{PALETTE[4]};font-weight:700}}
  .t{{font-size:12px;fill:{DIM}}}{anim}
</style>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>
<circle cx="20" cy="18" r="5" fill="#ff5f56"/><circle cx="37" cy="18" r="5" fill="#ffbd2e"/><circle cx="54" cy="18" r="5" fill="#27c93f"/>
<text x="{W / 2}" y="22" class="t" text-anchor="middle">{d["username"]}: ~/contributions</text>
{"".join(months)}{wdays}
{"".join(cells)}
{legend}
{stats}
</svg>'''
    OUT.write_text(svg)
    print(f"{len(days)} days -> {OUT.name}")


if __name__ == "__main__":
    main()
