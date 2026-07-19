"""Drawing QTO Block - Quantity Take-Off from DXF/DWG construction drawings"""

import os
import re
import math
import tempfile
from typing import Any, Dict, List, Tuple, Optional
from app.core.universal_base import UniversalBlock


# DXF INSUNITS code → multiplier to convert that unit to meters.
# 0 = unitless (legacy default mm); 1 = in; 2 = ft; 3 = miles;
# 4 = mm; 5 = cm; 6 = m; 7 = km.
_DXF_UNIT_TO_METERS = {
    0: 0.001,
    1: 0.0254,
    2: 0.3048,
    3: 1609.344,
    4: 0.001,
    5: 0.01,
    6: 1.0,
    7: 1000.0,
}


def _doc_units_to_meters(doc, override_scale: float = 1.0) -> Tuple[float, int]:
    """Return (multiplier-to-meters, raw_INSUNITS_code) for a DXF doc.

    Falls back to mm for unitless drawings — that matches the previous
    hard-coded behaviour and keeps existing call sites stable.
    """
    try:
        u = int(doc.units) if hasattr(doc, "units") else 0
    except (TypeError, ValueError):
        u = 0
    return _DXF_UNIT_TO_METERS.get(u, 0.001) * override_scale, u


class DrawingQTOBlock(UniversalBlock):
    name = "drawing_qto"
    version = "1.0.0"
    updated_at = "2026-07-19"
    description = "Extract measurements, areas, and volumes from DXF/DWG construction drawings"
    layer = 3
    tags = ["domain", "construction", "drawing", "qto", "dxf", "quantities"]
    requires = []

    default_config = {
        "unit_scale": 1.0,       # multiplier if drawing units ≠ mm
        "area_layer_filter": [],  # empty = all layers
        "min_area_m2": 0.01,
    }

    ui_schema = {
        "input": {
            "type": "file",
            "accept": [".dxf", ".dwg"],
            "placeholder": "Upload DXF or DWG drawing...",
        },
        "output": {
            "type": "table",
            "fields": [
                {"name": "measurements", "type": "list", "label": "Linear Measurements"},
                {"name": "areas", "type": "list", "unit": "m²", "label": "Areas"},
                {"name": "volumes", "type": "list", "unit": "m³", "label": "Volumes"},
                {"name": "total_area_m2", "type": "number", "unit": "m²", "label": "Total Area"},
            ],
        },
        "quick_actions": [
            {"icon": "📐", "label": "Full QTO", "prompt": "Extract all quantities from this drawing"},
            {"icon": "📏", "label": "Measurements", "prompt": "List all linear measurements"},
            {"icon": "🔲", "label": "Floor Areas", "prompt": "Calculate floor areas by room"},
        ],
    }

    async def merge_drawings(self, input_data: Any, params: Dict = None) -> Dict:
        """Connect 2+ DXF drawings: extract metadata per sheet, find lines that
        continue across sheet boundaries.

        Inputs:
          input_data: {"file_paths": ["a.dxf", "b.dxf", ...]} OR list of paths
          params: {"angle_tol_rad": 0.05, "coord_tol_pct": 0.02}

        Returns sheets[] (per-drawing metadata + bbox + boundary line count)
        and pairings[] (cross-sheet line continuity matches sorted by
        confidence). Useful for stitching adjacent floor plans, verifying
        match-line alignment between disciplines, or detecting that a wall on
        sheet A-101 keeps going on sheet A-102.
        """
        params = params or {}
        if isinstance(input_data, list):
            file_paths = input_data
        elif isinstance(input_data, dict):
            file_paths = input_data.get("file_paths") or input_data.get("files") or []
        else:
            file_paths = []
        if isinstance(file_paths, dict):
            file_paths = list(file_paths.values())
        if not isinstance(file_paths, list) or len(file_paths) < 2:
            return {
                "status": "error",
                "error": "merge_drawings requires file_paths list with ≥2 DXF files",
            }

        try:
            import ezdxf  # noqa: F401
        except ImportError:
            return {"status": "error", "error": "ezdxf not installed. pip install ezdxf"}
        import ezdxf

        scale = float(params.get("unit_scale", self.config.get("unit_scale", 1.0)))
        angle_tol = float(params.get("angle_tol_rad", 0.05))
        coord_tol = float(params.get("coord_tol_pct", 0.02))

        # Parse each drawing — collect lines + bbox + sheet metadata
        sheets: List[Dict] = []
        for fp in file_paths:
            entry: Dict[str, Any] = {"file": os.path.basename(str(fp)), "path": str(fp)}
            if not os.path.exists(fp):
                entry.update({"status": "error", "error": "file not found"})
                sheets.append(entry)
                continue
            ext = os.path.splitext(fp)[1].lower()
            if ext != ".dxf":
                entry.update({"status": "error", "error": f"unsupported format {ext} (DXF only — convert DWG via ODA)"})
                sheets.append(entry)
                continue
            try:
                doc = ezdxf.readfile(fp)
            except Exception as e:
                entry.update({"status": "error", "error": f"DXF read error: {e}"})
                sheets.append(entry)
                continue

            msp = doc.modelspace()
            to_meters, units_code = _doc_units_to_meters(doc, scale)
            measurements = self._extract_measurements(msp, to_meters)
            line_endpoints: List[Tuple[float, float]] = []
            for m in measurements:
                if m.get("type") == "line":
                    s = m.get("start") or [0, 0]
                    e = m.get("end") or [0, 0]
                    line_endpoints.extend([(s[0], s[1]), (e[0], e[1])])
            bbox = _bbox(line_endpoints)
            boundary = _find_boundary_lines(measurements, bbox, tol_pct=coord_tol)
            metadata = _extract_sheet_metadata(doc)

            entry.update({
                "status": "success",
                "sheet_id": metadata.get("sheet_id"),
                "scale": metadata.get("scale_annotation"),
                "title": metadata.get("title_text"),
                "project": metadata.get("project_text"),
                "drawing_units": metadata.get("drawing_units"),
                "_units_code": units_code,
                "bbox": [round(c, 3) for c in bbox],
                "total_lines": sum(1 for m in measurements if m.get("type") == "line"),
                "boundary_lines": len(boundary),
                "_lines": measurements,
                "_boundary": boundary,
                "_bbox": bbox,
            })
            sheets.append(entry)

        # Cross-match every successful sheet pair. Skip pairings where the
        # two sheets disagree on units — they'd be at radically different
        # scales after normalisation anyway, and the user probably meant
        # to convert one of them first.
        pairings: List[Dict] = []
        unit_mismatches: List[Dict] = []
        successful = [s for s in sheets if s.get("status") == "success"]
        for i, sa in enumerate(successful):
            for sb in successful[i + 1:]:
                if sa.get("_units_code") != sb.get("_units_code"):
                    unit_mismatches.append({
                        "sheet_a": sa.get("sheet_id") or sa.get("file"),
                        "sheet_b": sb.get("sheet_id") or sb.get("file"),
                        "units_a": sa.get("drawing_units"),
                        "units_b": sb.get("drawing_units"),
                    })
                    continue
                pairs = _match_continuity(
                    sa["_boundary"], sa["_bbox"],
                    sb["_boundary"], sb["_bbox"],
                    angle_tol_rad=angle_tol,
                    coord_tol_pct=coord_tol,
                )
                if pairs:
                    pairings.append({
                        "sheet_a": sa.get("sheet_id") or sa.get("file"),
                        "sheet_b": sb.get("sheet_id") or sb.get("file"),
                        "match_count": len(pairs),
                        "top_confidence": pairs[0]["confidence"],
                        "edge_distribution": _summarise_edge_distribution(pairs),
                        "matches": pairs[:50],  # cap to keep response size bounded
                    })

        # Strip the heavy internal arrays before returning
        for s in sheets:
            for k in ("_lines", "_boundary", "_bbox", "_units_code"):
                s.pop(k, None)

        # Suggest a stitching order: pair sheets by their adjacency edges.
        stitching_suggestion: List[str] = []
        if pairings:
            top = max(pairings, key=lambda p: p["top_confidence"])
            stitching_suggestion.append(
                f"Strongest match: {top['sheet_a']} ↔ {top['sheet_b']} "
                f"({top['match_count']} aligned lines, confidence {top['top_confidence']:.2f})"
            )
            for p in pairings:
                if p is top:
                    continue
                stitching_suggestion.append(
                    f"  - {p['sheet_a']} ↔ {p['sheet_b']}: {p['match_count']} matches"
                )
        else:
            stitching_suggestion.append(
                "No line-continuity matches found — drawings may not share a match-line "
                "or may be at different scales/orientations."
            )

        return {
            "status": "success",
            "action": "merge_drawings",
            "sheets_processed": len(sheets),
            "sheets_successful": len(successful),
            "sheets": sheets,
            "pairings": pairings,
            "unit_mismatches": unit_mismatches,
            "total_matches": sum(p["match_count"] for p in pairings),
            "stitching_suggestion": stitching_suggestion,
            "tolerances_used": {"angle_rad": angle_tol, "coord_pct": coord_tol},
        }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        params = params or {}

        # Multi-drawing route: action=merge_drawings with file_paths list
        if (params.get("action") == "merge_drawings"
                or (isinstance(input_data, dict) and isinstance(input_data.get("file_paths"), list))):
            return await self.merge_drawings(input_data, params)

        file_path = self._resolve_file_path(input_data, params)

        # If no valid file path, try text-based quantity extraction
        if not file_path or not os.path.exists(file_path):
            text_input = self._extract_text_from_input(input_data, params)
            if text_input:
                return self._extract_quantities_from_text(text_input)
            if not file_path:
                return {"status": "error", "error": "No file_path provided. Requires a DXF or DWG file path, or text containing dimensions."}
            return {"status": "error", "error": f"File not found: {file_path}"}

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".dwg":
            return {
                "status": "error",
                "error": (
                    "DWG format requires ODA File Converter. "
                    "Convert to DXF first: https://www.opendesign.com/guestfiles/oda_file_converter"
                ),
            }
        if ext != ".dxf":
            return {"status": "error", "error": f"Unsupported format: {ext}. Use .dxf"}

        try:
            import ezdxf
        except ImportError:
            return {"status": "error", "error": "ezdxf not installed. Run: pip install ezdxf"}

        try:
            doc = ezdxf.readfile(file_path)
        except Exception as e:
            return {"status": "error", "error": f"DXF read error: {e}"}

        scale = float(params.get("unit_scale", self.config.get("unit_scale", 1.0)))
        layer_filter = params.get("area_layer_filter", self.config.get("area_layer_filter", []))
        min_area = float(params.get("min_area_m2", self.config.get("min_area_m2", 0.01)))

        msp = doc.modelspace()
        to_meters, _units_code = _doc_units_to_meters(doc, scale)
        measurements = self._extract_measurements(msp, to_meters)
        areas = self._extract_areas(msp, to_meters, layer_filter, min_area)
        volumes = self._estimate_volumes(areas, params)
        layers = list({e.dxf.layer for e in msp if hasattr(e.dxf, "layer")})

        total_area = sum(a["area_m2"] for a in areas)
        total_length = sum(m["length_m"] for m in measurements)

        return {
            "status": "success",
            "measurements": measurements,
            "areas": areas,
            "volumes": volumes,
            "total_area_m2": round(total_area, 3),
            "total_length_m": round(total_length, 3),
            "entity_count": len(list(msp)),
            "layers": layers[:50],
            "drawing_units": str(doc.units),
        }

    def _extract_text_from_input(self, input_data: Any, params: Dict) -> str:
        """Extract raw text from input when no file is provided."""
        if isinstance(input_data, str):
            return input_data
        if isinstance(input_data, dict):
            return (
                input_data.get("text", "") or
                input_data.get("content", "") or
                input_data.get("extracted_text", "") or
                ""
            )
        if isinstance(params, dict):
            return params.get("text", "") or params.get("content", "") or ""
        return ""

    def _extract_quantities_from_text(self, text: str) -> Dict:
        """Extract measurements and quantities from text descriptions."""
        import re
        t = text.lower()

        measurements = []
        areas = []
        volumes = []

        # Dimension patterns: 5.5m x 3.2m, 10' x 12', etc.
        dim_pat = re.compile(
            r'(\d+(?:\.\d+)?)\s*(?:m|m\.|meter|meters|ft|feet|foot|\')\s*(?:x|by|×)\s*(\d+(?:\.\d+)?)\s*(?:m|m\.|meter|meters|ft|feet|foot|\')',
            re.IGNORECASE
        )
        for m in dim_pat.finditer(t):
            w = float(m.group(1))
            h = float(m.group(2))
            unit = "m" if "m" in m.group(0).lower() else "ft"
            area_val = w * h
            measurements.append({
                "type": "dimension",
                "length_m": round((w + h) * 2, 3),
                "width": w,
                "height": h,
                "unit": unit,
                "raw": m.group(0),
            })
            areas.append({
                "type": "rectangular",
                "area_m2": round(area_val, 3) if unit == "m" else round(area_val * 0.092903, 3),
                "width": w,
                "height": h,
                "unit": unit,
                "source": "text_extraction",
            })

        # Single dimensions: 150mm, 5.5m, etc.
        single_pat = re.compile(r'\b(\d+(?:\.\d+)?)\s*(mm|cm|m|ft|in)\b', re.IGNORECASE)
        for m in single_pat.finditer(t):
            val = float(m.group(1))
            unit = m.group(2).lower()
            if unit == "mm":
                val_m = val / 1000.0
            elif unit == "cm":
                val_m = val / 100.0
            elif unit == "ft":
                val_m = val * 0.3048
            elif unit == "in":
                val_m = val * 0.0254
            else:
                val_m = val
            measurements.append({
                "type": "length",
                "length_m": round(val_m, 4),
                "unit": unit,
                "raw": m.group(0),
            })

        # Area patterns: 100m2, 500 sqm, etc.
        area_pat = re.compile(r'(\d+(?:\.\d+)?)\s*(?:m2|m²|sqm|sq\.?\s*m|sf|sq\.?\s*ft)', re.IGNORECASE)
        for m in area_pat.finditer(t):
            val = float(m.group(1))
            unit = "m2" if any(u in m.group(0).lower() for u in ["m2", "m²", "sqm", "sq m"]) else "ft2"
            area_m2 = val if unit == "m2" else val * 0.092903
            areas.append({
                "type": "area",
                "area_m2": round(area_m2, 3),
                "unit": unit,
                "source": "text_extraction",
            })

        # Volume patterns: 45m3, 100 cubic metres, etc.
        vol_pat = re.compile(r'(\d+(?:\.\d+)?)\s*(?:m3|m³|cbm|cu\.?\s*m|cubic\s*m)', re.IGNORECASE)
        for m in vol_pat.finditer(t):
            val = float(m.group(1))
            volumes.append({
                "type": "volume",
                "volume_m3": round(val, 3),
                "unit": "m3",
                "source": "text_extraction",
            })

        # Concrete / steel quantities from descriptive text
        concrete_pat = re.compile(r'concrete[^\n]*?(\d[\d,\.\s]*)\s*(?:m3|m³|cbm)', re.IGNORECASE)
        m = concrete_pat.search(t)
        if m:
            try:
                vol = float(m.group(1).replace(",", "").replace(" ", ""))
                volumes.append({"type": "concrete", "volume_m3": round(vol, 2), "unit": "m3", "source": "text_extraction"})
            except ValueError:
                pass

        steel_pat = re.compile(r'(?:steel|rebar|reinforcement)[^\n]*?(\d[\d,\.\s]*)\s*(?:kg|ton|tonne)', re.IGNORECASE)
        m = steel_pat.search(t)
        if m:
            try:
                weight = float(m.group(1).replace(",", "").replace(" ", ""))
                if "ton" in m.group(0).lower():
                    weight = weight * 1000
                measurements.append({"type": "steel_weight", "length_m": round(weight, 2), "unit": "kg", "source": "text_extraction"})
            except ValueError:
                pass

        total_area = sum(a["area_m2"] for a in areas)
        total_length = sum(m["length_m"] for m in measurements)

        # Estimate volumes from areas + thickness
        estimated_volumes = self._estimate_volumes(areas, {})

        return {
            "status": "success",
            "source": "text_extraction",
            "note": "No DXF/DWG file provided. Quantities extracted from text description.",
            "measurements": measurements,
            "areas": areas,
            "volumes": volumes + estimated_volumes,
            "total_area_m2": round(total_area, 3),
            "total_length_m": round(total_length, 3),
            "entity_count": 0,
            "layers": [],
            "drawing_units": "text",
        }

    def _resolve_file_path(self, input_data: Any, params: Dict) -> Optional[str]:
        """Resolve file path from input_data and params, writing bytes to temp if needed."""
        if isinstance(input_data, str):
            return input_data
        if isinstance(input_data, bytes):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as f:
                f.write(input_data)
                return f.name
        if isinstance(input_data, dict):
            file_bytes = input_data.get("file") or input_data.get("bytes")
            if isinstance(file_bytes, bytes):
                ext = ".dxf"
                for candidate in [".dxf", ".dwg"]:
                    if candidate in str(input_data.get("filename", "")).lower():
                        ext = candidate
                        break
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                    f.write(file_bytes)
                    return f.name
            return (
                input_data.get("file_path")
                or input_data.get("path")
                or input_data.get("text")
                or input_data.get("input")
            )
        if isinstance(params, dict):
            return params.get("file_path")
        return None

    def _extract_measurements(self, msp, to_meters: float) -> List[Dict]:
        """Extract linear measurements. `to_meters` is the multiplier from
        native drawing units → meters (already accounts for INSUNITS)."""
        results = []
        for entity in msp:
            etype = entity.dxftype()
            try:
                if etype == "LINE":
                    start = entity.dxf.start
                    end = entity.dxf.end
                    length = math.dist(
                        (start.x, start.y, start.z),
                        (end.x, end.y, end.z)
                    ) * to_meters
                    results.append({
                        "type": "line",
                        "length_m": round(length, 4),
                        "layer": entity.dxf.layer,
                        "start": [round(start.x * to_meters, 3), round(start.y * to_meters, 3)],
                        "end": [round(end.x * to_meters, 3), round(end.y * to_meters, 3)],
                    })
                elif etype == "CIRCLE":
                    radius = entity.dxf.radius * to_meters
                    circumference = 2 * math.pi * radius
                    results.append({
                        "type": "circle",
                        "radius_m": round(radius, 4),
                        "circumference_m": round(circumference, 4),
                        "length_m": round(circumference, 4),
                        "layer": entity.dxf.layer,
                    })
                elif etype == "ARC":
                    radius = entity.dxf.radius * to_meters
                    start_angle = math.radians(entity.dxf.start_angle)
                    end_angle = math.radians(entity.dxf.end_angle)
                    if end_angle < start_angle:
                        end_angle += 2 * math.pi
                    arc_length = radius * (end_angle - start_angle)
                    results.append({
                        "type": "arc",
                        "radius_m": round(radius, 4),
                        "arc_length_m": round(arc_length, 4),
                        "length_m": round(arc_length, 4),
                        "layer": entity.dxf.layer,
                    })
                elif etype in ("LWPOLYLINE", "POLYLINE"):
                    pts = list(entity.get_points() if etype == "LWPOLYLINE" else entity.points())
                    length = 0.0
                    for i in range(len(pts) - 1):
                        length += math.dist(
                            (pts[i][0], pts[i][1]),
                            (pts[i + 1][0], pts[i + 1][1])
                        )
                    if entity.is_closed and len(pts) > 1:
                        length += math.dist(
                            (pts[-1][0], pts[-1][1]),
                            (pts[0][0], pts[0][1])
                        )
                    length = length * to_meters
                    results.append({
                        "type": "polyline",
                        "length_m": round(length, 4),
                        "closed": entity.is_closed,
                        "vertex_count": len(pts),
                        "layer": entity.dxf.layer,
                    })
                elif etype == "DIMENSION":
                    if hasattr(entity.dxf, "actual_measurement"):
                        val = entity.dxf.actual_measurement * to_meters
                        results.append({
                            "type": "dimension",
                            "length_m": round(val, 4),
                            "layer": entity.dxf.layer,
                            "text": getattr(entity.dxf, "text", ""),
                        })
            except Exception:
                continue
        return results

    def _extract_areas(
        self, msp, to_meters: float, layer_filter: List[str], min_area: float
    ) -> List[Dict]:
        results = []
        try:
            from shapely.geometry import Polygon
            use_shapely = True
        except ImportError:
            use_shapely = False

        for entity in msp:
            etype = entity.dxftype()
            layer = getattr(entity.dxf, "layer", "0")
            if layer_filter and layer not in layer_filter:
                continue
            try:
                if etype == "CIRCLE":
                    r = entity.dxf.radius * to_meters
                    area = math.pi * r * r
                    if area >= min_area:
                        results.append({
                            "type": "circle",
                            "area_m2": round(area, 4),
                            "perimeter_m": round(2 * math.pi * r, 4),
                            "layer": layer,
                        })
                elif etype in ("LWPOLYLINE", "POLYLINE") and entity.is_closed:
                    pts = list(entity.get_points() if etype == "LWPOLYLINE" else entity.points())
                    coords = [(p[0] * to_meters, p[1] * to_meters) for p in pts]
                    if use_shapely and len(coords) >= 3:
                        poly = Polygon(coords)
                        area = poly.area
                        perim = poly.length
                    else:
                        area = abs(_shoelace(coords))
                        perim = sum(
                            math.dist(coords[i], coords[(i + 1) % len(coords)])
                            for i in range(len(coords))
                        )
                    if area >= min_area:
                        results.append({
                            "type": "polyline_area",
                            "area_m2": round(area, 4),
                            "perimeter_m": round(perim, 4),
                            "vertex_count": len(pts),
                            "layer": layer,
                        })
                elif etype == "HATCH":
                    if hasattr(entity, "paths"):
                        for path in entity.paths:
                            if hasattr(path, "vertices") and len(path.vertices) >= 3:
                                coords = [
                                    (v[0] * to_meters, v[1] * to_meters)
                                    for v in path.vertices
                                ]
                                area = abs(_shoelace(coords))
                                if area >= min_area:
                                    results.append({
                                        "type": "hatch_area",
                                        "area_m2": round(area, 4),
                                        "layer": layer,
                                    })
            except Exception:
                continue
        return sorted(results, key=lambda x: x["area_m2"], reverse=True)

    def _estimate_volumes(self, areas: List[Dict], params: Dict) -> List[Dict]:
        height = float(params.get("height_m", 3.0))  # default floor height 3m
        volumes = []
        for a in areas:
            if a["area_m2"] > 1.0:
                volumes.append({
                    "type": f"{a['type']}_volume",
                    "area_m2": a["area_m2"],
                    "height_m": height,
                    "volume_m3": round(a["area_m2"] * height, 4),
                    "layer": a.get("layer", ""),
                })
        return volumes


def _shoelace(coords: List[Tuple[float, float]]) -> float:
    n = len(coords)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    return area / 2.0


# ── Multi-drawing analysis (sheet matching + line continuity) ─────────────
# Used by the construction container's `merge_drawings` action. Detects
# when two drawings cover adjacent regions: line endpoints near the sheet
# boundary on drawing A that match line endpoints + direction on the
# corresponding edge of drawing B = a continuity candidate.

def _bbox(points: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    """Return (min_x, min_y, max_x, max_y) bounding box."""
    if not points:
        return (0.0, 0.0, 0.0, 0.0)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _classify_boundary_edge(
    point: Tuple[float, float],
    bbox: Tuple[float, float, float, float],
    tol_pct: float = 0.05,
) -> Optional[str]:
    """Return 'left'/'right'/'top'/'bottom' if point is within tol_pct of the
    matching edge of bbox; None if interior. Uses % of the bbox side length
    for tolerance so the same threshold works at any drawing scale."""
    min_x, min_y, max_x, max_y = bbox
    width = max_x - min_x or 1.0
    height = max_y - min_y or 1.0
    tol_x = width * tol_pct
    tol_y = height * tol_pct
    px, py = point
    edges = []
    if abs(px - min_x) <= tol_x:
        edges.append(("left", abs(px - min_x)))
    if abs(px - max_x) <= tol_x:
        edges.append(("right", abs(px - max_x)))
    if abs(py - min_y) <= tol_y:
        edges.append(("bottom", abs(py - min_y)))
    if abs(py - max_y) <= tol_y:
        edges.append(("top", abs(py - max_y)))
    if not edges:
        return None
    # Closest wins
    edges.sort(key=lambda e: e[1])
    return edges[0][0]


def _line_direction_angle(start: Tuple[float, float], end: Tuple[float, float]) -> float:
    """Return line direction in radians, normalised to [0, π) so that a
    line and its reverse get the same angle."""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    angle = math.atan2(dy, dx)
    if angle < 0:
        angle += math.pi
    if angle >= math.pi:
        angle -= math.pi
    return angle


def _find_boundary_lines(
    measurements: List[Dict],
    bbox: Tuple[float, float, float, float],
    tol_pct: float = 0.05,
) -> List[Dict]:
    """Filter the measurements list down to lines with at least one
    endpoint near the bbox edge — those are continuity candidates."""
    boundary: List[Dict] = []
    for m in measurements:
        if m.get("type") != "line":
            continue
        start = m.get("start") or [0, 0]
        end = m.get("end") or [0, 0]
        s_edge = _classify_boundary_edge((start[0], start[1]), bbox, tol_pct)
        e_edge = _classify_boundary_edge((end[0], end[1]), bbox, tol_pct)
        if s_edge or e_edge:
            boundary.append({
                **m,
                "start_edge": s_edge,
                "end_edge": e_edge,
                "angle_rad": round(_line_direction_angle(tuple(start[:2]), tuple(end[:2])), 4),
            })
    return boundary


_OPPOSITE_EDGE = {"left": "right", "right": "left", "top": "bottom", "bottom": "top"}


def _match_continuity(
    bdy_a: List[Dict],
    bbox_a: Tuple[float, float, float, float],
    bdy_b: List[Dict],
    bbox_b: Tuple[float, float, float, float],
    *,
    angle_tol_rad: float = 0.05,
    coord_tol_pct: float = 0.02,
) -> List[Dict]:
    """Pair lines across two drawings that look like the same physical line
    continuing across a match-line boundary.

    Algorithm:
      - Drawing A's right-edge candidates pair with Drawing B's left-edge.
        Top/bottom and other edge orientations work the same way.
      - Lines must share the same direction angle (mod π) within angle_tol.
      - The endpoint-coordinate perpendicular to the match edge must match
        within coord_tol_pct of bbox extent (e.g. for a right-left pairing,
        the y-coords of the endpoints must agree).

    Returns: list of pairings each with both line dicts + a confidence
    score derived from angle delta + coord delta.
    """
    pairs: List[Dict] = []
    # Average the two bboxes when computing perpendicular-coordinate
    # tolerance — sheets that share a match-line often differ in extent,
    # so locking the tolerance to bbox_a alone biased small-vs-large
    # pairings.
    width_avg = (((bbox_a[2] - bbox_a[0]) + (bbox_b[2] - bbox_b[0])) / 2) or 1.0
    height_avg = (((bbox_a[3] - bbox_a[1]) + (bbox_b[3] - bbox_b[1])) / 2) or 1.0

    for la in bdy_a:
        # The edge that touches the boundary
        edge_a = la.get("end_edge") or la.get("start_edge")
        if not edge_a:
            continue
        opp = _OPPOSITE_EDGE[edge_a]
        # Coordinate perpendicular to the match (the one we expect to align)
        if edge_a in ("left", "right"):
            tol_perp = height_avg * coord_tol_pct
            perp_a = (la.get("start") or [0, 0])[1] if la.get("start_edge") == edge_a else (la.get("end") or [0, 0])[1]
        else:
            tol_perp = width_avg * coord_tol_pct
            perp_a = (la.get("start") or [0, 0])[0] if la.get("start_edge") == edge_a else (la.get("end") or [0, 0])[0]

        for lb in bdy_b:
            edge_b = lb.get("start_edge") or lb.get("end_edge")
            if edge_b != opp:
                continue
            # Direction must match (lines are 'same' if angles within tol mod π)
            d_angle = abs((la.get("angle_rad", 0) - lb.get("angle_rad", 0)) % math.pi)
            d_angle = min(d_angle, math.pi - d_angle)
            if d_angle > angle_tol_rad:
                continue
            if edge_b in ("left", "right"):
                perp_b = (lb.get("start") or [0, 0])[1] if lb.get("start_edge") == edge_b else (lb.get("end") or [0, 0])[1]
            else:
                perp_b = (lb.get("start") or [0, 0])[0] if lb.get("start_edge") == edge_b else (lb.get("end") or [0, 0])[0]
            d_perp = abs(perp_a - perp_b)
            if d_perp > tol_perp:
                continue
            # Confidence: blend of angle delta + coord delta
            angle_score = max(0, 1 - d_angle / max(angle_tol_rad, 1e-6))
            perp_score = max(0, 1 - d_perp / max(tol_perp, 1e-6))
            confidence = round((angle_score * 0.4 + perp_score * 0.6), 3)
            pairs.append({
                "drawing_a_line": la,
                "drawing_b_line": lb,
                "edge": f"{edge_a}↔{opp}",
                "angle_delta_rad": round(d_angle, 4),
                "coord_delta": round(d_perp, 4),
                "confidence": confidence,
                "same_layer": la.get("layer") == lb.get("layer"),
            })
    pairs.sort(key=lambda p: -p["confidence"])
    return pairs


def _extract_sheet_metadata(doc) -> Dict:
    """Pull title-block hints from a DXF: sheet number, scale annotation,
    drawing units. Best-effort — DXF doesn't standardise title blocks so we
    look for common conventions (TEXT entities on TITLE_BLOCK / TITLE layer
    + scale strings like '1:50' or 'SCALE: 1/100')."""
    sheet_id = None
    scale_text = None
    project_text = None
    title_text = None
    msp = doc.modelspace()
    sheet_re = re.compile(r"\b([A-Z]{1,2}-?\d{2,4}[A-Z]?)\b")  # A-101, S101, M-201A
    scale_re = re.compile(r"\b(?:scale|esc\.?)\s*[:=]?\s*(1\s*[:/]\s*\d{1,4}|\d+/\d+|\d+\"\s*=\s*\d+'?)", re.IGNORECASE)
    for entity in msp:
        etype = entity.dxftype()
        if etype not in ("TEXT", "MTEXT"):
            continue
        try:
            text = entity.text if etype == "MTEXT" else entity.dxf.text
            text = str(text or "").strip()
            if not text:
                continue
            layer = (getattr(entity.dxf, "layer", "") or "").upper()
            if "TITLE" in layer or "TBLOCK" in layer or "BORDER" in layer:
                if not title_text:
                    title_text = text[:120]
            if not sheet_id:
                m = sheet_re.search(text)
                if m and len(m.group(1)) <= 10:
                    sheet_id = m.group(1)
            if not scale_text:
                m = scale_re.search(text)
                if m:
                    scale_text = m.group(1).strip()
            if not project_text and ("project" in text.lower() or "proyecto" in text.lower()):
                project_text = text[:120]
        except Exception:
            continue
    return {
        "sheet_id": sheet_id,
        "scale_annotation": scale_text,
        "project_text": project_text,
        "title_text": title_text,
        "drawing_units": str(doc.units) if hasattr(doc, "units") else None,
    }


def _summarise_edge_distribution(pairs: List[Dict]) -> Dict[str, int]:
    """Count which edge-orientations matched. Tells the user whether the
    drawings stitch primarily horizontally (left↔right) or vertically
    (top↔bottom)."""
    out: Dict[str, int] = {}
    for p in pairs:
        edge = p.get("edge", "?")
        out[edge] = out.get(edge, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))
