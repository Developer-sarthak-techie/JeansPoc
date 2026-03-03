import os
import uuid
import json
import cv2
import numpy as np
from PIL import Image

from app.services.grading_engine import GradingEngine


Image.MAX_IMAGE_PIXELS = None


class FeatureGradingEngine:
    """
    Grades a multi-piece jeans TIFF (16 pieces) to a target size (32/34).

    The TIFF layout may differ from the DXF layout, so this engine does NOT
    map DXF coordinates to TIFF pixels. Instead, it:
      1. Detects all pieces in the TIFF via contour analysis
      2. Matches each detected piece to a DXF polygon by area
      3. Applies the DXF-derived grading scale to each matched piece
      4. Applies average grading scale to unmatched pieces
      5. Preserves the original TIFF layout (scaled positions)
    """

    def __init__(self, dxf_30, dxf_32, dxf_34):
        self.engine = GradingEngine(dxf_30, dxf_32, dxf_34)
        self._last_dpi = 300

    def process(self, input_path, target_size, dpi=300):
        if target_size not in [30, 32, 34]:
            raise ValueError("Supported sizes: 30, 32, 34")

        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        dpi = self._read_tiff_dpi(input_path, default_dpi=dpi)
        self._last_dpi = dpi
        print(f"[FeatureGrading] Using DPI: {dpi}")

        image = self._load_image(input_path)
        if image is None:
            raise ValueError(f"Failed to load image: {input_path}")

        h_img, w_img = image.shape[:2]
        ch = image.shape[2] if len(image.shape) == 3 else 1
        print(f"[FeatureGrading] Input: {w_img}x{h_img}, channels={ch}")

        base_polys = [rule[0] for rule in self.engine.grade_rules]
        graded_polys = self.engine.grade(target_size)
        n_polys = len(base_polys)
        print(f"[FeatureGrading] DXF polygon count: {n_polys}")

        scale = dpi / 25.4

        poly_scales = self._compute_per_poly_scales(base_polys, graded_polys)
        avg_scale = float(np.mean(poly_scales)) if poly_scales else 1.0
        print(f"[FeatureGrading] Per-poly scales: "
              f"min={min(poly_scales):.4f}, max={max(poly_scales):.4f}, avg={avg_scale:.4f}")

        dxf_areas_px = []
        for bp in base_polys:
            area_dxf = abs(cv2.contourArea(np.array(bp, dtype=np.float32)))
            dxf_areas_px.append(area_dxf * scale * scale)

        pieces = self._detect_pieces(image)
        print(f"[FeatureGrading] Detected {len(pieces)} pieces in TIFF")

        if len(pieces) == 0:
            raise ValueError(
                "No garment pieces detected in the input image. "
                "Ensure the TIFF contains pieces on a contrasting background."
            )

        self._match_pieces_to_dxf(pieces, dxf_areas_px, poly_scales, avg_scale)

        margin = 100
        out_w = int(w_img * avg_scale) + 2 * margin
        out_h = int(h_img * avg_scale) + 2 * margin

        if ch >= 3:
            canvas = np.ones((out_h, out_w, ch), dtype=np.uint8) * 255
        else:
            canvas = np.ones((out_h, out_w), dtype=np.uint8) * 255
        print(f"[FeatureGrading] Output canvas: {out_w}x{out_h}")

        placed = 0
        for i, piece in enumerate(pieces):
            try:
                self._place_graded_piece(image, canvas, piece, margin)
                placed += 1
            except Exception as e:
                print(f"[FeatureGrading] Piece {i} failed: {e}")

        if placed == 0:
            raise RuntimeError("All piece placements failed — output would be empty")

        print(f"[FeatureGrading] Placed {placed}/{len(pieces)} pieces")

        canvas = self._auto_crop(canvas)
        print(f"[FeatureGrading] After crop: {canvas.shape[1]}x{canvas.shape[0]}")

        os.makedirs("outputs", exist_ok=True)
        fid = uuid.uuid4().hex[:8]
        tiff_out = f"outputs/feature_graded_{target_size}_{fid}.tiff"
        png_out = f"outputs/feature_graded_{target_size}_{fid}.png"

        cv2.imwrite(tiff_out, canvas, [cv2.IMWRITE_TIFF_COMPRESSION, 1])

        png_canvas = canvas
        max_png_dim = 10000
        ph, pw = canvas.shape[:2]
        if pw > max_png_dim or ph > max_png_dim:
            ratio = min(max_png_dim / pw, max_png_dim / ph)
            png_canvas = cv2.resize(canvas, (int(pw * ratio), int(ph * ratio)),
                                    interpolation=cv2.INTER_AREA)

        cv2.imwrite(png_out, png_canvas, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        print(f"[FeatureGrading] Saved: {tiff_out}, {png_out}")

        return tiff_out, png_out

    # ================================================================
    # IMAGE LOADING
    # ================================================================

    @staticmethod
    def _read_tiff_dpi(path, default_dpi=300):
        try:
            img = Image.open(path)
            dpi_info = img.info.get("dpi", None)
            img.close()
            if dpi_info and dpi_info[0] > 0:
                return int(dpi_info[0])
        except Exception:
            pass
        return default_dpi

    @staticmethod
    def _load_image(path):
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is not None:
            return img

        pil_img = Image.open(path)
        if pil_img.mode == "RGBA":
            arr = np.array(pil_img)
            img = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)
        elif pil_img.mode == "RGB":
            arr = np.array(pil_img)
            img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        elif pil_img.mode == "L":
            img = np.array(pil_img)
        else:
            pil_img = pil_img.convert("RGB")
            arr = np.array(pil_img)
            img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        pil_img.close()
        return img

    # ================================================================
    # DXF GRADING SCALE COMPUTATION
    # ================================================================

    @staticmethod
    def _compute_per_poly_scales(base_polys, graded_polys):
        scales = []
        for bp, gp in zip(base_polys, graded_polys):
            ba = abs(cv2.contourArea(np.array(bp, dtype=np.float32)))
            ga = abs(cv2.contourArea(np.array(gp, dtype=np.float32)))
            scales.append(np.sqrt(ga / ba) if ba > 0 else 1.0)
        return scales

    # ================================================================
    # PIECE DETECTION
    # ================================================================

    @staticmethod
    def _detect_pieces(image):
        gray = (cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                if len(image.shape) == 3 else image.copy())

        edge_px = np.concatenate([
            gray[0, :], gray[-1, :], gray[:, 0], gray[:, -1]
        ])
        bg = int(np.median(edge_px))

        if bg > 128:
            _, thresh = cv2.threshold(gray, bg - 30, 255, cv2.THRESH_BINARY_INV)
        else:
            _, thresh = cv2.threshold(gray, bg + 30, 255, cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=3)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        h, w = image.shape[:2]
        min_area = h * w * 0.0005

        pieces = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < min_area:
                continue
            M = cv2.moments(c)
            if M["m00"] == 0:
                continue
            pieces.append({
                "contour": c,
                "centroid": (M["m10"] / M["m00"], M["m01"] / M["m00"]),
                "bbox": cv2.boundingRect(c),
                "area": area,
            })

        pieces.sort(key=lambda p: p["area"], reverse=True)
        return pieces

    # ================================================================
    # PIECE-TO-DXF MATCHING BY AREA
    # ================================================================

    @staticmethod
    def _match_pieces_to_dxf(pieces, dxf_areas_px, poly_scales, avg_scale):
        """
        Match each detected TIFF piece to the closest DXF polygon by area.
        DXF polygons come in mirror pairs, so each can match up to 2 pieces.
        """
        match_count = [0] * len(dxf_areas_px)
        matched = 0

        for piece in pieces:
            pa = piece["area"]
            best_idx = -1
            best_ratio = float("inf")

            for j, da in enumerate(dxf_areas_px):
                if match_count[j] >= 2:
                    continue
                ratio = max(pa, da) / max(min(pa, da), 1.0)
                if ratio < best_ratio:
                    best_ratio = ratio
                    best_idx = j

            if best_ratio < 1.25 and best_idx >= 0:
                piece["dxf_idx"] = best_idx
                piece["grade_scale"] = poly_scales[best_idx]
                match_count[best_idx] += 1
                matched += 1
            else:
                piece["dxf_idx"] = -1
                piece["grade_scale"] = avg_scale

        print(f"[FeatureGrading] Matched {matched}/{len(pieces)} pieces to DXF polygons")

    # ================================================================
    # PIECE GRADING AND PLACEMENT
    # ================================================================

    @staticmethod
    def _place_graded_piece(image, canvas, piece, margin):
        x, y, w, h = piece["bbox"]
        contour = piece["contour"]
        gs = piece["grade_scale"]
        h_img, w_img = image.shape[:2]

        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(w_img, x + w), min(h_img, y + h)
        if x2 <= x1 or y2 <= y1:
            return

        crop = image[y1:y2, x1:x2].copy()

        shifted = contour.copy()
        shifted[:, :, 0] -= x1
        shifted[:, :, 1] -= y1
        mask = np.zeros((y2 - y1, x2 - x1), dtype=np.uint8)
        cv2.drawContours(mask, [shifted], -1, 255, -1)

        if len(crop.shape) == 3:
            crop = cv2.bitwise_and(crop, crop, mask=mask)
        else:
            crop = cv2.bitwise_and(crop, mask)

        nw = max(1, int(crop.shape[1] * gs))
        nh = max(1, int(crop.shape[0] * gs))
        scaled_crop = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
        scaled_mask = cv2.resize(mask, (nw, nh), interpolation=cv2.INTER_NEAREST)

        nx = int(x1 * gs) + margin
        ny = int(y1 * gs) + margin

        c_h, c_w = canvas.shape[:2]
        ex = min(c_w, nx + nw)
        ey = min(c_h, ny + nh)
        pw = ex - nx
        ph = ey - ny

        if pw <= 0 or ph <= 0 or nx < 0 or ny < 0:
            return

        region = canvas[ny:ey, nx:ex]
        piece_slice = scaled_crop[:ph, :pw]
        mask_slice = scaled_mask[:ph, :pw]

        inv = cv2.bitwise_not(mask_slice)
        bg = cv2.bitwise_and(region, region, mask=inv)
        fg = cv2.bitwise_and(piece_slice, piece_slice, mask=mask_slice)
        canvas[ny:ey, nx:ex] = cv2.add(bg, fg)

    # ================================================================
    # UTILITIES
    # ================================================================

    @staticmethod
    def _auto_crop(canvas):
        gray = (cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
                if len(canvas.shape) == 3 else canvas)
        _, thresh = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
        coords = cv2.findNonZero(thresh)
        if coords is None:
            return canvas
        bx, by, bw, bh = cv2.boundingRect(coords)
        pad = 100
        y1 = max(0, by - pad)
        x1 = max(0, bx - pad)
        y2 = min(canvas.shape[0], by + bh + pad)
        x2 = min(canvas.shape[1], bx + bw + pad)
        return canvas[y1:y2, x1:x2]

    # ================================================================
    # VERIFICATION SYSTEM
    # ================================================================

    def verify(self, input_path, output_path, target_size):
        """
        Compares input and output TIFFs to verify grading accuracy.

        Returns a dict with:
          - summary: overall pass/fail and stats
          - pieces: per-piece measurements and accuracy
          - visual_report: path to annotated verification image
        """
        dpi = self._read_tiff_dpi(input_path, default_dpi=self._last_dpi)
        mm_per_px = 25.4 / dpi

        base_polys = [rule[0] for rule in self.engine.grade_rules]
        graded_polys = self.engine.grade(target_size)
        scale_px = dpi / 25.4

        poly_scales = self._compute_per_poly_scales(base_polys, graded_polys)
        avg_scale = float(np.mean(poly_scales))

        dxf_areas_px = []
        dxf_areas_mm2 = []
        graded_areas_mm2 = []
        for bp, gp in zip(base_polys, graded_polys):
            ba = abs(cv2.contourArea(np.array(bp, dtype=np.float32)))
            ga = abs(cv2.contourArea(np.array(gp, dtype=np.float32)))
            dxf_areas_px.append(ba * scale_px * scale_px)
            dxf_areas_mm2.append(ba)
            graded_areas_mm2.append(ga)

        img_in = self._load_image(input_path)
        img_out = self._load_image(output_path)

        pieces_in = self._detect_pieces(img_in)
        pieces_out = self._detect_pieces(img_out)

        self._match_pieces_to_dxf(
            pieces_in, dxf_areas_px, poly_scales, avg_scale
        )

        results = []
        errors = []
        area_tolerance = 0.05

        for idx_out, po in enumerate(pieces_out):
            # Find the matching input piece by nearest centroid
            best_in = self._find_nearest_input_piece(
                po, pieces_in, avg_scale
            )

            area_out = po["area"]
            bx, by, bw, bh = po["bbox"]

            record = {
                "piece_index": idx_out,
                "output_area_px": round(area_out),
                "output_area_mm2": round(area_out * mm_per_px * mm_per_px, 2),
                "output_width_mm": round(bw * mm_per_px, 2),
                "output_height_mm": round(bh * mm_per_px, 2),
            }

            if best_in is not None:
                area_in = best_in["area"]
                gs = best_in.get("grade_scale", avg_scale)
                expected_area = area_in * gs * gs
                actual_ratio = np.sqrt(area_out / area_in) if area_in > 0 else 0

                bx_i, by_i, bw_i, bh_i = best_in["bbox"]
                record["input_area_px"] = round(area_in)
                record["input_area_mm2"] = round(area_in * mm_per_px * mm_per_px, 2)
                record["input_width_mm"] = round(bw_i * mm_per_px, 2)
                record["input_height_mm"] = round(bh_i * mm_per_px, 2)
                record["expected_scale"] = round(gs, 5)
                record["actual_scale"] = round(actual_ratio, 5)
                record["scale_error_pct"] = round(
                    abs(actual_ratio - gs) / gs * 100, 3
                )
                record["area_error_pct"] = round(
                    abs(area_out - expected_area) / expected_area * 100, 3
                )

                dxf_idx = best_in.get("dxf_idx", -1)
                if dxf_idx >= 0:
                    expected_mm2 = graded_areas_mm2[dxf_idx]
                    record["dxf_expected_area_mm2"] = round(expected_mm2, 2)
                    record["dxf_match"] = True
                else:
                    record["dxf_match"] = False

                if record["scale_error_pct"] > area_tolerance * 100:
                    record["status"] = "WARN"
                    errors.append(
                        f"Piece {idx_out}: scale error {record['scale_error_pct']:.2f}%"
                    )
                else:
                    record["status"] = "PASS"
            else:
                record["input_area_px"] = None
                record["status"] = "UNMATCHED"
                errors.append(f"Piece {idx_out}: no matching input piece")

            results.append(record)

        pass_count = sum(1 for r in results if r["status"] == "PASS")
        warn_count = sum(1 for r in results if r["status"] == "WARN")
        fail_count = sum(1 for r in results if r["status"] == "UNMATCHED")

        overall = "PASS" if pass_count == len(results) else (
            "WARN" if fail_count == 0 else "FAIL"
        )

        visual_path = self._generate_visual_report(
            img_in, img_out, pieces_in, pieces_out, results, target_size, dpi
        )

        report = {
            "summary": {
                "overall": overall,
                "target_size": target_size,
                "dpi": dpi,
                "input_pieces": len(pieces_in),
                "output_pieces": len(pieces_out),
                "passed": pass_count,
                "warnings": warn_count,
                "unmatched": fail_count,
                "avg_expected_scale": round(avg_scale, 5),
                "errors": errors,
            },
            "pieces": results,
            "visual_report": visual_path,
        }

        os.makedirs("outputs", exist_ok=True)
        report_path = f"outputs/verification_{target_size}_{uuid.uuid4().hex[:6]}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        return report, report_path

    @staticmethod
    def _find_nearest_input_piece(output_piece, input_pieces, avg_scale):
        """Match an output piece to the nearest input piece by area ratio."""
        oa = output_piece["area"]
        best = None
        best_diff = float("inf")

        for ip in input_pieces:
            expected_out_area = ip["area"] * ip.get("grade_scale", avg_scale) ** 2
            diff = abs(oa - expected_out_area) / max(expected_out_area, 1.0)
            if diff < best_diff:
                best_diff = diff
                best = ip

        return best if best_diff < 0.3 else None

    def _generate_visual_report(self, img_in, img_out, pieces_in, pieces_out,
                                results, target_size, dpi):
        """
        Creates an annotated side-by-side comparison image.
        Left = input with piece outlines, Right = output with measured dimensions.
        Green = PASS, Yellow = WARN, Red = UNMATCHED.
        """
        max_dim = 4000
        h_in, w_in = img_in.shape[:2]
        h_out, w_out = img_out.shape[:2]

        r_in = min(max_dim / w_in, max_dim / h_in, 1.0)
        r_out = min(max_dim / w_out, max_dim / h_out, 1.0)
        ratio = min(r_in, r_out)

        small_in = cv2.resize(img_in, (int(w_in * ratio), int(h_in * ratio)),
                              interpolation=cv2.INTER_AREA)
        small_out = cv2.resize(img_out, (int(w_out * ratio), int(h_out * ratio)),
                               interpolation=cv2.INTER_AREA)

        sh_in, sw_in = small_in.shape[:2]
        sh_out, sw_out = small_out.shape[:2]
        gap = 40
        max_h = max(sh_in, sh_out)
        canvas_w = sw_in + gap + sw_out
        header_h = 80
        footer_h = 120

        if len(small_in.shape) == 2:
            small_in = cv2.cvtColor(small_in, cv2.COLOR_GRAY2BGR)
        if len(small_out.shape) == 2:
            small_out = cv2.cvtColor(small_out, cv2.COLOR_GRAY2BGR)

        vis = np.ones((header_h + max_h + footer_h, canvas_w, 3),
                      dtype=np.uint8) * 255

        vis[header_h:header_h + sh_in, :sw_in] = small_in
        vis[header_h:header_h + sh_out, sw_in + gap:sw_in + gap + sw_out] = small_out

        vis[header_h:header_h + max_h, sw_in:sw_in + gap] = (200, 200, 200)

        font = cv2.FONT_HERSHEY_SIMPLEX
        mm_per_px = 25.4 / dpi

        cv2.putText(vis, f"INPUT (Size 30)", (10, 50),
                    font, 1.5, (0, 0, 0), 3)
        cv2.putText(vis, f"OUTPUT (Size {target_size})", (sw_in + gap + 10, 50),
                    font, 1.5, (0, 0, 0), 3)

        for i, pi in enumerate(pieces_in):
            cnt = (pi["contour"] * ratio).astype(np.int32)
            cv2.drawContours(vis[header_h:header_h + sh_in, :sw_in],
                             [cnt], -1, (255, 180, 0), 2)

            bx, by, bw, bh = pi["bbox"]
            cx = int((bx + bw / 2) * ratio)
            cy = int((by + bh / 2) * ratio) + header_h
            w_mm = bw * mm_per_px
            h_mm = bh * mm_per_px
            label = f"{w_mm:.0f}x{h_mm:.0f}mm"
            cv2.putText(vis, label, (cx - 60, cy),
                        font, 0.5, (0, 0, 200), 1)

        color_map = {"PASS": (0, 180, 0), "WARN": (0, 200, 255), "UNMATCHED": (0, 0, 255)}

        for i, po in enumerate(pieces_out):
            status = results[i]["status"] if i < len(results) else "UNMATCHED"
            color = color_map.get(status, (0, 0, 255))

            cnt = (po["contour"] * ratio).astype(np.int32)
            cnt[:, :, 0] += sw_in + gap
            cv2.drawContours(vis[header_h:header_h + sh_out, sw_in + gap:sw_in + gap + sw_out],
                             [(po["contour"] * ratio).astype(np.int32)], -1, color, 2)

            bx, by, bw, bh = po["bbox"]
            cx = int((bx + bw / 2) * ratio) + sw_in + gap
            cy = int((by + bh / 2) * ratio) + header_h
            w_mm = bw * mm_per_px
            h_mm = bh * mm_per_px
            label = f"{w_mm:.0f}x{h_mm:.0f}mm"
            cv2.putText(vis, label, (cx - 60, cy), font, 0.5, color, 1)

            if i < len(results) and results[i].get("actual_scale") is not None:
                s_label = f"x{results[i]['actual_scale']:.3f}"
                cv2.putText(vis, s_label, (cx - 40, cy + 20), font, 0.45, color, 1)

        pass_count = sum(1 for r in results if r["status"] == "PASS")
        warn_count = sum(1 for r in results if r["status"] == "WARN")
        fail_count = sum(1 for r in results if r["status"] == "UNMATCHED")
        avg_scale = np.mean([
            r["actual_scale"] for r in results if r.get("actual_scale") is not None
        ]) if results else 0

        y_footer = header_h + max_h + 30
        cv2.putText(vis, f"VERIFICATION: {pass_count} PASS | {warn_count} WARN | {fail_count} FAIL",
                    (10, y_footer), font, 0.9, (0, 0, 0), 2)
        cv2.putText(vis, f"Avg measured scale: {avg_scale:.4f} | Target: size {target_size}",
                    (10, y_footer + 35), font, 0.7, (80, 80, 80), 2)
        cv2.putText(vis, f"Green=PASS (<5% error) | Yellow=WARN (>5%) | Red=UNMATCHED",
                    (10, y_footer + 65), font, 0.6, (120, 120, 120), 1)

        os.makedirs("outputs", exist_ok=True)
        vis_path = f"outputs/verification_visual_{target_size}_{uuid.uuid4().hex[:6]}.png"
        cv2.imwrite(vis_path, vis, [cv2.IMWRITE_PNG_COMPRESSION, 5])

        return vis_path
