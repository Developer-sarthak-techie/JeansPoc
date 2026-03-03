from PIL import Image, ImageDraw

CM_TO_INCH = 2.54

def cm_to_pixels(cm, dpi):
    return int(cm * dpi / CM_TO_INCH)


def generate_scaled_pattern(width_cm, height_cm, dpi=300):

    width_px = cm_to_pixels(width_cm, dpi)
    height_px = cm_to_pixels(height_cm, dpi)

    img = Image.new("RGBA", (width_px, height_px), (255,255,255,255))
    draw = ImageDraw.Draw(img)

    # Example: draw sample blueprint rectangle
    draw.rectangle(
        [(100,100), (width_px-100, height_px-100)],
        outline="black",
        width=8
    )

    # Add dotted marker border
    gap = 40
    for x in range(0, width_px, gap*2):
        draw.line([(x,0),(x+gap,0)], fill="black", width=3)
        draw.line([(x,height_px),(x+gap,height_px)], fill="black", width=3)

    output_path = f"outputs/scaled_pattern_{width_cm}x{height_cm}.png"
    img.save(output_path, dpi=(dpi,dpi))

    return output_path