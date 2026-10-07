"""Render data/contributions.json as an animated 53-week contribution heatmap SVG.

Usage: python scripts/render_heatmap_svg.py  -> writes contrib-heatmap.svg
Set STATIC=1 to emit a frozen frame (handy for local previews).
"""
import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#          none -> brightest (level 5 is a neon top end for the busiest days)
BG, FG, MUTED = "#0d1117", "#c9d1d9", "#8b949e"
W = 860
CELL, STEP = 12, 15
LEFT, TOP = 46, 44
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
DIAG_DELAY, START = 0.022, 0.3  # seconds per diagonal step


def level_of(day: dict, top_cut: int) -> int:
    if day["count"] and day["count"] >= top_cut:
        return 5
    return day["level"]


def main() -> None:
    data = json.loads(SRC.read_text())
    days = data["days"]

    nonzero = sorted(d["count"] for d in days if d["count"])
    # Top ~5% of active days get the neon level; never fewer than 2 contributions.
    top_cut = max(nonzero[int(len(nonzero) * 0.95)], 2) if nonzero else 10**9

    first = date.fromisoformat(days[0]["date"])
    sunday0 = first.toordinal() - (first.weekday() + 1) % 7

    cells, months = [], []
    last_month = None
    weeks = 0
    for d in days:
        dt = date.fromisoformat(d["date"])
        week, dow = divmod(dt.toordinal() - sunday0, 7)
        weeks = max(weeks, week + 1)
        x, y = LEFT + week * STEP, TOP + dow * STEP
        if dow == 0 and dt.month != last_month:
            if dt.day <= 7 and week < 52:
                months.append(f'<text x="{x}" y="{TOP - 10}">{dt.strftime("%b")}</text>')
            last_month = dt.month
        lvl = level_of(d, top_cut)
        anim = "" if STATIC else f' class="c" style="animation-delay:{START + (week + dow) * DIAG_DELAY:.3f}s"'
        tip = f"{d['count']} contribution{'s' if d['count'] != 1 else ''} on {d['date']}"
        cells.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{PALETTE[lvl]}"{anim}><title>{tip}</title></rect>'
        )

    grid_bottom = TOP + 7 * STEP
    day_labels = "".join(
        f'<text x="{LEFT - 10}" y="{TOP + i * STEP + CELL - 2}" text-anchor="end">{n}</text>'
        for i, n in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )

    legend_y = grid_bottom + 14
    right = LEFT + weeks * STEP - (STEP - CELL)
    lx = right - len(PALETTE) * STEP - 34
    legend = (
        f'<text x="{lx - 8}" y="{legend_y + CELL - 2}" text-anchor="end">Less</text>'
        + "".join(
            f'<rect x="{lx + i * STEP}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="3" fill="{c}"/>'
            for i, c in enumerate(PALETTE)
        )
        + f'<text x="{lx + len(PALETTE) * STEP + 4}" y="{legend_y + CELL - 2}">More</text>'
    )

    best = data["best_day"]
    best_label = date.fromisoformat(best["date"]).strftime("%b %-d")
    stats = (
        f'<tspan fill="{FG}" font-weight="700">{data["total"]:,}</tspan> contributions in the last year'
        f'  ·  current streak <tspan fill="{FG}">{data["current_streak"]}d</tspan>'
        f'  ·  longest <tspan fill="{FG}">{data["longest_streak"]}d</tspan>'
        f'  ·  best day <tspan fill="{FG}">{best["count"]}</tspan> ({best_label})'
    )
    h = legend_y + CELL + 22

    css = (
        ""
        if STATIC
        else """<style>
.c{transform-box:fill-box;transform-origin:center;animation:drop .5s cubic-bezier(.2,.8,.2,1) both}
@keyframes drop{from{opacity:0;transform:translateY(-10px) scale(.6)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.c{animation:none}}
</style>"""
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="{data['total']} contributions in the last year">
{css}
<rect width="{W}" height="{h}" rx="10" fill="{BG}"/>
<g font-family="{FONT}" font-size="11" fill="{MUTED}">
{''.join(months)}
{day_labels}
<text x="{LEFT}" y="{legend_y + CELL - 2}">{stats}</text>
{legend}
</g>
<g>
{chr(10).join(cells)}
</g>
</svg>
"""
    OUT.write_text(svg)
    print(f"wrote {OUT.relative_to(ROOT)} ({weeks} weeks, neon cut >= {top_cut})")


if __name__ == "__main__":
    main()
