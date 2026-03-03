# from PIL import Image, ImageEnhance, ImageChops, ImageFilter
# import numpy as np

# # -----------------------------
# # ADVANCED FABRIC RENDER ENGINE
# # -----------------------------

# # Load fabric texture
# texture = Image.open(TEXTURE_PATH).convert("RGB").resize(final.size)

# # Convert both to numpy for better blending
# art_np = np.array(final.convert("RGB"), dtype=np.float32) / 255.0
# tex_np = np.array(texture, dtype=np.float32) / 255.0

# # 1️⃣ Ink absorption simulation
# # Dark fabrics absorb 10–15% brightness
# absorption_strength = 0.12
# art_np = art_np * (1 - absorption_strength)

# # 2️⃣ Preserve original highlights (prevents dull look)
# highlight_mask = np.clip(tex_np * 1.3, 0, 1)
# art_np = art_np * (1 - highlight_mask * 0.1) + art_np

# # 3️⃣ Fabric weave interaction
# # Instead of multiply, modulate with texture luminance
# texture_luminance = np.mean(tex_np, axis=2, keepdims=True)
# blend_strength = 0.25
# art_np = art_np * (1 - blend_strength) + (art_np * texture_luminance) * blend_strength

# # 4️⃣ Add subtle micro contrast
# contrast_boost = 1.05
# art_np = np.clip((art_np - 0.5) * contrast_boost + 0.5, 0, 1)

# # Convert back to image
# realistic = Image.fromarray((art_np * 255).astype(np.uint8))

# # Slight softness to embed ink into threads
# realistic = realistic.filter(ImageFilter.GaussianBlur(0.5))



 #checkpoint 4 - added noise and vignette for extra realism, also switched to thumbnail for better aspect ratio handling
from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps
import os
import random

BASE_PATH = "app/templates"

def process_design(size: str, user_image_path: str):

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    TEXTURE_PATH = os.path.join(BASE_DIR, "textures", "dark_raw_denim_texture_4000x4000.png")

    template_path = os.path.join(BASE_PATH, size, "template.png")
    mask_path = os.path.join(BASE_PATH, size, "mask.png")

    template = Image.open(template_path).convert("RGBA")
    mask = Image.open(mask_path).convert("L")
    design = Image.open(user_image_path).convert("RGBA")

    #design_resized = design.resize(template.size)
    design.thumbnail(template.size, Image.LANCZOS)

    canvas = Image.new("RGBA", template.size, (0,0,0,0))
    x = (template.size[0] - design.size[0]) // 2
    y = (template.size[1] - design.size[1]) // 2
    canvas.paste(design, (x, y))

    design_resized = canvas

    # Apply mask
    final = Image.composite(design_resized, template, mask)

    # -----------------------------
    # REALISM ENGINE START
    # -----------------------------

    texture = Image.open(TEXTURE_PATH).convert("RGBA").resize(final.size)

    # 1️⃣ Multiply with denim texture
    # realistic = ImageChops.multiply(final, texture)
    realistic = Image.blend(final, texture, alpha=0.2)

    # 2️⃣ Slight ink absorption simulation
    realistic = ImageEnhance.Color(realistic).enhance(0.88)
    realistic = ImageEnhance.Brightness(realistic).enhance(0.94)

    # 3️⃣ Add subtle fabric grain noise
    noise = Image.effect_noise(realistic.size, 8)
    noise = noise.convert("RGBA")
    noise = ImageEnhance.Brightness(noise).enhance(0.2)
    realistic = ImageChops.overlay(realistic, noise)

    # 4️⃣ Add edge shadow for depth (vignette style)
    vignette = Image.new("L", realistic.size, 0)
    for y in range(realistic.size[1]):
        for x in range(realistic.size[0]):
            distance = min(
                x,
                y,
                realistic.size[0] - x,
                realistic.size[1] - y
            )
            shade = int(255 * (distance / 600))
            shade = max(0, min(255, shade))
            vignette.putpixel((x, y), shade)

    vignette = vignette.filter(ImageFilter.GaussianBlur(150))
    vignette = ImageOps.invert(vignette)
    vignette = vignette.convert("RGBA")

    realistic = ImageChops.multiply(realistic, vignette)

    # -----------------------------
    # SAVE OUTPUTS
    # -----------------------------

    os.makedirs("outputs", exist_ok=True)

    preview_path = f"outputs/realistic_preview_{size}.png"
    print_path = f"outputs/print_ready_{size}.png"

    realistic.save(preview_path, dpi=(300, 300))
    final.save(print_path, dpi=(300, 300))

    return {
        "preview": preview_path,
        "print_file": print_path
    }

#second checkpoint for fabric realism - added desaturation and brightness adjustments

# from PIL import Image, ImageChops, ImageEnhance
# import os

# BASE_PATH = "app/templates"
# TEXTURE_PATH = "textures/dark_raw_denim_texture_4000x4000.png"

# def process_design(size: str, user_image_path: str):

#     template_path = os.path.join(BASE_PATH, size, "template.png")
#     mask_path = os.path.join(BASE_PATH, size, "mask.png")

#     # Load files
#     template = Image.open(template_path).convert("RGBA")
#     mask = Image.open(mask_path).convert("L")
#     design = Image.open(user_image_path).convert("RGBA")

#     # Resize design to match template
#     design_resized = design.resize(template.size)

#     # Apply mask (fill inside garment)
#     final = Image.composite(design_resized, template, mask)

#     # -----------------------------
#     # FABRIC REALISM SECTION
#     # -----------------------------

#     # Load texture and resize to match output
#     texture = Image.open(TEXTURE_PATH).convert("RGBA")
#     texture = texture.resize(final.size)

#     # Multiply blend for denim effect
#     realistic = ImageChops.multiply(final, texture)

#     # Slight desaturation (ink absorption simulation)
#     color_enhancer = ImageEnhance.Color(realistic)
#     realistic = color_enhancer.enhance(0.9)

#     # Slight brightness reduction
#     brightness_enhancer = ImageEnhance.Brightness(realistic)
#     realistic = brightness_enhancer.enhance(0.95)

#     # -----------------------------
#     # Save Outputs
#     # -----------------------------

#     os.makedirs("outputs", exist_ok=True)

#     preview_path = f"outputs/realistic_preview_{size}.png"
#     print_path = f"outputs/print_ready_{size}.png"

#     # Save preview (fabric realistic)
#     realistic.save(preview_path, dpi=(300, 300))

#     # Save clean print version (without texture)
#     final.save(print_path, dpi=(300, 300))

#     return {
#         "preview": preview_path,
#         "print_file": print_path
#     }






# first checkpoint for fabric realism - basic multiply blend with texture


# from PIL import Image
# import os
# from PIL import ImageChops

# BASE_PATH = "app/templates"

# def process_design(size: str, user_image_path: str):

#     template_path = os.path.join(BASE_PATH, size, "template.png")
#     mask_path = os.path.join(BASE_PATH, size, "mask.png")

#     template = Image.open(template_path).convert("RGBA")
#     mask = Image.open(mask_path).convert("L")
#     design = Image.open(user_image_path).convert("RGBA")



#     texture = Image.open("textures/dark_raw_denim_texture_4000x4000.png").resize(final.size)

# # Multiply blend for fabric realism
#     realistic = ImageChops.multiply(final, texture)

#     realistic.save("outputs/realistic_preview.png", dpi=(300, 300))

#     # Resize user image to template size
#     design_resized = design.resize(template.size)

#     # Apply mask
#     final = Image.composite(design_resized, template, mask)

#     # Optional: Blend with template for better integration
#     # final = Image.blend(template, final, alpha=0.5)  #
#     Image.blend()
#     ImageChops.multiply()
#     Image.transform()

#     output_path = f"outputs/output_{size}.png"
#     final.save(output_path, dpi=(300, 300))

#     return output_path