import ezdxf
from ezdxf import recover
import numpy as np
from PIL import Image
import cv2
import math


def load_dxf_safe(path):
    try:
        doc, auditor = recover.readfile(path)
        return doc
    except Exception as e:
        raise Exception(f"Failed to load DXF: {e}")


def extract_polygons_from_dxf(doc):

    msp = doc.modelspace()
    polygons = []

    for insert in msp.query("INSERT"):

        block_name = insert.dxf.name
        block = doc.blocks.get(block_name)
        insert_matrix = insert.matrix44()

        for entity in block:

            # POLYLINE
            if entity.dxftype() == "POLYLINE":
                pts = []
                for v in entity.vertices:
                    x = v.dxf.location.x
                    y = v.dxf.location.y
                    tx, ty, _ = insert_matrix.transform((x, y, 0))
                    pts.append((tx, ty))

                if len(pts) > 3:
                    polygons.append(pts)

            # LWPOLYLINE
            elif entity.dxftype() == "LWPOLYLINE":
                pts = []
                for p in entity:
                    tx, ty, _ = insert_matrix.transform((p[0], p[1], 0))
                    pts.append((tx, ty))

                if entity.closed and len(pts) > 3:
                    polygons.append(pts)

            # SPLINE
            elif entity.dxftype() == "SPLINE":
                try:
                    spline_pts = list(entity.approximate(120))
                    pts = []
                    for x, y, *_ in spline_pts:
                        tx, ty, _ = insert_matrix.transform((x, y, 0))
                        pts.append((tx, ty))

                    if len(pts) > 3:
                        polygons.append(pts)
                except:
                    continue

    return polygons


def project_texture_on_dxf(dxf_path, texture_path, output_path, dpi=300):

    doc = load_dxf_safe(dxf_path)
    polygons = extract_polygons_from_dxf(doc)

    if not polygons:
        raise Exception("No valid pattern pieces found in DXF.")

    # --- Compute Bounding Box ---
    all_pts = [pt for poly in polygons for pt in poly]
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    scale = dpi / 25.4  # mm → px

    # Add 5mm safety margin
    margin_mm = 5
    margin_px = int(margin_mm * scale)

    width_px = math.ceil((max_x - min_x) * scale) + 2 * margin_px
    height_px = math.ceil((max_y - min_y) * scale) + 2 * margin_px

    if width_px <= 0 or height_px <= 0:
        raise Exception("Invalid DXF bounds.")

    total_pixels = width_px * height_px

    # Safety cap (~800 million pixels)
    if total_pixels > 800_000_000:
        raise Exception(
            f"Image too large ({total_pixels} pixels). "
            f"Reduce DPI or split into tiles."
        )

    # --- Create Canvas ---
    canvas_np = np.zeros((height_px, width_px, 3), dtype=np.uint8)
    mask = np.zeros((height_px, width_px), dtype=np.uint8)

    # --- Load Texture ---
    texture = Image.open(texture_path).convert("RGB")
    texture_np = np.array(texture)

    tex_h, tex_w = texture_np.shape[:2]

    # --- Tile Texture ---
    tiled_texture = np.tile(
        texture_np,
        (
            height_px // tex_h + 1,
            width_px // tex_w + 1,
            1
        )
    )

    tiled_texture = tiled_texture[:height_px, :width_px]

    # --- Rasterize Polygons ---
    for poly in polygons:

        pixel_poly = []

        for x, y in poly:
            px = (x - min_x) * scale + margin_px
            py = height_px - ((y - min_y) * scale + margin_px)

            # Clamp to canvas
            px = max(0, min(width_px - 1, px))
            py = max(0, min(height_px - 1, py))

            pixel_poly.append((int(round(px)), int(round(py))))

        cv2.fillPoly(mask, [np.array(pixel_poly, dtype=np.int32)], 255)

    # --- Apply Texture ---
    canvas_np[mask == 255] = tiled_texture[mask == 255]

    # --- Save ---
    final = Image.fromarray(canvas_np)
    final.save(output_path, dpi=(dpi, dpi))

    return output_path






























# import ezdxf
# from ezdxf import recover
# import numpy as np
# from PIL import Image
# import cv2


# def load_dxf_safe(path):
#     try:
#         doc, auditor = recover.readfile(path)
#         return doc
#     except Exception as e:
#         raise Exception(f"Failed to load DXF: {e}")


# def extract_polygons_from_dxf(doc):
#     """
#     Extracts closed pattern polygons from:
#     - INSERT blocks
#     - POLYLINE
#     - LWPOLYLINE
#     - SPLINE
#     """
#     msp = doc.modelspace()
#     polygons = []

#     for insert in msp.query("INSERT"):

#         block_name = insert.dxf.name
#         block = doc.blocks.get(block_name)
#         insert_matrix = insert.matrix44()

#         for entity in block:

#             # --- POLYLINE ---
#             if entity.dxftype() == "POLYLINE":
#                 pts = []
#                 for v in entity.vertices:
#                     x = v.dxf.location.x
#                     y = v.dxf.location.y
#                     tx, ty, _ = insert_matrix.transform((x, y, 0))
#                     pts.append((tx, ty))

#                 if len(pts) > 3:
#                     polygons.append(pts)

#             # --- LWPOLYLINE ---
#             elif entity.dxftype() == "LWPOLYLINE":
#                 pts = []
#                 for p in entity:
#                     tx, ty, _ = insert_matrix.transform((p[0], p[1], 0))
#                     pts.append((tx, ty))

#                 if entity.closed and len(pts) > 3:
#                     polygons.append(pts)

#             # --- SPLINE ---
#             elif entity.dxftype() == "SPLINE":
#                 try:
#                     spline_pts = list(entity.approximate(80))
#                     pts = []
#                     for x, y, *_ in spline_pts:
#                         tx, ty, _ = insert_matrix.transform((x, y, 0))
#                         pts.append((tx, ty))

#                     if len(pts) > 3:
#                         polygons.append(pts)
#                 except:
#                     continue

#     return polygons


# def project_texture_on_dxf(dxf_path, texture_path, output_path, dpi=300):

#     # --- Load DXF ---
#     doc = load_dxf_safe(dxf_path)

#     # --- Extract Pattern Pieces ---
#     polygons = extract_polygons_from_dxf(doc)

#     if not polygons:
#         raise Exception("No valid pattern pieces found in DXF.")

#     # --- Compute Bounding Box ---
#     all_pts = [pt for poly in polygons for pt in poly]
#     xs = [p[0] for p in all_pts]
#     ys = [p[1] for p in all_pts]

#     min_x, max_x = min(xs), max(xs)
#     min_y, max_y = min(ys), max(ys)

#     scale = dpi / 25.4  # mm → pixel

#     width_px = int((max_x - min_x) * scale)
#     height_px = int((max_y - min_y) * scale)

#     if width_px <= 0 or height_px <= 0:
#         raise Exception("Invalid DXF bounds.")

#     # --- Create Master Canvas ---
#     canvas_np = np.zeros((height_px, width_px, 3), dtype=np.uint8)
#     mask = np.zeros((height_px, width_px), dtype=np.uint8)

#     # --- Load Texture ---
#     texture = Image.open(texture_path).convert("RGB")
#     texture_np = np.array(texture)

#     tex_h, tex_w = texture_np.shape[:2]

#     # --- Tile Texture Once to Full Canvas ---
#     tiled_texture = np.tile(
#         texture_np,
#         (
#             height_px // tex_h + 1,
#             width_px // tex_w + 1,
#             1
#         )
#     )

#     tiled_texture = tiled_texture[:height_px, :width_px]

#     # --- Rasterize All Polygons Into One Mask ---
#     for poly in polygons:

#         pixel_poly = [
#             (
#                 int((x - min_x) * scale),
#                 int(height_px - (y - min_y) * scale)
#             )
#             for x, y in poly
#         ]

#         cv2.fillPoly(mask, [np.array(pixel_poly, dtype=np.int32)], 255)

#     # --- Apply Texture ---
#     canvas_np[mask == 255] = tiled_texture[mask == 255]

#     # --- Save ---
#     final = Image.fromarray(canvas_np)
#     final.save(output_path, dpi=(dpi, dpi))

#     return output_path




























# import ezdxf
# import numpy as np
# from PIL import Image, ImageDraw
# import cv2
# from shapely.geometry import Polygon


# def project_texture_on_dxf(dxf_path, texture_path, output_path, dpi=300):

#     # Load DXF
#     # doc = ezdxf.readfile(dxf_path)


#     doc = load_dxf_safe(dxf_path)
#     doc = doc
#     msp = doc.modelspace()

#     # Load texture
#     texture = Image.open(texture_path).convert("RGB")
#     texture_np = np.array(texture)

#     # Collect polygons
#     # polygons = []

#     # for entity in msp:
#     #     if entity.dxftype() == "LWPOLYLINE":
#     #         points = [(p[0], p[1]) for p in entity]
#     #         if len(points) > 3:
#     #             polygons.append(points)
#     for entity in msp:
#         print(entity.dxftype())
#     polygons = []

#     print("---- BLOCK CONTENT INSPECTION ----")

#     for insert in msp.query("INSERT"):
#         block_name = insert.dxf.name
#         print("INSERT Block Name:", block_name)

#         block = doc.blocks.get(block_name)

#         for entity in block:
#             print("   ->", entity.dxftype())

#     polygons = []

#     for insert in msp.query("INSERT"):

#         block_name = insert.dxf.name
#         block = doc.blocks.get(block_name)

#         insert_matrix = insert.matrix44()

#         for entity in block:

#             # ✅ Handle POLYLINE (your case)
#             if entity.dxftype() == "POLYLINE":

#                 pts = []

#                 for v in entity.vertices:
#                     x = v.dxf.location.x
#                     y = v.dxf.location.y

#                     # Apply INSERT transformation
#                     tx, ty, _ = insert_matrix.transform((x, y, 0))
#                     pts.append((tx, ty))

#                 if len(pts) > 3:
#                     polygons.append(pts)

#             # Optional: handle LWPOLYLINE just in case
#             elif entity.dxftype() == "LWPOLYLINE":

#                 pts = []
#                 for p in entity:
#                     tx, ty, _ = insert_matrix.transform((p[0], p[1], 0))
#                     pts.append((tx, ty))

#                 if entity.closed and len(pts) > 3:
#                     polygons.append(pts)













#     # for insert in msp.query("INSERT"):

#     #     block_name = insert.dxf.name
#     #     block = doc.blocks.get(block_name)

#     #     # Transformation matrix of INSERT
#     #     insert_matrix = insert.matrix44()

#     #     for entity in block:

#     #         # Handle LWPOLYLINE
#     #         if entity.dxftype() == "LWPOLYLINE":

#     #             pts = []
#     #             for p in entity:
#     #                 x, y = p[0], p[1]
#     #                 transformed = insert_matrix.transform((x, y, 0))
#     #                 pts.append((transformed[0], transformed[1]))

#     #             if entity.closed and len(pts) > 3:
#     #                 polygons.append(pts)

#     #         # Handle SPLINE (very common in garment CAD)
#     #         elif entity.dxftype() == "SPLINE":

#     #             spline_pts = list(entity.approximate(100))
#     #             pts = []

#     #             for x, y, *_ in spline_pts:
#     #                 transformed = insert_matrix.transform((x, y, 0))
#     #                 pts.append((transformed[0], transformed[1]))

#     #             if len(pts) > 3:
#     #                 polygons.append(pts)















#     # polygons = []

#     # for entity in msp:

#     #     # Case 1: LWPOLYLINE
#     #     if entity.dxftype() == "LWPOLYLINE":
#     #         points = [(p[0], p[1]) for p in entity]
#     #         if entity.closed and len(points) > 3:
#     #             polygons.append(points)

#     #     # Case 2: POLYLINE (older type)
#     #     elif entity.dxftype() == "POLYLINE":
#     #         points = [(v.dxf.location.x, v.dxf.location.y)
#     #                 for v in entity.vertices]
#     #         if len(points) > 3:
#     #             polygons.append(points)

#     #     # Case 3: SPLINE (very common in garment CAD)
#     #     elif entity.dxftype() == "SPLINE":
#     #         spline_points = list(entity.approximate(50))
#     #         if len(spline_points) > 3:
#     #             polygons.append([(p[0], p[1]) for p in spline_points])

#     # # 2️⃣ Extract geometry from BLOCKS (very important)
#     # for insert in msp.query("INSERT"):

#     #     block_name = insert.dxf.name
#     #     block = doc.blocks.get(block_name)

#     #     for entity in block:

#     #         if entity.dxftype() == "LWPOLYLINE":
#     #             pts = [(p[0], p[1]) for p in entity]
#     #             if entity.closed:
#     #                 polygons.append(pts)

#     #         elif entity.dxftype() == "SPLINE":
#     #             pts = list(entity.approximate(80))
#     #             if len(pts) > 3:
#     #                 polygons.append([(p[0], p[1]) for p in pts])
#     if not polygons:
#         raise Exception("No valid pattern pieces found in DXF.")

#     # Determine canvas bounds
#     all_points = [pt for poly in polygons for pt in poly]
#     xs = [p[0] for p in all_points]
#     ys = [p[1] for p in all_points]

#     min_x, max_x = min(xs), max(xs)
#     min_y, max_y = min(ys), max(ys)

#     scale = dpi / 25.4  # mm to pixel scaling

#     width_px = int((max_x - min_x) * scale)
#     height_px = int((max_y - min_y) * scale)

#     canvas = Image.new("RGB", (width_px, height_px), "white")
#     canvas_np = np.array(canvas)

#     # Process each pattern piece
#     for poly in polygons:

#         # Convert DXF coords to pixel coords
#         pixel_poly = [
#             (
#                 int((x - min_x) * scale),
#                 int(height_px - (y - min_y) * scale)
#             )
#             for x, y in poly
#         ]

#         mask = np.zeros((height_px, width_px), dtype=np.uint8)
#         cv2.fillPoly(mask, [np.array(pixel_poly, dtype=np.int32)], 255)

#         # Tile texture over entire canvas
#         tiled_texture = np.tile(
#             texture_np,
#             (
#                 int(height_px / texture_np.shape[0]) + 1,
#                 int(width_px / texture_np.shape[1]) + 1,
#                 1
#             )
#         )

#         # Apply mask
#         canvas_np[mask == 255] = tiled_texture[mask == 255]

#     final = Image.fromarray(canvas_np)
#     final.save(output_path, dpi=(dpi, dpi))

#     return output_path



# import ezdxf
# from ezdxf import recover

# def load_dxf_safe(path):

#     try:
#         doc, auditor = recover.readfile(path)

#         if auditor.has_errors:
#             print("DXF had structural issues but was recovered.")

#         return doc

#     except Exception as e:
#         raise Exception(f"Failed to load DXF: {e}")