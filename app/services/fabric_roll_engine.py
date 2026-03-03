from PIL import Image
import math
import os

def generate_fabric_roll(
    sample_path: str,
    output_path: str,
    width_m: float,
    height_m: float,
    dpi: int
):

    inches_per_meter = 39.3701
    width_px = int(width_m * inches_per_meter * dpi)
    height_px = int(height_m * inches_per_meter * dpi)

    # Reduce safety limit (careful)
    Image.MAX_IMAGE_PIXELS = None

    sample = Image.open(sample_path).convert("RGB")
    sample_w, sample_h = sample.size

    # Create image in vertical strips
    strip_height = 5000  # safe chunk size
    final_image = Image.new("RGB", (width_px, height_px))

    for y_start in range(0, height_px, strip_height):

        current_strip_height = min(strip_height, height_px - y_start)
        strip = Image.new("RGB", (width_px, current_strip_height))

        tiles_x = math.ceil(width_px / sample_w)
        tiles_y = math.ceil(current_strip_height / sample_h)

        for x in range(tiles_x):
            for y in range(tiles_y):
                pos_x = x * sample_w
                pos_y = y * sample_h
                strip.paste(sample, (pos_x, pos_y))

        strip = strip.crop((0, 0, width_px, current_strip_height))
        final_image.paste(strip, (0, y_start))

    final_image.save(output_path, dpi=(dpi, dpi), format="TIFF", compression="tiff_lzw")

    return output_path




# from PIL import Image
# import math
# import os

# def generate_fabric_roll(
#     sample_path: str,
#     output_path: str,
#     width_m: float = 1.0,
#     height_m: float = 2.0,
#     dpi: int = 600
# ):

#     inches_per_meter = 39.3701

#     width_inches = width_m * inches_per_meter
#     height_inches = height_m * inches_per_meter

#     width_px = int(width_inches * dpi)
#     height_px = int(height_inches * dpi)

#     # Load sample
#     sample = Image.open(sample_path).convert("RGB")

#     sample_w, sample_h = sample.size

#     # Calculate how many tiles needed
#     tiles_x = math.ceil(width_px / sample_w)
#     tiles_y = math.ceil(height_px / sample_h)

#     # Create large canvas
#     fabric = Image.new("RGB", (width_px, height_px))

#     for x in range(tiles_x):
#         for y in range(tiles_y):
#             pos_x = x * sample_w
#             pos_y = y * sample_h
#             fabric.paste(sample, (pos_x, pos_y))

#     # Crop exact size
#     fabric = fabric.crop((0, 0, width_px, height_px))

#     fabric.save(output_path, dpi=(dpi, dpi))

#     return output_path