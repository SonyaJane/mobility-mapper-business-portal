#!/usr/bin/env python3
#  python scripts\split_image_4x4.py media\other\image.png media\other
"""
Split an input image into a 4x4 grid and save each tile as "other_i.png" in the output directory.
Usage:
    python split_image_4x4.py <input_image> [output_dir]

Example:
    python split_image_4x4.py media/verification_photos/large_image.png media/verification_photos/others
"""
import os
import sys
from PIL import Image

def split_image(input_path, output_dir, rows=4, cols=4, prefix='other'):
    img = Image.open(input_path)
    width, height = img.size
    tile_w = width // cols
    tile_h = height // rows

    os.makedirs(output_dir, exist_ok=True)

    count = 1
    for row in range(rows):
        for col in range(cols):
            left = col * tile_w
            upper = row * tile_h
            # For last tile in row/column, include remainder pixels
            right = (col + 1) * tile_w if col < cols - 1 else width
            lower = (row + 1) * tile_h if row < rows - 1 else height

            tile = img.crop((left, upper, right, lower))
            filename = f"{prefix}_{count}.png"
            out_path = os.path.join(output_dir, filename)
            tile.save(out_path)
            print(f"Saved {out_path}")
            count += 1

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    input_image = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(input_image)[0] + '_tiles'
    split_image(input_image, output_dir)
