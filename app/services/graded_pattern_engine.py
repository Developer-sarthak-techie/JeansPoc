from PIL import Image, ImageDraw
from app.patterns.base_pattern import BASE_PATTERN
from app.patterns.grading_rules import GRADING_RULES

# def generate_graded_mask(size, canvas_size):

#     rule = GRADING_RULES[size]

#     img = Image.new("L", canvas_size, 255)  # L = grayscale, white background
#     draw = ImageDraw.Draw(img)

#     for piece, points in BASE_PATTERN.items():

#         graded_points = []

#         for x, y in points:
#             graded_x = x + rule["x_shift"]
#             graded_y = y + rule["y_shift"]
#             graded_points.append((graded_x, graded_y))

#         draw.polygon(graded_points, fill=0)  # garment area black

    # return img
def generate_graded_mask(size, canvas_size):

    rule = GRADING_RULES[size]

    img = Image.new("RGBA", canvas_size, (0,0,0,0))
    draw = ImageDraw.Draw(img)

    for piece, points in BASE_PATTERN.items():

        graded_points = []

        for x, y in points:
            graded_x = x + rule["x_shift"]
            graded_y = y + rule["y_shift"]
            graded_points.append((graded_x, graded_y))

        draw.polygon(graded_points, fill=(255,255,255,255))

    return img