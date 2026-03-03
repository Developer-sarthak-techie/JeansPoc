from PIL import Image
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATTERN_ROOT = os.path.join(BASE_DIR, "app", "templates", "patterns")

def generate_size_cut(seamless_panel_path, size):

    fabric = Image.open(seamless_panel_path).convert("RGBA")

    size_folder = os.path.join(PATTERN_ROOT, size)

    if not os.path.exists(size_folder):
        raise Exception(f"Size patterns not found: {size}")

    cut_pieces = []

    for file in os.listdir(size_folder):

        if not file.endswith(".png"):
            continue

        mask_path = os.path.join(size_folder, file)
        mask = Image.open(mask_path).convert("RGBA")

        # Ensure mask matches fabric size EXACTLY
        if mask.size != fabric.size:
            raise Exception("Mask size must match fabric size")

        alpha_mask = mask.split()[3]

        clipped = Image.composite(
            fabric,
            Image.new("RGBA", fabric.size),
            alpha_mask
        )

        # Crop to bounding box (VERY IMPORTANT)
        bbox = alpha_mask.getbbox()
        if bbox:
            clipped = clipped.crop(bbox)
            cut_pieces.append(clipped)
        print("Fabric size:", fabric.size)
        print("Mask size:", mask.size)
        print("Alpha bbox:", alpha_mask.getbbox())

    # Create compact layout
    padding = 100
    total_height = sum(p.height for p in cut_pieces) + padding * len(cut_pieces)
    max_width = max(p.width for p in cut_pieces)

    output = Image.new("RGBA", (max_width + 200, total_height), (255,255,255,255))

    y_offset = 0
    for piece in cut_pieces:
        output.paste(piece, (100, y_offset), piece)
        y_offset += piece.height + padding

    os.makedirs("outputs", exist_ok=True)

    output_path = f"outputs/final_cut_layout_{size}.png"
    output.save(output_path, format="PNG", compress_level=1)

    return output_path




# from PIL import Image
# import os

# from app.services.graded_pattern_engine import generate_graded_mask

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# PATTERN_ROOT = os.path.join(BASE_DIR, "app", "templates", "patterns")

# def generate_size_cut(seamless_panel_path, size):

#     fabric = Image.open(seamless_panel_path).convert("RGBA")

#     size_folder = os.path.join(PATTERN_ROOT, size)

#     if not os.path.exists(size_folder):
#         raise Exception(f"Size patterns not found: {size}")

#     cut_pieces = []

#     for file in os.listdir(size_folder):

#         if not file.endswith(".png"):
#             continue

#         mask_path = os.path.join(size_folder, file)
#         # mask = Image.open(mask_path).convert("RGBA")

#         # # Ensure mask same size as fabric
#         # mask = mask.resize(fabric.size, Image.LANCZOS)

#         # alpha_mask = mask.split()[3]

#         mask = generate_graded_mask(size, fabric.size)

#         alpha = mask.split()[3]

#         final = Image.composite(
#             fabric,
#             Image.new("RGBA", fabric.size),
#             alpha
# )

#         # clipped = Image.composite(
#         #     fabric,
#         #     Image.new("RGBA", fabric.size),
#         #     alpha_mask
#         # )

#         cut_pieces.append(final)

#     # Arrange cut pieces vertically
#     width = fabric.width
#     height = fabric.height * len(cut_pieces)

#     output = Image.new("RGBA", (width, height), (255, 255, 255, 255))

#     y_offset = 0
#     for piece in cut_pieces:
#         output.paste(piece, (0, y_offset), piece)
#         y_offset += fabric.height

#     os.makedirs("outputs", exist_ok=True)

#     output_path = f"outputs/final_cut_layout_{size}.png"
#     output.save(output_path, dpi=(300, 300))

#     return output_path