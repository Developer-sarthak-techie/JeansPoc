import cv2
import numpy as np
from PIL import Image
from app.models.panel_geometry import PANEL_GEOMETRY


def project_texture_to_panels(texture_path, output_path):

    base = Image.open("outputs/jeans_master_alignment_panel_size32_300dpi.png")
    base_np = np.array(base)

    texture = Image.open(texture_path).convert("RGB")
    texture_np = np.array(texture)

    result = base_np.copy()

    for panel_name, coords in PANEL_GEOMETRY.items():

        # Destination polygon
        dst_pts = np.array(coords, dtype=np.float32)

        # Source rectangle (full texture)
        h, w = texture_np.shape[:2]
        src_pts = np.array([
            [0,0],
            [w,0],
            [w,h],
            [0,h]
        ], dtype=np.float32)

        # Compute perspective transform
        matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

        warped = cv2.warpPerspective(
            texture_np,
            matrix,
            (base_np.shape[1], base_np.shape[0])
        )

        # Create mask
        mask = np.zeros(base_np.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [dst_pts.astype(np.int32)], 255)

        # Blend into result
        result[mask == 255] = warped[mask == 255]

    final = Image.fromarray(result)
    final.save(output_path)

    return output_path