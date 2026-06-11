#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow", "numpy"]
# ///
"""
sqify.py — normalize PNGs to 400x400 with 25px padding for fastfetch
Output files are prefixed with "sq_" in the same folder as the script.
Already-prefixed sq_*.png files are skipped automatically.
"""

import sys
import os
from pathlib import Path
from PIL import Image
import numpy as np

CANVAS = 400
PADDING = 25
CONTENT_SIZE = CANVAS - PADDING * 2  # 350


def sqify(src: Path) -> Path:
    with Image.open(src) as im:
        im = im.convert("RGBA")
        arr = np.array(im)
        alpha = arr[:, :, 3]

        # Find bounding box of non-transparent pixels
        rows = np.any(alpha > 0, axis=1)
        cols = np.any(alpha > 0, axis=0)

        if not rows.any():
            print(f"  [skip] {src.name} — fully transparent")
            return None

        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]

        # Crop to content
        content = im.crop((cmin, rmin, cmax + 1, rmax + 1))
        cw, ch = content.size

        # Scale to fit within CONTENT_SIZE x CONTENT_SIZE preserving aspect
        scale = min(CONTENT_SIZE / cw, CONTENT_SIZE / ch)
        new_w = round(cw * scale)
        new_h = round(ch * scale)
        content = content.resize((new_w, new_h), Image.LANCZOS)

        # Paste centred on a transparent 400x400 canvas
        canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
        x = (CANVAS - new_w) // 2
        y = (CANVAS - new_h) // 2
        canvas.paste(content, (x, y), content)

        out_name = "sq_" + src.name
        out_path = src.parent / out_name
        canvas.save(out_path, "PNG")
        return out_path


def main():
    script_dir = Path(__file__).parent

    # Collect PNGs in the same folder, skip ones already prefixed sq_
    targets = [
        p for p in sorted(script_dir.glob("*.png"))
        if not p.name.startswith("sq_")
    ]

    if not targets:
        print("No non-sq_ PNGs found next to the script.")
        sys.exit(0)

    print(f"Processing {len(targets)} file(s) → 400×400, {PADDING}px padding\n")
    for src in targets:
        out = sqify(src)
        if out:
            print(f"  ✓  {src.name}  →  {out.name}")

    print("\nDone.")


if __name__ == "__main__":
    main()
