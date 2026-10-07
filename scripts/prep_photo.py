"""Prep a photo for ASCII conversion: remove background, boost local contrast, flatten onto white.

Usage: python scripts/prep_photo.py source-photo.jpg  -> writes source-prepped.png
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "source-photo.jpg"
    out = ROOT / "source-prepped.png"

    cutout = remove(Image.open(src).convert("RGBA"))
    rgba = np.array(cutout)
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0

    gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
    # Lift shadows on a dark, backlit subject before local equalization.
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX, mask=(alpha > 0.5).astype(np.uint8))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray).astype(np.float32)

    # Composite onto white so the background maps to the blank end of the ramp.
    flat = gray * alpha + 255.0 * (1.0 - alpha)
    Image.fromarray(flat.clip(0, 255).astype(np.uint8), "L").save(out)
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
