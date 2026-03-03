from PIL import Image
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_seamless_print(panel_path, design_path):

    panel = Image.open(panel_path).convert("RGBA")
    design = Image.open(design_path).convert("RGBA")

    # Create large fabric canvas same size as panel
    fabric_canvas = Image.new("RGBA", panel.size)

    # Scale design to fully cover panel (no gaps)
    scale_ratio = max(
        panel.size[0] / design.size[0],
        panel.size[1] / design.size[1]
    )

    new_size = (
        int(design.size[0] * scale_ratio),
        int(design.size[1] * scale_ratio)
    )

    design_resized = design.resize(new_size, Image.LANCZOS)

    # Center design on fabric
    x = (panel.size[0] - design_resized.size[0]) // 2
    y = (panel.size[1] - design_resized.size[1]) // 2

    fabric_canvas.paste(design_resized, (x, y))

    # Extract alpha mask from panel
    panel_mask = panel.split()[3]

    # Clip fabric using panel mask
    final_print = Image.composite(fabric_canvas, Image.new("RGBA", panel.size), panel_mask)

    output_path = "outputs/seamless_print_ready.png"
    final_print.save(output_path, dpi=(300, 300))

    return output_path