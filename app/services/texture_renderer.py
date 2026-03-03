import numpy as np
import cv2
from PIL import Image


def render_texture(polygons, texture_path, output_path, dpi=300):

    all_pts = [pt for poly in polygons for pt in poly]
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    scale = dpi / 25.4

    width_px = int((max_x - min_x) * scale)
    height_px = int((max_y - min_y) * scale)

    # canvas = np.zeros((height_px, width_px, 3), dtype=np.uint8)
    canvas = np.ones((height_px, width_px, 3), dtype=np.uint8) * 255
    mask = np.zeros((height_px, width_px), dtype=np.uint8)

    texture = Image.open(texture_path).convert("RGB")
    texture_np = np.array(texture)

    tex_h, tex_w = texture_np.shape[:2]

    tiled_texture = np.tile(
        texture_np,
        (height_px // tex_h + 1, width_px // tex_w + 1, 1)
    )

    tiled_texture = tiled_texture[:height_px, :width_px]

    for poly in polygons:

        pixel_poly = [
            (
                int((x - min_x) * scale),
                int(height_px - (y - min_y) * scale)
            )
            for x, y in poly
        ]

        cv2.fillPoly(mask, [np.array(pixel_poly, dtype=np.int32)], 255)

    canvas[mask == 255] = tiled_texture[mask == 255]

    final = Image.fromarray(canvas)
    # final.save(output_path, dpi=(dpi, dpi))
    final.save(
    output_path,
    format="TIFF",
    dpi=(dpi, dpi),
    compression="tiff_lzw"  # lossless
)

    return output_path