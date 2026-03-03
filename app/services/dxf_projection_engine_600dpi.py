import ezdxf
from ezdxf import recover
import numpy as np
from PIL import Image
import cv2
import math


# ---------------------------------------------------
# SAFE DXF LOADER
# ---------------------------------------------------

def load_dxf_safe(path):
    try:
        doc, auditor = recover.readfile(path)
        return doc
    except Exception as e:
        raise Exception(f"Failed to load DXF: {e}")


# ---------------------------------------------------
# EXTRACT POLYGONS
# ---------------------------------------------------

def extract_polygons(doc):
    msp = doc.modelspace()
    polygons = []

    for insert in msp.query("INSERT"):

        block = doc.blocks.get(insert.dxf.name)
        insert_matrix = insert.matrix44()

        for entity in block:

            if entity.dxftype() == "POLYLINE":
                pts = []
                for v in entity.vertices:
                    x = v.dxf.location.x
                    y = v.dxf.location.y
                    tx, ty, _ = insert_matrix.transform((x, y, 0))
                    pts.append((tx, ty))
                if len(pts) > 3:
                    polygons.append(pts)

            elif entity.dxftype() == "LWPOLYLINE":
                pts = []
                for p in entity:
                    tx, ty, _ = insert_matrix.transform((p[0], p[1], 0))
                    pts.append((tx, ty))
                if entity.closed and len(pts) > 3:
                    polygons.append(pts)

            elif entity.dxftype() == "SPLINE":
                try:
                    spline_pts = list(entity.approximate(100))
                    pts = []
                    for x, y, *_ in spline_pts:
                        tx, ty, _ = insert_matrix.transform((x, y, 0))
                        pts.append((tx, ty))
                    if len(pts) > 3:
                        polygons.append(pts)
                except:
                    continue

    return polygons


# ---------------------------------------------------
# 600 DPI PROJECTION ENGINE
# ---------------------------------------------------

def project_texture_on_dxf_600dpi(
    dxf_path,
    texture_path,
    output_path,
    dpi=600,
    max_pixels=500_000_000   # safety limit (~500MP)
):

    doc = load_dxf_safe(dxf_path)
    polygons = extract_polygons(doc)

    if not polygons:
        raise Exception("No valid pattern pieces found in DXF.")

    # Compute bounds
    all_pts = [pt for poly in polygons for pt in poly]
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    scale = dpi / 25.4  # mm → px

    width_px = int((max_x - min_x) * scale)
    height_px = int((max_y - min_y) * scale)

    if width_px <= 0 or height_px <= 0:
        raise Exception("Invalid DXF bounds.")

    total_pixels = width_px * height_px

    if total_pixels > max_pixels:
        raise Exception(
            f"Image too large ({total_pixels} pixels). "
            f"Reduce DPI or increase memory limit."
        )

    print(f"Generating {width_px} x {height_px} at {dpi} DPI")

    # Create empty canvas
    canvas = np.zeros((height_px, width_px, 3), dtype=np.uint8)
    mask = np.zeros((height_px, width_px), dtype=np.uint8)

    # Rasterize mask
    for poly in polygons:

        pixel_poly = [
            (
                int((x - min_x) * scale),
                int(height_px - (y - min_y) * scale)
            )
            for x, y in poly
        ]

        cv2.fillPoly(mask, [np.array(pixel_poly, dtype=np.int32)], 255)

    # Load texture
    texture = Image.open(texture_path).convert("RGB")
    texture_np = np.array(texture)
    tex_h, tex_w = texture_np.shape[:2]

    # STREAM TILE (row-wise, not full memory tile)
    for y in range(height_px):

        if y % 2000 == 0:
            print(f"Processing row {y}/{height_px}")

        tex_y = y % tex_h

        for x in range(width_px):
            if mask[y, x] == 255:
                tex_x = x % tex_w
                canvas[y, x] = texture_np[tex_y, tex_x]

    final = Image.fromarray(canvas)
    final.save(output_path, dpi=(dpi, dpi))

    return output_path