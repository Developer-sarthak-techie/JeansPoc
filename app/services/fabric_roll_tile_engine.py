import os
import uuid
import math
import json
from PIL import Image
import numpy as np

TILE_SIZE = 512
ROLL_WIDTH_M = 1.0
ROLL_HEIGHT_M = 2.0


def generate_fabric_roll_tiles(texture_path, dpi=300):

    roll_id = str(uuid.uuid4())
    base_dir = f"fabric_rolls/{roll_id}"
    os.makedirs(base_dir, exist_ok=True)

    # Convert meters to pixels
    width_px = int((ROLL_WIDTH_M * 1000 / 25.4) * dpi)
    height_px = int((ROLL_HEIGHT_M * 1000 / 25.4) * dpi)

    # Safety limit (avoid memory crash)
    if width_px * height_px > 2_000_000_000:
        raise Exception("Requested resolution too large.")

    texture = Image.open(texture_path).convert("RGB")
    tex_np = np.array(texture)

    tex_h, tex_w = tex_np.shape[:2]

    zoom_levels = 4  # 100%, 50%, 25%, 12%

    for z in range(zoom_levels):

        scale_factor = 1 / (2 ** z)

        z_width = int(width_px * scale_factor)
        z_height = int(height_px * scale_factor)

        z_dir = f"{base_dir}/z{z}"
        os.makedirs(z_dir, exist_ok=True)

        tiles_x = math.ceil(z_width / TILE_SIZE)
        tiles_y = math.ceil(z_height / TILE_SIZE)

        for ty in range(tiles_y):
            for tx in range(tiles_x):

                x_start = tx * TILE_SIZE
                y_start = ty * TILE_SIZE

                tile = np.zeros((TILE_SIZE, TILE_SIZE, 3), dtype=np.uint8)

                for y in range(TILE_SIZE):
                    for x in range(TILE_SIZE):

                        global_x = int((x_start + x) / scale_factor)
                        global_y = int((y_start + y) / scale_factor)

                        if global_x < width_px and global_y < height_px:

                            tile[y, x] = tex_np[
                                global_y % tex_h,
                                global_x % tex_w
                            ]

                tile_img = Image.fromarray(tile)
                tile_img.save(f"{z_dir}/tile_{tx}_{ty}.jpg", quality=90)

    # Save metadata
    metadata = {
        "roll_id": roll_id,
        "dpi": dpi,
        "width_px": width_px,
        "height_px": height_px,
        "tile_size": TILE_SIZE,
        "zoom_levels": zoom_levels
    }

    with open(f"{base_dir}/metadata.json", "w") as f:
        json.dump(metadata, f)

    return roll_id