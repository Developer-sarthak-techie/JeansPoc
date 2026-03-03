import os
import uuid
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

    def process(self, input_path, target_size, dpi=300):
        if target_size not in [30, 32, 34]:
            raise ValueError("Supported sizes: 30, 32, 34")

        dpi = self._read_tiff_dpi(input_path, default_dpi=dpi)
        print(f"[FeatureGrading] Using DPI: {dpi}")

        image = self._load_image(input_path)
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
