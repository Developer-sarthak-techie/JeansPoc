import math
import ezdxf
from ezdxf import recover


class GradingEngine:

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self, dxf30, dxf32, dxf34):

        self.doc30 = self.load_dxf(dxf30)
        self.doc32 = self.load_dxf(dxf32)
        self.doc34 = self.load_dxf(dxf34)

        self.base_polygons = self.extract_polygons(self.doc30)
        self.polygons_32 = self.extract_polygons(self.doc32)
        self.polygons_34 = self.extract_polygons(self.doc34)

        if not self.base_polygons:
            raise Exception("No base polygons found in size 30 DXF")

        if len(self.base_polygons) != len(self.polygons_34):
            raise Exception("Pattern piece count mismatch between 30 and 34")

        self.grade_rules = self.compute_grading_rules()

    # ==========================================================
    # DXF LOADING
    # ==========================================================

    def load_dxf(self, path):
        doc, auditor = recover.readfile(path)
        return doc

    # ==========================================================
    # POLYGON EXTRACTION
    # ==========================================================

    def extract_polygons(self, doc):

        msp = doc.modelspace()
        polygons = []

        for insert in msp.query("INSERT"):

            block = doc.blocks.get(insert.dxf.name)
            matrix = insert.matrix44()

            for entity in block:

                if entity.dxftype() in ["LWPOLYLINE", "POLYLINE"]:

                    pts = []

                    if entity.dxftype() == "LWPOLYLINE":
                        for p in entity:
                            x, y, _ = matrix.transform((p[0], p[1], 0))
                            pts.append((x, y))

                    else:
                        for v in entity.vertices:
                            x = v.dxf.location.x
                            y = v.dxf.location.y
                            tx, ty, _ = matrix.transform((x, y, 0))
                            pts.append((tx, ty))

                    if len(pts) > 3:
                        polygons.append(pts)

        return polygons

    # ==========================================================
    # GEOMETRY UTILITIES
    # ==========================================================

    def cumulative_lengths(self, poly):

        lengths = [0]
        total = 0

        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            seg = math.hypot(x2 - x1, y2 - y1)
            total += seg
            lengths.append(total)

        return lengths, total

    def interpolate_polygon(self, poly, target_count=200):

        lengths, total_length = self.cumulative_lengths(poly)
        resampled = []

        for i in range(target_count):

            target_len = (i / target_count) * total_length

            for j in range(len(lengths) - 1):

                if lengths[j] <= target_len <= lengths[j + 1]:

                    seg_len = lengths[j + 1] - lengths[j]
                    if seg_len == 0:
                        ratio = 0
                    else:
                        ratio = (target_len - lengths[j]) / seg_len

                    x1, y1 = poly[j % len(poly)]
                    x2, y2 = poly[(j + 1) % len(poly)]

                    x = x1 + ratio * (x2 - x1)
                    y = y1 + ratio * (y2 - y1)

                    resampled.append((x, y))
                    break

        return resampled

    # ==========================================================
    # COMPUTE GRADING RULES
    # ==========================================================

    def compute_grading_rules(self):

        rules = []

        for base_poly, poly34 in zip(self.base_polygons,
                                     self.polygons_34):

            # Resample both to identical vertex count
            base_resampled = self.interpolate_polygon(base_poly, 200)
            poly34_resampled = self.interpolate_polygon(poly34, 200)

            poly_rules = []

            for (x30, y30), (x34, y34) in zip(base_resampled,
                                              poly34_resampled):

                # Size 34 is +2 sizes from 30
                dx = (x34 - x30) / 2
                dy = (y34 - y30) / 2

                poly_rules.append((dx, dy))

            rules.append((base_resampled, poly_rules))

        return rules

    # ==========================================================
    # GRADE TO TARGET SIZE
    # ==========================================================

    def grade(self, target_size):

        if target_size not in [30, 32, 34]:
            raise Exception("Supported sizes: 30, 32, 34")

        size_diff = (target_size - 30) // 2
        graded_polygons = []

        for base_resampled, poly_rules in self.grade_rules:

            graded_poly = []

            for (x, y), (dx, dy) in zip(base_resampled, poly_rules):
                graded_poly.append(
                    (x + dx * size_diff,
                     y + dy * size_diff)
                )

            graded_polygons.append(graded_poly)

        return graded_polygons
    
































# import math
# import ezdxf
# import numpy as np
# from ezdxf import recover


# class GradingEngine:

#     def polygon_perimeter(poly):
#         length = 0
#         for i in range(len(poly)):
#             x1, y1 = poly[i]
#             x2, y2 = poly[(i + 1) % len(poly)]
#             length += math.hypot(x2 - x1, y2 - y1)
#         return length


#     def cumulative_lengths(poly):
#         lengths = [0]
#         total = 0
#         for i in range(len(poly)):
#             x1, y1 = poly[i]
#             x2, y2 = poly[(i + 1) % len(poly)]
#             total += math.hypot(x2 - x1, y2 - y1)
#             lengths.append(total)
#         return lengths, total


#     def interpolate_polygon(poly, target_count):
#         """
#         Resample polygon to fixed vertex count
#         """
#         lengths, total_length = cumulative_lengths(poly)
#         resampled = []

#         for i in range(target_count):
#             target_len = (i / target_count) * total_length

#             for j in range(len(lengths)-1):
#                 if lengths[j] <= target_len <= lengths[j+1]:
#                     ratio = ((target_len - lengths[j]) /
#                             (lengths[j+1] - lengths[j] + 1e-9))

#                     x1, y1 = poly[j % len(poly)]
#                     x2, y2 = poly[(j+1) % len(poly)]

#                     x = x1 + ratio * (x2 - x1)
#                     y = y1 + ratio * (y2 - y1)
#                     resampled.append((x, y))
#                     break








#         return resampled
#     def __init__(self, dxf30, dxf32, dxf34):
#         self.doc30 = self.load_dxf(dxf30)
#         self.doc32 = self.load_dxf(dxf32)
#         self.doc34 = self.load_dxf(dxf34)

#         self.base_polygons = self.extract_polygons(self.doc30)
#         self.polygons_32 = self.extract_polygons(self.doc32)
#         self.polygons_34 = self.extract_polygons(self.doc34)

#         if not self.base_polygons:
#             raise Exception("No base polygons found in size 30 DXF")

#         self.grade_rules = self.compute_grading_rules()

#     def load_dxf(self, path):
#         doc, _ = recover.readfile(path)
#         return doc

#     def extract_polygons(self, doc):
#         msp = doc.modelspace()
#         polygons = []

#         for insert in msp.query("INSERT"):
#             block = doc.blocks.get(insert.dxf.name)
#             matrix = insert.matrix44()

#             for entity in block:
#                 if entity.dxftype() in ["LWPOLYLINE", "POLYLINE"]:
#                     pts = []

#                     if entity.dxftype() == "LWPOLYLINE":
#                         for p in entity:
#                             x, y, _ = matrix.transform((p[0], p[1], 0))
#                             pts.append((x, y))
#                     else:
#                         for v in entity.vertices:
#                             x = v.dxf.location.x
#                             y = v.dxf.location.y
#                             tx, ty, _ = matrix.transform((x, y, 0))
#                             pts.append((tx, ty))

#                     if len(pts) > 3:
#                         polygons.append(pts)

#         return polygons

#     # def compute_grading_rules(self):
#     #     rules = []

#     #     for base_poly, poly32, poly34 in zip(
#     #         self.base_polygons,
#     #         self.polygons_32,
#     #         self.polygons_34
#     #     ):
#     #         poly_rules = []

#     #         for i in range(len(base_poly)):
#     #             x30, y30 = base_poly[i]
#     #             x32, y32 = poly32[i]
#     #             x34, y34 = poly34[i]

#     #             inc_x = ((x32 - x30) + (x34 - x30) / 2) / 2
#     #             inc_y = ((y32 - y30) + (y34 - y30) / 2) / 2

#     #             poly_rules.append((inc_x, inc_y))

#     #         rules.append(poly_rules)

#     #     return rules
#     def compute_grading_rules(self):
#         rules = []

#         for base_poly, poly34 in zip(self.base_polygons, self.polygons_34):

#             # 🔥 Force both polygons to same vertex count
#             target_count = 200  # CAD-safe resolution

#             base_resampled = interpolate_polygon(base_poly, target_count)
#             poly34_resampled = interpolate_polygon(poly34, target_count)

#             poly_rules = []

#             for (x30, y30), (x34, y34) in zip(base_resampled, poly34_resampled):
#                 inc_x = (x34 - x30) / 2
#                 inc_y = (y34 - y30) / 2
#                 poly_rules.append((inc_x, inc_y))

#             rules.append((base_resampled, poly_rules))

#         return rules

#     # def grade(self, target_size):
#     #     size_diff = (target_size - 30) // 2

#     #     graded_polygons = []

#     #     for base_poly, poly_rules in zip(self.base_polygons, self.grade_rules):

#     #         graded_poly = []

#     #         for (x, y), (dx, dy) in zip(base_poly, poly_rules):
#     #             graded_poly.append(
#     #                 (x + dx * size_diff, y + dy * size_diff)
#     #             )

#     #         graded_polygons.append(graded_poly)

#     #     return graded_polygons


#     def grade(self, target_size):

#         size_diff = (target_size - 30) // 2
#         graded_polygons = []

#         for base_resampled, poly_rules in self.grade_rules:

#             graded_poly = []

#             for (x, y), (dx, dy) in zip(base_resampled, poly_rules):
#                 graded_poly.append((x + dx * size_diff,
#                                     y + dy * size_diff))

#             graded_polygons.append(graded_poly)

#         return graded_polygons
