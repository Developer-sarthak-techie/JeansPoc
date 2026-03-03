from PIL import Image
from app.services.fabric_engine import apply_fabric_effect

def generate_preview(print_sheet_path, fabric_type):

    sheet = Image.open(print_sheet_path).convert("RGB")

    realistic = apply_fabric_effect(sheet, fabric_type)

    preview_path = print_sheet_path.replace("print_sheet", "preview")

    realistic.save(preview_path, dpi=(300,300))

    return preview_path