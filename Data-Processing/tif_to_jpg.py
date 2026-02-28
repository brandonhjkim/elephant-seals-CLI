"""
TIF to JPG Converter
This script converts all TIF/TIFF files in a specified directory to JPG format.
"""

from PIL import Image
import os
from pathlib import Path


def convert_tif_to_jpg(input_dir, output_dir=None, quality=100):

    input_path = Path(input_dir)

    if not input_path.exists():
        print(f"Error: Directory '{input_dir}' does not exist.")
        return

    if not input_path.is_dir():

        input_path = input_path.parent
        print(f"Using parent directory: {input_path}")

    if output_dir is None:
        output_path = input_path
    else:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

    tif_files = list(input_path.glob('*.tif')) + list(input_path.glob('*.tiff')) + \
                list(input_path.glob('*.TIF')) + list(input_path.glob('*.TIFF'))

    if not tif_files:
        print(f"No TIF files found in '{input_path}'")
        return

    print(f"Found {len(tif_files)} TIF file(s) to convert")
    print(f"Output directory: {output_path}")
    print("-" * 50)

    converted = 0
    for tif_file in tif_files:
        try:

            with Image.open(tif_file) as img:

                if img.mode in ('RGBA', 'LA', 'P'):

                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                output_file = output_path / f"{tif_file.stem}.jpg"

                img.save(output_file, 'JPEG', quality=quality, optimize=True)

                print(f"✓ Converted: {tif_file.name} -> {output_file.name}")
                converted += 1

        except Exception as e:
            print(f"✗ Error converting {tif_file.name}: {str(e)}")

    print("-" * 50)
    print(f"Conversion complete: {converted}/{len(tif_files)} files converted successfully")


if __name__ == "__main__":
    # Your directory path
    directory = "/Users/danielalvarezmorales/Documents/WINTER 2026/DATA 451/Classified 2"

    output_directory = "/Users/danielalvarezmorales/Documents/WINTER 2026/DATA 451/Classified2_Converted"


    convert_tif_to_jpg(directory, output_directory, quality=100)