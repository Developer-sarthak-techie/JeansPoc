from PIL import Image, ImageDraw
from app.patterns.base_pattern import BASE_PATTERN
from app.patterns.grading_rules import GRADING_RULES

def generate_cut_overlay(seamless_path, size):

    fabric = Image.open(seamless_path).convert("RGBA")
    draw = ImageDraw.Draw(fabric)

    rule = GRADING_RULES[size]

    for piece_name, points in BASE_PATTERN.items():

        graded_points = []

        for x, y in points:
            graded_x = x + rule["x_shift"]
            graded_y = y + rule["y_shift"]
            graded_points.append((graded_x, graded_y))

        # Draw dotted cut line
        for i in range(len(graded_points)):
            start = graded_points[i]
            end = graded_points[(i + 1) % len(graded_points)]

            draw_dotted_line(draw, start, end, color=(0,0,0), width=4)

    output_path = f"outputs/final_print_with_cutlines_{size}.png"
    fabric.save(output_path, dpi=(300,300))

    return output_path


def draw_dotted_line(draw, start, end, color, width=2, gap=20):

    from math import hypot

    x1, y1 = start
    x2, y2 = end

    length = hypot(x2 - x1, y2 - y1)
    dx = (x2 - x1) / length
    dy = (y2 - y1) / length

    for i in range(0, int(length), gap * 2):
        x_start = x1 + dx * i
        y_start = y1 + dy * i

        x_end = x1 + dx * (i + gap)
        y_end = y1 + dy * (i + gap)

        draw.line([(x_start, y_start), (x_end, y_end)], fill=color, width=width)