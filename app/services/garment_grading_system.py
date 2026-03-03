import ezdxf
import numpy as np
from ezdxf import recover


def load_dxf(path):
    doc, _ = recover.readfile(path)
    return doc


def extract_polygons(doc):
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


def compute_grading_vectors(base_poly, size32_poly, size34_poly):
    grade_rules = []

    for i in range(len(base_poly)):
        x30, y30 = base_poly[i]
        x32, y32 = size32_poly[i]
        x34, y34 = size34_poly[i]

        inc32_x = x32 - x30
        inc32_y = y32 - y30

        inc34_x = (x34 - x30) / 2
        inc34_y = (y34 - y30) / 2

        grade_rules.append((
            (inc32_x + inc34_x) / 2,
            (inc32_y + inc34_y) / 2
        ))

    return grade_rules