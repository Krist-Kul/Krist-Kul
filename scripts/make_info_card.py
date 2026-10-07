"""Render a neofetch-style info card SVG whose lines print in one after another.

Usage: python scripts/make_info_card.py  -> writes info-card.svg
Set STATIC=1 to emit a frozen frame (handy for local previews).
Edit USER / ROWS below to change what the card says.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

USER = "krist@github"
# (key, value) rows; a value may be a list to wrap across several lines. None = blank spacer.
ROWS = [
    ("Name", "Krist Kul"),
    ("Now", "Your current role @ Company"),
    ("Prev", "Previous role @ Company"),
    ("Location", "City, Country"),
    None,
    ("Stack", ["Python · TypeScript · Go", "React · Node · PostgreSQL", "Docker · AWS · GitHub Actions"]),
    None,
    ("Highlights", ["Shipped something you're proud of", "Won / built / led something notable", "Open-source thing people use"]),
    None,
    ("Contact", "you@example.com"),
]

W = 560
PAD_X, PAD_TOP = 22, 54
LINE_H = 22
KEY_W = 118
BG, BAR, FG, MUTED, TITLE = "#0d1117", "#161b22", "#c9d1d9", "#8b949e", "#39d353"
KEY_COLORS = ["#58a6ff", "#d2a8ff", "#ff7b72", "#ffa657", "#79c0ff", "#7ee787"]
SWATCHES = ["#484f58", "#ff7b72", "#7ee787", "#ffa657", "#58a6ff", "#d2a8ff", "#79c0ff", "#c9d1d9"]
STAGGER, START = 0.12, 0.4


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    lines: list[str] = []  # each entry is the inner SVG of one printed line
    y = PAD_TOP

    def add(inner: str) -> None:
        nonlocal y
        lines.append(f'<g transform="translate(0 {y})">{inner}</g>')
        y += LINE_H

    add(f'<text x="{PAD_X}" fill="{TITLE}" font-weight="700">{esc(USER)}</text>')
    add(f'<text x="{PAD_X}" fill="{MUTED}">{"-" * len(USER)}</text>')

    color_i = 0
    for row in ROWS:
        if row is None:
            y += LINE_H // 2
            continue
        key, value = row
        values = value if isinstance(value, list) else [value]
        color = KEY_COLORS[color_i % len(KEY_COLORS)]
        color_i += 1
        for j, v in enumerate(values):
            k = f'<text x="{PAD_X}" fill="{color}" font-weight="700">{esc(key)}</text>' if j == 0 else ""
            bullet = "› " if len(values) > 1 else ""
            add(f'{k}<text x="{PAD_X + KEY_W}" fill="{FG}">{esc(bullet + v)}</text>')

    y += LINE_H // 2
    sw = "".join(
        f'<rect x="{PAD_X + i * 30}" y="-13" width="26" height="16" rx="3" fill="{c}"/>' for i, c in enumerate(SWATCHES)
    )
    add(sw)
    h = y + 4

    styled = []
    for i, inner in enumerate(lines):
        cls = "" if STATIC else f' class="ln" style="animation-delay:{START + i * STAGGER:.2f}s"'
        styled.append(f"<g{cls}>{inner}</g>")

    css = (
        ""
        if STATIC
        else """<style>
.ln{opacity:0;animation:in .45s ease-out forwards}
@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:translateX(0)}}
</style>"""
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="{esc(USER)} info card">
{css}
<rect width="{W}" height="{h}" rx="10" fill="{BG}"/>
<path d="M0 10a10 10 0 0 1 10-10h{W - 20}a10 10 0 0 1 10 10v20h-{W}z" fill="{BAR}"/>
<circle cx="20" cy="15" r="5.5" fill="#ff5f56"/><circle cx="38" cy="15" r="5.5" fill="#ffbd2e"/><circle cx="56" cy="15" r="5.5" fill="#27c93f"/>
<text x="{W / 2}" y="19.5" text-anchor="middle" fill="{MUTED}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="12">~ neofetch</text>
<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace" font-size="14">
{chr(10).join(styled)}
</g>
</svg>
"""
    OUT.write_text(svg)
    print(f"wrote {OUT.relative_to(ROOT)} ({W}x{h})")


if __name__ == "__main__":
    main()
