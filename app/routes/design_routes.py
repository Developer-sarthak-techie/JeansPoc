import os
import uuid
import cv2
import ezdxf
import numpy as np
import shutil
from fastapi import APIRouter, UploadFile, File, Form
from app.services.dimension_pattern_engine import generate_scaled_pattern
from app.services.dxf_projection_engine import project_texture_on_dxf
from app.services.fabric_roll_engine import generate_fabric_roll
from app.services.fabric_roll_tile_engine import generate_fabric_roll_tiles
from app.services.grading_engine import GradingEngine
from app.services.grading_engine import GradingEngine
from app.services.garment_engine import process_garment
from app.services.texture_renderer import render_texture
from app.utils.file_util import save_upload_file

from app.services.seamless_print_engine import generate_seamless_print
from app.services.scale_sample_engine import generate_scaled_from_sample

from app.services.dxf_projection_engine_600dpi import project_texture_on_dxf_600dpi
from app.services.feature_grading_engine import FeatureGradingEngine



BASE_DXF_30 = "app/templates/jeans/JEAN (S-30 cm) STD DXF.dxf"       
BASE_DXF_32 = "app/templates/jeans/JEAN (S-32 cm) STD DXF.dxf"
BASE_DXF_34 = "app/templates/jeans/JEAN (S-34 cm) STD DXF.dxf"

router = APIRouter(prefix="/design", tags=["Design"])

@router.post("/generate")
async def generate_design(
    size: str = Form(...),
    fabric_type: str = Form(...),
    image: UploadFile = File(...)
):

    file_path = save_upload_file(image)

    result = process_garment(size, file_path, fabric_type)
    return {
        "message": "Generated successfully",
        "print_sheet_url": f"http://localhost:8000/{result['print_sheet']}",
        "preview_url": f"http://localhost:8000/{result['preview']}"
    }


@router.post("/generate-seamless")
async def generate_seamless(
    image: UploadFile = File(...)
):

    file_path = save_upload_file(image)

    panel_path = "app/templates/jeans_panel_high_resolution_4x.png"  # your panel path

    output_path = generate_seamless_print(panel_path, file_path)

    return {
        "message": "Seamless print generated",
        "output_url": f"http://localhost:8000/{output_path}"
    }


from app.services.cut_engine import generate_size_cut

@router.post("/cut-size")
async def cut_by_size(
    size: str = Form(...)
):

    seamless_path = "outputs/seamless_print_ready.png"

    output_path = generate_size_cut(seamless_path, size)

    return {
        "message": "Cut layout generated",
        "output_url": f"http://localhost:8000/{output_path}"
    }



from app.services.overlay_cut_engine import generate_cut_overlay

@router.post("/add-cut-lines")
async def add_cut_lines(size: str = Form(...)):

    seamless_path = "outputs/seamless_print_ready.png"

    output_path = generate_cut_overlay(seamless_path, size)

    return {
        "message": "Cut lines added",
        "output_url": f"http://localhost:8000/{output_path}"
    }



@router.post("/generate-by-dimension")
async def generate_by_dimension(
    width_cm: float = Form(...),
    height_cm: float = Form(...),
    dpi: int = Form(300)
):

    output = generate_scaled_pattern(width_cm, height_cm, dpi)

    return {
        "message": "Pattern generated",
        "output_url": f"http://localhost:8000/{output}"
    }



@router.post("/scale-sample")
async def scale_sample(
    width_cm: float = Form(...),
    height_cm: float = Form(...),
    dpi: int = Form(300),
    image: UploadFile = File(...)
):

    file_path = save_upload_file(image)

    output_path = generate_scaled_from_sample(
        file_path,
        width_cm,
        height_cm,
        dpi
    )

    return {
        "message": "Scaled successfully",
        "output_url": f"http://localhost:8000/{output_path}"
    }


from app.services.garment_projection_engine import project_texture_to_panels

@router.post("/project-texture")
async def project_texture(image: UploadFile = File(...)):

    file_path = save_upload_file(image)

    output_path = "outputs/projected_result.png"

    project_texture_to_panels(file_path, output_path)

    return {
        "message": "Texture projected successfully",
        "output_url": f"http://localhost:8000/{output_path}"
    }


@router.post("/generate-fabric-roll")
async def generate_roll(
    size_width_m: float,
    size_height_m: float,
    dpi: int,
    image: UploadFile = File(...)
):
    file_path = save_upload_file(image)

    output_path = "outputs/fabric_roll_2m_1m.png"

    generate_fabric_roll(
        sample_path=file_path,
        output_path=output_path,
        width_m=size_width_m,
        height_m=size_height_m,
        dpi=dpi
    )

    return {
        "message": "Fabric roll generated successfully",
        "output": output_path
    }






@router.post("/dxf-imprint")
async def dxf_imprint(
    dxf_file: UploadFile = File(...),
    texture: UploadFile = File(...)
):

    dxf_path = save_upload_file(dxf_file)
    texture_path = save_upload_file(texture)

    output_path = "outputs/dxf_texture_projection.png"

    project_texture_on_dxf(
        dxf_path=dxf_path,
        texture_path=texture_path,
        output_path=output_path,
        dpi=300
    )

    return {"output": output_path}





@router.post("/dxf-imprint-600dpi")
async def dxf_imprint(
    dxf_file: UploadFile = File(...),
    texture: UploadFile = File(...)
):

    dxf_path = save_upload_file(dxf_file)
    texture_path = save_upload_file(texture)

    output_path = "outputs/dxf_texture_projection.png"

    project_texture_on_dxf_600dpi(
        dxf_path=dxf_path,
        texture_path=texture_path,
        output_path="outputs/print_ready_600dpi.png",
        dpi=400
    )

    return {"output": output_path}



@router.post("/fabric-roll-in-tiles")
async def create_fabric_roll(file: UploadFile = File(...), dpi: int = 300):

    temp_path = f"outputs/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    roll_id = generate_fabric_roll_tiles(temp_path, dpi)

    return {
        "roll_id": roll_id,
        "viewer_url": f"/fabric_rolls/{roll_id}/metadata.json"
    }



@router.post("/engine/grade-imprint")
async def grade_imprint(
    size: int = Form(...),
    texture: UploadFile = File(...)
):
    if size not in [30, 32, 34]:
        return {"error": "Supported sizes: 30, 32, 34"}

    os.makedirs("outputs", exist_ok=True)

    texture_path = f"outputs/{texture.filename}"
    with open(texture_path, "wb") as buffer:
        shutil.copyfileobj(texture.file, buffer)

    engine = GradingEngine(
        BASE_DXF_30,
        BASE_DXF_32,
        BASE_DXF_34
    )

    graded_polygons = engine.grade(size)

    output_path = f"outputs/graded_size_{size}.png"

    render_texture(
        graded_polygons,
        texture_path,
        output_path,
        dpi=300
    )

    return {
        "status": "success",
        "size": size,
        "output": output_path
    }



@router.post("/design/engine/project-graded")
async def project_graded(
    texture: UploadFile = File(...),
    size: int = Form(...)
):

    input_path = save_upload(texture)

    input_dpi = 300
    output_dpi = 400

    image = cv2.imread(input_path)

    # Extract geometry
    base_polygons = extract_polygons(BASE_DXF_30)

    if size == 32:
        target_polygons = extract_polygons(BASE_DXF_32)
    elif size == 34:
        target_polygons = extract_polygons(BASE_DXF_34)
    else:
        return {"error": "Unsupported size"}

    # Convert cm → pixels
    base_px = cm_to_pixels(base_polygons, input_dpi)
    target_px = cm_to_pixels(target_polygons, output_dpi)

    # Determine output canvas size
    all_pts = [pt for poly in target_px.values() for pt in poly]

    max_x = int(max(p[0] for p in all_pts))
    max_y = int(max(p[1] for p in all_pts))

    canvas = np.zeros((max_y + 200, max_x + 200, 3), dtype=np.uint8)

    # Project each component
    # for name in base_px:

    #     if name not in target_px:
    #         continue

    #     src_poly = base_px[name]
    #     dst_poly = target_px[name]

    #     cropped, shifted = crop_polygon(image, src_poly)

    #     H, _ = cv2.findHomography(
    #         np.array(shifted, dtype=np.float32),
    #         np.array(dst_poly, dtype=np.float32)
    #     )

    #     warped = cv2.warpPerspective(
    #         cropped,
    #         H,
    #         (canvas.shape[1], canvas.shape[0]),
    #         flags=cv2.INTER_LANCZOS4
    #     )

    #     canvas = overlay(canvas, warped)


    matched_components = set(base_px.keys()).intersection(set(target_px.keys()))

    if not matched_components:
        raise Exception("No matching components between DXF files.")

    skipped_base = set(base_px.keys()) - matched_components
    skipped_target = set(target_px.keys()) - matched_components

    print("Matched components:", matched_components)
    print("Skipped (base only):", skipped_base)
    print("Skipped (target only):", skipped_target)

    for name in matched_components:

        try:
            src_poly = base_px[name]
            dst_poly = target_px[name]

            cropped, shifted = crop_polygon(image, src_poly)

            H, _ = cv2.findHomography(
                np.array(shifted, dtype=np.float32),
                np.array(dst_poly, dtype=np.float32)
            )

            warped = cv2.warpPerspective(
                cropped,
                H,
                (canvas.shape[1], canvas.shape[0]),
                flags=cv2.INTER_LANCZOS4
            )

            canvas = overlay(canvas, warped)

        except Exception as e:
            print(f"⚠ Skipping component {name}: {str(e)}")
            continue
    # # ===== OUTPUT PATHS =====
    # os.makedirs("outputs", exist_ok=True)

    # file_id = uuid.uuid4().hex

    # tiff_path = f"outputs/graded_{size}_{file_id}.tiff"
    # png_path  = f"outputs/graded_{size}_{file_id}.png"

    # # ===== SAVE HIGH QUALITY TIFF (400 DPI) =====
    # cv2.imwrite(
    #     tiff_path,
    #     canvas,
    #     [
    #         cv2.IMWRITE_TIFF_COMPRESSION, 1  # No compression
    #     ]
    # )

    # # ===== SAVE PNG PREVIEW =====
    # cv2.imwrite(
    #     png_path,
    #     canvas,
    #     [
    #         cv2.IMWRITE_PNG_COMPRESSION, 3  # Light compression (fast)
    #     ]
    # )

    # return {
    #     "status": "success",
    #     "size": size,
    #     "dpi": 400,
    #     "tiff": tiff_path,
    #     "preview": png_path
    # }

    output_path = f"outputs/graded_{size}_400dpi.tiff"

    cv2.imwrite(
        output_path,
        canvas,
        [cv2.IMWRITE_TIFF_COMPRESSION, 1]
    )

    return {
        "status": "success",
        "size": size,
        "dpi": 400,
        "output": output_path
    }


def dxf_to_pixels(polygons, dpi):
    pixels_per_cm = dpi / 2.54

    scaled = {}
    for name, pts in polygons.items():
        scaled[name] = [(x * pixels_per_cm, y * pixels_per_cm)
                        for x, y in pts]
    return scaled

def cm_to_pixels(polygons, dpi, image_height_px=None):
    px_per_cm = dpi / 2.54

    scaled = {}

    for name, pts in polygons.items():
        new_pts = []
        for x_cm, y_cm in pts:
            x_px = x_cm * px_per_cm
            y_px = y_cm * px_per_cm

            # 🔥 Flip Y axis if image height provided
            if image_height_px is not None:
                y_px = image_height_px - y_px

            new_pts.append((x_px, y_px))

        scaled[name] = new_pts

    return scaled

def extract_polygons(dxf_path):
    doc, auditor = ezdxf.recover.readfile(dxf_path)
    msp = doc.modelspace()

    components = {}

    for entity in msp:
        if entity.dxftype() in ["LWPOLYLINE", "POLYLINE"]:
            layer = entity.dxf.layer or "DEFAULT"

            if entity.dxftype() == "LWPOLYLINE":
                pts = [(p[0], p[1]) for p in entity.get_points()]
            else:
                pts = [(v.dxf.location.x, v.dxf.location.y)
                       for v in entity.vertices]

            if len(pts) > 2:
                components[layer] = pts

        elif entity.dxftype() == "INSERT":
            block = doc.blocks.get(entity.dxf.name)

            for e in block:
                if e.dxftype() in ["LWPOLYLINE", "POLYLINE"]:
                    layer = e.dxf.layer or "DEFAULT"

                    if e.dxftype() == "LWPOLYLINE":
                        pts = [(p[0], p[1]) for p in e.get_points()]
                    else:
                        pts = [(v.dxf.location.x, v.dxf.location.y)
                               for v in e.vertices]

                    if len(pts) > 2:
                        components[layer] = pts

    if not components:
        raise Exception("No polygons extracted from DXF.")

    return components
def crop_polygon(image, polygon):

    h_img, w_img = image.shape[:2]

    pts = np.array(polygon, dtype=np.float32)

    x_min = int(np.floor(np.min(pts[:, 0])))
    y_min = int(np.floor(np.min(pts[:, 1])))
    x_max = int(np.ceil(np.max(pts[:, 0])))
    y_max = int(np.ceil(np.max(pts[:, 1])))

    # 🔥 Clamp to image boundaries
    x_min = max(0, x_min)
    y_min = max(0, y_min)
    x_max = min(w_img, x_max)
    y_max = min(h_img, y_max)

    if x_max <= x_min or y_max <= y_min:
        raise Exception("Polygon outside image bounds")

    cropped = image[y_min:y_max, x_min:x_max]

    if cropped.size == 0:
        raise Exception("Cropped image is empty")

    shifted = [(x - x_min, y - y_min) for x, y in polygon]

    mask = np.zeros((cropped.shape[0], cropped.shape[1]), dtype=np.uint8)

    cv2.fillPoly(
        mask,
        [np.array(shifted, dtype=np.int32)],
        255
    )

    if mask.shape[:2] != cropped.shape[:2]:
        raise Exception("Mask size mismatch")

    cropped_masked = cv2.bitwise_and(cropped, cropped, mask=mask)

    return cropped_masked, shifted


def overlay(canvas, warped):
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

    inv = cv2.bitwise_not(mask)

    bg = cv2.bitwise_and(canvas, canvas, mask=inv)
    fg = cv2.bitwise_and(warped, warped, mask=mask)

    return cv2.add(bg, fg)





def save_upload(upload_file):
    # Ensure directory exists
    os.makedirs("outputs", exist_ok=True)

    # Generate unique filename
    extension = os.path.splitext(upload_file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{extension}"

    file_path = os.path.join("outputs", unique_name)

    # Save file in chunks (safe for large TIFF)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return file_path


@router.post("/engine/featureGrading")
async def feature_grading(
    texture: UploadFile = File(...),
    size: int = Form(...),
    dpi: int = Form(300)
):
    if size not in [32, 34]:
        return {"error": "Supported sizes: 32, 34"}

    os.makedirs("outputs", exist_ok=True)
    input_path = save_upload(texture)

    try:
        engine = FeatureGradingEngine(
            BASE_DXF_30,
            BASE_DXF_32,
            BASE_DXF_34
        )

        tiff_path, png_path = engine.process(input_path, size, dpi=dpi)

        return {
            "status": "success",
            "size": size,
            "tiff": tiff_path,
            "preview": png_path
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@router.post("/engine/featureGrading/verify")
async def feature_grading_verify(
    input_texture: UploadFile = File(...),
    output_tiff: UploadFile = File(...),
    size: int = Form(...),
    dpi: int = Form(300)
):
    """
    Verifies that a graded TIFF matches the expected size.
    Upload both the original (size 30) TIFF and the graded output TIFF.
    Returns a detailed per-piece accuracy report + annotated visual.
    """
    if size not in [32, 34]:
        return {"error": "Supported sizes: 32, 34"}

    os.makedirs("outputs", exist_ok=True)
    input_path = save_upload(input_texture)

    out_path = f"outputs/verify_upload_{uuid.uuid4().hex[:6]}.tiff"
    with open(out_path, "wb") as f:
        shutil.copyfileobj(output_tiff.file, f)

    try:
        engine = FeatureGradingEngine(
            BASE_DXF_30,
            BASE_DXF_32,
            BASE_DXF_34
        )

        report, report_path = engine.verify(input_path, out_path, size)

        return {
            "status": "success",
            "summary": report["summary"],
            "pieces": report["pieces"],
            "visual_report": report["visual_report"],
            "json_report": report_path,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
















# @router.post("/design/engine/project-graded/2.0")
# async def project_graded(
#     texture: UploadFile = File(...),
#     size: int = Form(...)
# ):
#     temp_path = save_upload(texture)

#     base_polygons = normalize(extract_polygons(BASE_DXF_30))

#     if size == 32:
#         target_polygons = normalize(extract_polygons(BASE_DXF_32))
#     elif size == 34:
#         target_polygons = normalize(extract_polygons(BASE_DXF_34))
#     else:
#         return {"error": "Unsupported size"}

#     image = cv2.imread(temp_path)

#     canvas = np.zeros_like(image)

#     for name, src_poly in base_polygons.items():

#         if name not in target_polygons:
#             continue

#         dst_poly = target_polygons[name]

#         mask = create_mask(image, src_poly)
#         cropped = cv2.bitwise_and(image, image, mask=mask)

#         H = compute_homography(src_poly, dst_poly)

#         warped = cv2.warpPerspective(
#             cropped,
#             H,
#             (canvas.shape[1], canvas.shape[0]),
#             flags=cv2.INTER_LANCZOS4
#         )

#         canvas = cv2.add(canvas, warped)

#     output_path = f"outputs/graded_{size}.tiff"
#     cv2.imwrite(output_path, canvas)

#     return {
#         "status": "success",
#         "output": output_path
#     }



























































# @router.post("/design/engine/project-graded")
# async def project_graded(
#     texture: UploadFile = File(...),
#     size: int = Form(...)
# ):

#     # Save TIFF
#     temp_path = f"outputs/{texture.filename}"
#     with open(temp_path, "wb") as buffer:
#         shutil.copyfileobj(texture.file, buffer)

#     if size == 32:
#         target_dxf = BASE_DXF_32
#     elif size == 34:
#         target_dxf = BASE_DXF_34
#     else:
#         return {"error": "Unsupported size"}

#     base_polygons = extract_polygons(BASE_DXF_30)
#     target_polygons = extract_polygons(target_dxf)

#     image = cv2.imread(temp_path)

#     canvas = np.zeros_like(image)

#     for name in base_polygons:
#         src_poly = base_polygons[name]
#         dst_poly = target_polygons[name]

#         crop = crop_polygon(image, src_poly)
#         H = compute_transform(src_poly, dst_poly)

#         warped = cv2.warpPerspective(
#             crop,
#             H,
#             (canvas.shape[1], canvas.shape[0]),
#             flags=cv2.INTER_LANCZOS4
#         )

#         canvas = cv2.add(canvas, warped)

#     output_path = f"outputs/graded_{size}.tiff"
#     cv2.imwrite(output_path, canvas)

#     return {
#         "status": "success",
#         "output": output_path
#     }

# def extract_polygons(dxf_path):
#     try:
#         doc, auditor = ezdxf.recover.readfile(dxf_path)
#     except Exception as e:
#         raise Exception(f"DXF load failed: {e}")

#     if auditor.has_errors:
#         print("⚠ DXF had recoverable errors.")

#     msp = doc.modelspace()

#     components = {}

#     for entity in msp:
#         if entity.dxftype() in ["LWPOLYLINE", "POLYLINE"]:
#             layer = entity.dxf.layer or "DEFAULT"

#             try:
#                 if entity.dxftype() == "LWPOLYLINE":
#                     points = [(p[0], p[1]) for p in entity.get_points()]
#                 else:
#                     points = [(v.dxf.location.x, v.dxf.location.y)
#                               for v in entity.vertices]

#                 components[layer] = points

#             except Exception:
#                 continue  # skip broken entity

#     return components

# def crop_polygon(image, polygon):
#     pts = np.array(polygon, dtype=np.int32)

#     x, y, w, h = cv2.boundingRect(pts)

#     cropped = image[y:y+h, x:x+w]

#     shifted_polygon = [(px-x, py-y) for px, py in polygon]

#     mask = np.zeros((h, w), dtype=np.uint8)
#     cv2.fillPoly(mask, [np.array(shifted_polygon, dtype=np.int32)], 255)

#     cropped_masked = cv2.bitwise_and(cropped, cropped, mask=mask)

#     return cropped_masked, shifted_polygon, (x, y, w, h)

# def compute_transform(src_pts, dst_pts):
#     src = np.array(src_pts[:4], dtype=np.float32)
#     dst = np.array(dst_pts[:4], dtype=np.float32)

#     H, _ = cv2.findHomography(src, dst)
#     return H

# def normalize(polygons):
#     min_x = min(pt[0] for poly in polygons.values() for pt in poly)
#     min_y = min(pt[1] for poly in polygons.values() for pt in poly)

#     normalized = {}
#     for name, pts in polygons.items():
#         normalized[name] = [(x-min_x, y-min_y) for x,y in pts]

#     return normalized

# def compute_homography(src_poly, dst_poly):
#     src = np.array(src_poly, dtype=np.float32)
#     dst = np.array(dst_poly, dtype=np.float32)

#     H, _ = cv2.findHomography(src, dst, method=0)
#     return H


# def save_upload(upload_file, folder="temp"):
#     os.makedirs(folder, exist_ok=True)

#     ext = os.path.splitext(upload_file.filename)[1]
#     filename = f"{uuid.uuid4()}{ext}"
#     path = os.path.join(folder, filename)

#     with open(path, "wb") as buffer:
#         buffer.write(upload_file.file.read())

#     return path

# def create_mask(image, polygon):
#     mask = np.zeros(image.shape[:2], dtype=np.uint8)

#     pts = np.array(polygon, dtype=np.int32)

#     cv2.fillPoly(mask, [pts], 255)

#     return mask



# def debug_dxf_entities(dxf_path):
#     import ezdxf
#     doc, auditor = ezdxf.recover.readfile(dxf_path)
#     msp = doc.modelspace()

#     types = set()
#     for e in msp:
#         types.add(e.dxftype())

#     print("DXF entity types found:", types)


# # from fastapi import APIRouter, UploadFile, File, Form
# # from app.services.image_processor import process_design
# # from app.utils.file_util import save_upload_file

# # router = APIRouter(prefix="/design", tags=["Design"])

# # @router.post("/generate")
# # async def generate_design(
# #     size: str = Form(...),
# #     image: UploadFile = File(...)
# # ):

# #     file_path = save_upload_file(image)

# #     output_path = process_design(size, file_path)

# #     # return {
# #     #     "message": "Design generated successfully",
# #     #     "output_file": output_path
# #     # }

# #     return {
# #     "message": "Design generated successfully",
# #     "preview_url": f"http://localhost:8000/{output_path}"
# # }