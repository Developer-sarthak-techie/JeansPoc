from PIL import Image, ImageEnhance
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FABRIC_PROFILES = {
    "dark_raw_denim": {
        "texture": "dark_raw_denim.png",
        "absorption": 0.12,
        "contrast": 1.05
    },
    "washed_denim": {
        "texture": "washed_denim.png",
        "absorption": 0.08,
        "contrast": 1.02
    },
    "cotton_canvas": {
        "texture": "cotton_canvas.png",
        "absorption": 0.06,
        "contrast": 1.00
    },
    "polyester_smooth": {
        "texture": "polyester_smooth.png",
        "absorption": 0.03,
        "contrast": 1.08
    }
}

def apply_fabric_effect(image, fabric_type):

    profile = FABRIC_PROFILES[fabric_type]
    texture_path = os.path.join(BASE_DIR, "textures", profile["texture"])

    texture = Image.open(texture_path).convert("RGB")
    texture = texture.resize(image.size)

    # Blend texture softly
    blended = Image.blend(image, texture, alpha=0.2)

    # Simulate ink absorption
    blended = ImageEnhance.Brightness(blended).enhance(1 - profile["absorption"])

    # Slight contrast boost
    blended = ImageEnhance.Contrast(blended).enhance(profile["contrast"])

    return blended