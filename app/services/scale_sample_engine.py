from PIL import Image
import os

CM_TO_INCH = 2.54
MAX_PIXELS = 200_000_000
#MAX_PIXELS = 40_000_000  # safety cap (~40MP)


def cm_to_pixels(cm, dpi):
    return int(cm * dpi / CM_TO_INCH)


def generate_scaled_from_sample(sample_path, width_cm, height_cm, dpi=300):


    max_pixels = 40_000_000

    width_px = cm_to_pixels(width_cm, dpi)
    height_px = cm_to_pixels(height_cm, dpi)

    total_pixels = width_px * height_px 

    if total_pixels > max_pixels:
        scale_factor = (max_pixels / total_pixels) ** 0.5
        width_px = int(width_px * scale_factor)
        height_px = int(height_px * scale_factor)
        sample = Image.open(sample_path).convert("RGBA")

    width_px = cm_to_pixels(width_cm, dpi)
    height_px = cm_to_pixels(height_cm, dpi)

    total_pixels = width_px * height_px

    if total_pixels > MAX_PIXELS:
        raise Exception("Requested size too large. Reduce dimensions or DPI.")

    # Scale sample to exact target size
    scaled = sample.resize((width_px, height_px), Image.LANCZOS)

    os.makedirs("outputs", exist_ok=True)

    output_path = f"outputs/scaled_{width_cm}x{height_cm}_{dpi}dpi.png"
    scaled.save(output_path, dpi=(dpi, dpi))

    return output_path