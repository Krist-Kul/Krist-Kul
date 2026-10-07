"""Convert source-prepped.png into a monochrome ASCII portrait SVG that types itself in row by row.

Usage: python scripts/make_ascii_svg.py  -> writes ascii-portrait.svg
Set STATIC=1 to emit a frozen, fully printed frame (handy for local previews).
"""
import os
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "ascii-portrait.svg"

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space clears the background
COLS = 64
CROP_BOTTOM = 0.62  # keep head + shoulders; a full-length dark jacket prints as a solid blob
CELL_W, CELL_H = 6.6, 12.0  # monospace cell; the ratio corrects for tall glyphs
FONT_SIZE = 11
PAD = 16
BG, FG, CURSOR = "#0d1117", "#c9d1d9", "#39d353"
ROW_STAGGER, ROW_DUR = 0.11, 0.18  # seconds
STATIC = os.environ.get("STATIC") == "1"


def to_grid() -> list[str]:
    img = np.array(Image.open(SRC).convert("L"))
    # Crop to the subject (anything not near-white) with a small margin.
    ys, xs = np.where(img < 245)
    m = 8
    y0, y1 = max(ys.min() - m, 0), min(ys.max() + m, img.shape[0])
    x0, x1 = max(xs.min() - m, 0), min(xs.max() + m, img.shape[1])
    y1 = y0 + round((y1 - y0) * CROP_BOTTOM)
    crop = Image.fromarray(img[y0:y1, x0:x1])

    rows = round(COLS * crop.height / crop.width * CELL_W / CELL_H)
    small = np.array(crop.resize((COLS, rows), Image.LANCZOS), dtype=np.float32)
    # Rank-equalize subject cells so every glyph in the ramp gets used; background stays blank.
    subject = small < 240
    darkness = np.zeros_like(small)
    ranks = (255.0 - small[subject]).argsort().argsort()
    darkness[subject] = (ranks + 1) / (ranks.size + 1)
    idx = (darkness * len(RAMP)).astype(int).clip(0, len(RAMP) - 1)
    idx[subject] = idx[subject].clip(1)
    return ["".join(RAMP[i] for i in row).rstrip() for row in idx]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    lines = to_grid()
    w = round(COLS * CELL_W + PAD * 2)
    h = round(len(lines) * CELL_H + PAD * 2)
    full_w = COLS * CELL_W

    defs, body = [], []
    t = 0.3
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        y = PAD + (i + 1) * CELL_H - 3
        top = PAD + i * CELL_H
        text_len = len(line) * CELL_W
        x0 = PAD + (len(line) - len(line.lstrip())) * CELL_W  # wipe starts at the first glyph
        text = (
            f'<text x="{PAD}" y="{y:.1f}" textLength="{text_len:.1f}" lengthAdjust="spacingAndGlyphs"'
            f' xml:space="preserve">{esc(line)}</text>'
        )
        if STATIC:
            body.append(text)
            continue
        begin = f"{t:.2f}s"
        row_w = PAD + text_len - x0
        # Base width is the full row and the animation starts at 0s holding 0 until this row's turn, so a
        # renderer that never runs SMIL still shows the finished portrait instead of a blank box.
        total = t + ROW_DUR
        defs.append(
            f'<clipPath id="r{i}"><rect x="{x0:.1f}" y="{top:.1f}" width="{row_w:.1f}" height="{CELL_H}">'
            f'<animate attributeName="width" values="0;0;{row_w:.1f}" keyTimes="0;{t / total:.4f};1" begin="0s" dur="{total:.2f}s" fill="freeze"/>'
            f"</rect></clipPath>"
        )
        body.append(f'<g clip-path="url(#r{i})">{text}</g>')
        body.append(
            f'<rect x="{x0:.1f}" y="{top + 1:.1f}" width="{CELL_W:.1f}" height="{CELL_H - 2}" fill="{CURSOR}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{begin}"/>'
            f'<animate attributeName="x" from="{x0:.1f}" to="{PAD + text_len:.1f}" begin="{begin}" dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{t + ROW_DUR:.2f}s"/>'
            f"</rect>"
        )
        t += ROW_STAGGER

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="ASCII portrait">
<defs>{''.join(defs)}</defs>
<rect width="{w}" height="{h}" rx="10" fill="{BG}"/>
<g fill="{FG}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace" font-size="{FONT_SIZE}">
{chr(10).join(body)}
</g>
</svg>
"""
    OUT.write_text(svg)
    print(f"wrote {OUT.relative_to(ROOT)} ({COLS}x{len(lines)}, {full_w:.0f}px grid)")


if __name__ == "__main__":
    main()
