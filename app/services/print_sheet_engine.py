from PIL import Image, ImageEnhance, ImageFilter, ImageChops,ImageDraw
import os

# Absolute base path (safe for production)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_ROOT = os.path.join(BASE_DIR, "app", "templates", "jeans")
TEXTURE_ROOT = os.path.join(BASE_DIR, "textures")

FABRIC_TEXTURES = {
    "dark_raw_denim": "dark_raw_denim.png",
    "washed_denim": "washed_denim.png",
    "cotton_canvas": "cotton_canvas.png",
    "polyester_smooth": "polyester_smooth.png"
}


def apply_fabric_effect(image, fabric_type):

    texture_path = os.path.join(TEXTURE_ROOT, FABRIC_TEXTURES[fabric_type])

    texture = Image.open(texture_path).convert("RGB")
    texture = texture.resize(image.size)

    # Soft blend (not heavy multiply)
    blended = Image.blend(image.convert("RGB"), texture, alpha=0.25)

    # Ink absorption simulation
    blended = ImageEnhance.Brightness(blended).enhance(0.92)

    # Slight contrast boost
    blended = ImageEnhance.Contrast(blended).enhance(1.05)

    return blended


def clip_artwork_to_panel(panel, artwork):

    panel_mask = panel.split()[3]  # alpha channel mask

    artwork_copy = artwork.copy()
    artwork_copy.thumbnail(panel.size, Image.LANCZOS)

    canvas = Image.new("RGBA", panel.size, (0, 0, 0, 0))

    x = (panel.size[0] - artwork_copy.size[0]) // 2
    y = (panel.size[1] - artwork_copy.size[1]) // 2

    canvas.paste(artwork_copy, (x, y))

    clipped = Image.composite(canvas, Image.new("RGBA", panel.size, (0, 0, 0, 0)), panel_mask)

    return clipped


def generate_print_sheet(size, artwork_path, fabric_type):

    panel_dir = os.path.join(TEMPLATE_ROOT, size)

    panels = [
        "front_left.png",
        "front_right.png",
        "back_left.png",
        "back_right.png"
    ]

    if not os.path.exists(panel_dir):
        raise Exception(f"Template folder not found: {panel_dir}")

    artwork = Image.open(artwork_path).convert("RGBA")

    processed_panels = []

    for panel_name in panels:

        panel_path = os.path.join(panel_dir, panel_name)

        if not os.path.exists(panel_path):
            raise Exception(f"Missing panel file: {panel_path}")

        panel = Image.open(panel_path).convert("RGBA")

        clipped = clip_artwork_to_panel(panel, artwork)

        processed_panels.append(clipped)

    if len(processed_panels) != 4:
        raise Exception("Panel processing failed.")

    # -----------------------------------
    # PRODUCTION PRINT SHEET (Flat Layout)
    # -----------------------------------

    w, h = processed_panels[0].size

    sheet = Image.new("RGBA", (w * 2, h * 2), (255, 255, 255, 255))

    sheet.paste(processed_panels[0], (0, 0), processed_panels[0])
    sheet.paste(processed_panels[1], (w, 0), processed_panels[1])
    sheet.paste(processed_panels[2], (0, h), processed_panels[2])
    sheet.paste(processed_panels[3], (w, h), processed_panels[3])

    os.makedirs("outputs", exist_ok=True)

    print_sheet_path = f"outputs/print_sheet_{size}_{fabric_type}.png"
    sheet.save(print_sheet_path, dpi=(300, 300))

    # # # -----------------------------------
    # # # REALISTIC STITCHED JEANS PREVIEW
    # # # -----------------------------------

    # # preview_canvas = Image.new("RGBA", (w * 2, h * 2), (40, 40, 40, 255))

    # # # Slight inward leg positioning for realism
    # # preview_canvas.paste(processed_panels[0], (100, 0), processed_panels[0])
    # # preview_canvas.paste(processed_panels[1], (w - 100, 0), processed_panels[1])
    # # preview_canvas.paste(processed_panels[2], (100, h), processed_panels[2])
    # # preview_canvas.paste(processed_panels[3], (w - 100, h), processed_panels[3])

    # # realistic_preview = apply_fabric_effect(preview_canvas, fabric_type)

    # # # # Add soft seam shading
    # # # seam_shadow = Image.new("RGBA", realistic_preview.size, (0, 0, 0, 0))
    # # # seam_shadow = seam_shadow.filter(ImageFilter.GaussianBlur(40))

    # # # realistic_preview = Image.blend(realistic_preview, seam_shadow, alpha=0.1)
    # # # Ensure same mode
    # # realistic_preview = realistic_preview.convert("RGB")

    # # # Create subtle vertical seam shading
    # # seam_shadow = Image.new("RGB", realistic_preview.size, (0, 0, 0))
    # # seam_shadow = seam_shadow.filter(ImageFilter.GaussianBlur(80))

    # # realistic_preview = Image.blend(realistic_preview, seam_shadow, alpha=0.05)

    # # preview_path = f"outputs/preview_{size}_{fabric_type}.png"
    # realistic_preview.save(preview_path, dpi=(300, 300))


    # -----------------------------------
    # REALISTIC STITCHED JEANS PREVIEW
    # -----------------------------------

    # preview_width = w * 2
    # preview_height = h * 2

    # preview_canvas = Image.new("RGBA", (preview_width, preview_height), (30, 30, 30, 255))

    # # Merge front panels
    # front_combined = Image.new("RGBA", (w * 2, h), (0, 0, 0, 0))
    # front_combined.paste(processed_panels[0], (0, 0), processed_panels[0])
    # front_combined.paste(processed_panels[1], (w, 0), processed_panels[1])

    # # Merge back panels
    # back_combined = Image.new("RGBA", (w * 2, h), (0, 0, 0, 0))
    # back_combined.paste(processed_panels[2], (0, 0), processed_panels[2])
    # back_combined.paste(processed_panels[3], (w, 0), processed_panels[3])

    # # Slight leg inward perspective effect
    # front_combined = front_combined.transform(
    #     front_combined.size,
    #     Image.PERSPECTIVE,
    #     (1, 0.05, 0, 0.02, 1, 0, 0, 0),
    #     Image.BICUBIC
    # )

    # # Position on canvas
    # preview_canvas.paste(front_combined, (0, 0), front_combined)
    # preview_canvas.paste(back_combined, (0, h), back_combined)

    # # Apply fabric realism
    # realistic_preview = apply_fabric_effect(preview_canvas, fabric_type)

    # # Add depth shading (top light source)
    # shading = Image.new("L", realistic_preview.size, 255)

    # for y in range(realistic_preview.size[1]):
    #     fade = int(255 * (1 - y / realistic_preview.size[1] * 0.4))
    #     for x in range(realistic_preview.size[0]):
    #         shading.putpixel((x, y), fade)

    # shading = shading.filter(ImageFilter.GaussianBlur(120))
    # shading = shading.convert("RGB")

    # realistic_preview = Image.blend(realistic_preview, shading, 0.15)

    # # Add soft vignette
    # vignette = Image.new("L", realistic_preview.size, 0)
    # for y in range(realistic_preview.size[1]):
    #     for x in range(realistic_preview.size[0]):
    #         dx = x - realistic_preview.size[0] / 2
    #         dy = y - realistic_preview.size[1] / 2
    #         dist = (dx*dx + dy*dy) ** 0.5
    #         max_dist = (realistic_preview.size[0]**2 + realistic_preview.size[1]**2) ** 0.5
    #         intensity = int(255 * (dist / max_dist))
    #         vignette.putpixel((x, y), min(intensity, 255))

    # vignette = vignette.filter(ImageFilter.GaussianBlur(200))
    # vignette = vignette.convert("RGB")

    # realistic_preview = ImageChops.multiply(realistic_preview, vignette)

    # preview_path = f"outputs/preview_{size}_{fabric_type}.png"
    # realistic_preview.save(preview_path, dpi=(300, 300))


    # -----------------------------------
    # ULTRA REALISTIC STITCHED PREVIEW
    # -----------------------------------

    preview_width = w * 2
    preview_height = h * 2

    preview_canvas = Image.new("RGBA", (preview_width, preview_height), (25, 25, 25, 255))

    # Merge front panels
    front_combined = Image.new("RGBA", (w * 2, h), (0, 0, 0, 0))
    front_combined.paste(processed_panels[0], (0, 0), processed_panels[0])
    front_combined.paste(processed_panels[1], (w, 0), processed_panels[1])

    # Slight inward perspective (legs closer at bottom)
    front_combined = front_combined.transform(
        front_combined.size,
        Image.PERSPECTIVE,
        (1, 0.08, 0, 0.02, 1, 0, 0, 0),
        Image.BICUBIC
    )

    preview_canvas.paste(front_combined, (0, 0), front_combined)

    # Apply fabric realism
    realistic_preview = apply_fabric_effect(preview_canvas.convert("RGB"), fabric_type)

    draw = ImageDraw.Draw(realistic_preview)

    # -----------------------------------
    # 1️⃣ Waistband Overlay
    # -----------------------------------

    waistband_height = int(h * 0.08)
    draw.rectangle(
        [(0, 0), (preview_width, waistband_height)],
        fill=(40, 40, 50)
    )

    # -----------------------------------
    # 2️⃣ Stitching Thread Lines
    # -----------------------------------

    stitch_color = (240, 200, 120)

    for x in range(0, preview_width, 12):
        draw.line(
            [(x, waistband_height + 5), (x, waistband_height + 8)],
            fill=stitch_color,
            width=1
        )

    # Side seam lines
    draw.line([(w, 0), (w, preview_height)], fill=stitch_color, width=2)

    # -----------------------------------
    # 3️⃣ Pocket Shadow Simulation
    # -----------------------------------

    pocket_width = int(w * 0.35)
    pocket_height = int(h * 0.25)

    pocket_shadow = Image.new("RGBA", realistic_preview.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(pocket_shadow)

    shadow_draw.ellipse(
        [(int(w*0.2), int(h*0.2)),
         (int(w*0.2)+pocket_width, int(h*0.2)+pocket_height)],
        fill=(0, 0, 0, 90)
    )

    pocket_shadow = pocket_shadow.filter(ImageFilter.GaussianBlur(25))
    realistic_preview = Image.alpha_composite(realistic_preview.convert("RGBA"), pocket_shadow).convert("RGB")

    # -----------------------------------
    # 4️⃣ Knee Bend Shading
    # -----------------------------------

    knee_y = int(h * 0.6)

    knee_shadow = Image.new("RGBA", realistic_preview.size, (0, 0, 0, 0))
    ks_draw = ImageDraw.Draw(knee_shadow)

    ks_draw.ellipse(
        [(int(w*0.1), knee_y),
         (int(w*1.9), knee_y + 250)],
        fill=(0, 0, 0, 70)
    )

    knee_shadow = knee_shadow.filter(ImageFilter.GaussianBlur(80))
    realistic_preview = Image.alpha_composite(realistic_preview.convert("RGBA"), knee_shadow).convert("RGB")

    # -----------------------------------
    # 5️⃣ Directional Light Simulation (Top Left)
    # -----------------------------------

    light_layer = Image.new("L", realistic_preview.size)

    for y in range(realistic_preview.size[1]):
        for x in range(realistic_preview.size[0]):
            intensity = int(255 - (x / realistic_preview.size[0]) * 80 - (y / realistic_preview.size[1]) * 60)
            light_layer.putpixel((x, y), max(0, min(255, intensity)))

    light_layer = light_layer.filter(ImageFilter.GaussianBlur(150))
    light_layer = light_layer.convert("RGB")

    realistic_preview = ImageChops.multiply(realistic_preview, light_layer)

    # -----------------------------------
    # Save Final Preview
    # -----------------------------------

    preview_path = f"outputs/preview_{size}_{fabric_type}.png"
    realistic_preview.save(preview_path, dpi=(300, 300))


    return {
        "print_sheet": print_sheet_path,
        "preview": preview_path
    }































# from PIL import Image
# import os

# BASE_PATH = "app/templates/jeans"

# def generate_print_sheet(size, artwork_path):

#     panel_dir = os.path.join(BASE_PATH, size)

#     panels = [
#         "front_left.png",
#         "front_right.png",
#         "back_left.png",
#         "back_right.png"
#     ]

#     artwork = Image.open(artwork_path).convert("RGBA")

#     processed_panels = []

#     # for panel_name in panels:

#     #     panel_path = os.path.join(panel_dir, panel_name)
#     #     panel = Image.open(panel_path).convert("RGBA")

#     #     # Preserve aspect ratio
#     #     artwork_copy = artwork.copy()
#     #     artwork_copy.thumbnail(panel.size, Image.LANCZOS)

#     #     canvas = Image.new("RGBA", panel.size, (0,0,0,0))
#     #     x = (panel.size[0] - artwork_copy.size[0]) // 2
#     #     y = (panel.size[1] - artwork_copy.size[1]) // 2
#     #     canvas.paste(artwork_copy, (x, y))

#     #     final_panel = Image.alpha_composite(panel, canvas)
#     #     processed_panels.append(final_panel)
    

#     # Create sheet canvas
#     w, h = processed_panels[0].size
#     sheet = Image.new("RGBA", (w*2, h*2), (255,255,255,255))

#     sheet.paste(processed_panels[0], (0,0))
#     sheet.paste(processed_panels[1], (w,0))
#     sheet.paste(processed_panels[2], (0,h))
#     sheet.paste(processed_panels[3], (w,h))

#     os.makedirs("outputs", exist_ok=True)

#     sheet_path = f"outputs/print_sheet_{size}.png"
#     sheet.save(sheet_path, dpi=(300,300))

#     return sheet_path