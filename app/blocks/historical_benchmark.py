"""Historical Benchmark Block — RS Means-style unit cost lookups and market ranges."""

import json
import os
from typing import Any, Dict, List, Optional
from app.core.universal_base import UniversalBlock


class HistoricalBenchmarkBlock(UniversalBlock):
    name = "historical_benchmark"
    version = "1.0"
    description = "RS Means-style benchmark unit costs, cost ranges, and market data for construction items"
    layer = 2
    tags = ["construction", "cost", "benchmark", "rsmeans", "aec"]

    ui_schema = {
        "input": {
            "type": "object",
            "placeholder": "Pass item description + location for benchmark rates",
        },
        "params": {
            "fields": [
                {"name": "item", "type": "string", "label": "Item description"},
                {"name": "unit", "type": "string", "label": "Unit (m2, m3, kg, ea…)"},
                {"name": "location", "type": "string", "label": "Location / city"},
                {"name": "project_type", "type": "string", "label": "Project type"},
            ]
        },
    }

    default_config = {
        "rates_env": "BENCHMARK_RATES_PATH",
        "factors_env": "BENCHMARK_FACTORS_PATH",
    }

    def __init__(self, hal_block=None, config: Dict = None):
        super().__init__(hal_block, config)
        self._rates: Dict[str, Dict] = {}
        self._location_factors: Dict[str, float] = {}
        self._project_factors: Dict[str, float] = {}
        self._load_data()

    def _load_data(self):
        """Load benchmark data from external files or environment variables."""
        rates_path = os.environ.get(
            self.config.get("rates_env", "BENCHMARK_RATES_PATH"), ""
        )
        factors_path = os.environ.get(
            self.config.get("factors_env", "BENCHMARK_FACTORS_PATH"), ""
        )

        if rates_path and os.path.exists(rates_path):
            try:
                with open(rates_path, "r") as f:
                    self._rates = json.load(f)
            except Exception:
                pass

        if factors_path and os.path.exists(factors_path):
            try:
                with open(factors_path, "r") as f:
                    factors = json.load(f)
                    self._location_factors = factors.get("location_factors", {})
                    self._project_factors = factors.get("project_factors", {})
            except Exception:
                pass

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        params = params or {}
        data = input_data if isinstance(input_data, dict) else {}

        action = params.get("action", data.get("action", "lookup"))

        # Allow inline injection of benchmark data for real computation
        inline_rates = data.get("rates") or params.get("rates")
        inline_loc_factors = data.get("location_factors") or params.get("location_factors")
        inline_proj_factors = data.get("project_factors") or params.get("project_factors")

        if inline_rates:
            self._rates.update(inline_rates)
        if inline_loc_factors:
            self._location_factors.update(inline_loc_factors)
        if inline_proj_factors:
            self._project_factors.update(inline_proj_factors)

        if action == "lookup":
            return self._lookup(data, params)
        if action == "batch":
            return self._batch_lookup(data, params)
        if action == "location_factors":
            return {"status": "success", "location_factors": self._location_factors}
        if action == "catalogue":
            return self._get_catalogue(params)

        return self._lookup(data, params)

    def _lookup(self, data: Dict, params: Dict) -> Dict:
        item = params.get("item") or data.get("item") or data.get("description") or data.get("text") or data.get("input", "")
        unit = (params.get("unit") or data.get("unit", "")).lower()
        location = (params.get("location") or data.get("location", "us national average")).lower()
        project_type = (params.get("project_type") or data.get("project_type", "general_building")).lower()

        if not self._rates:
            return {
                "status": "error",
                "error": "No benchmark data loaded. Provide rates via inline params, environment variable, or file.",
            }

        loc_factor = self._get_location_factor(location)
        proj_factor = self._project_factors.get(project_type, 1.05)

        rate_key, rate_data = self._find_best_match(item, unit)

        if not rate_data:
            return {
                "status": "not_found",
                "item": item,
                "message": f"No benchmark found for '{item}' ({unit}). Check catalogue for available items.",
            }

        base = rate_data["base"]
        adjusted = round(base * loc_factor * proj_factor, 2)

        return {
            "status": "success",
            "item": item,
            "matched_key": rate_key,
            "unit": rate_data["unit"],
            "trade": rate_data["trade"],
            "rates": {
                "base_usd": base,
                "low_usd": round(rate_data["low"] * loc_factor * proj_factor, 2),
                "high_usd": round(rate_data["high"] * loc_factor * proj_factor, 2),
                "adjusted_usd": adjusted,
            },
            "factors": {
                "location": location,
                "location_factor": loc_factor,
                "project_type": project_type,
                "project_factor": proj_factor,
            },
            "confidence": "high" if rate_key in item.lower().replace(" ", "_") else "medium",
            "source": "external benchmark database",
        }

    def _batch_lookup(self, data: Dict, params: Dict) -> Dict:
        items: List[Dict] = params.get("items") or data.get("items") or []
        location = (params.get("location") or data.get("location", "us national average")).lower()
        project_type = (params.get("project_type") or data.get("project_type", "general_building")).lower()

        results = []
        total = 0.0
        for item in items:
            result = self._lookup(
                {**data, **item},
                {"location": location, "project_type": project_type,
                 "item": item.get("item", item.get("description", "")),
                 "unit": item.get("unit", "")},
            )
            qty = float(item.get("quantity", 1))
            if result.get("status") == "success":
                line_total = round(result["rates"]["adjusted_usd"] * qty, 2)
                result["quantity"] = qty
                result["line_total"] = line_total
                total += line_total
            results.append(result)

        return {
            "status": "success",
            "action": "batch_lookup",
            "items_requested": len(items),
            "items_matched": len([r for r in results if r.get("status") == "success"]),
            "total_cost_usd": round(total, 2),
            "results": results,
        }

    def _get_catalogue(self, params: Dict) -> Dict:
        trade_filter = params.get("trade", "").lower()
        items = []
        for key, data in self._rates.items():
            if trade_filter and trade_filter not in data["trade"].lower():
                continue
            items.append({
                "key": key,
                "unit": data["unit"],
                "trade": data["trade"],
                "base_rate_usd": data["base"],
                "range": f"{data['low']} – {data['high']}",
            })
        return {
            "status": "success",
            "action": "catalogue",
            "total_items": len(items),
            "items": items,
        }

    def _find_best_match(self, item: str, unit: str) -> tuple:
        n = item.lower()
        u = unit.lower()

        # Exact keyword matching in priority order
        if "curtain wall" in n or "curtain_wall" in n:
            return "curtain_wall_m2", self._rates.get("curtain_wall_m2")
        if "cladding" in n:
            return "cladding_m2", self._rates.get("cladding_m2")
        if "glazing" in n or "glass" in n:
            return "glazing_standard_m2", self._rates.get("glazing_standard_m2")
        if "lift" in n or "elevator" in n:
            return "lift_passenger_ea", self._rates.get("lift_passenger_ea")
        if "structural steel" in n or ("steel" in n and "kg" in u):
            return "structural_steel_kg", self._rates.get("structural_steel_kg")
        if "rebar" in n or "reinforcement" in n:
            return "rebar_kg", self._rates.get("rebar_kg")
        if "c40" in n or ("concrete" in n and "40" in n):
            return "concrete_c40_m3", self._rates.get("concrete_c40_m3")
        if "c30" in n or ("concrete" in n and "30" in n):
            return "concrete_c30_m3", self._rates.get("concrete_c30_m3")
        if "concrete" in n and "m3" in u:
            return "concrete_c25_m3", self._rates.get("concrete_c25_m3")
        if "soffit" in n or ("formwork" in n and "soffit" in n):
            return "formwork_soffit_m2", self._rates.get("formwork_soffit_m2")
        if "formwork" in n or "shuttering" in n:
            return "formwork_standard_m2", self._rates.get("formwork_standard_m2")
        if "pil" in n:
            return "piling_lm", self._rates.get("piling_lm")
        if "excavat" in n:
            return "excavation_m3", self._rates.get("excavation_m3")
        if "brick" in n:
            return "brickwork_m2", self._rates.get("brickwork_m2")
        if "block" in n and "m2" in u:
            return "blockwork_m2", self._rates.get("blockwork_m2")
        if "waterproof" in n or "membrane" in n:
            return "waterproofing_m2", self._rates.get("waterproofing_m2")
        if "roof" in n:
            return "roofing_flat_m2", self._rates.get("roofing_flat_m2")
        if "suspended ceiling" in n or "false ceiling" in n:
            return "suspended_ceiling_m2", self._rates.get("suspended_ceiling_m2")
        if "drylining" in n or "drywall" in n:
            return "drylining_m2", self._rates.get("drylining_m2")
        if "plaster" in n:
            return "plaster_m2", self._rates.get("plaster_m2")
        if "premium tile" in n or "marble" in n or "stone tile" in n:
            return "tiling_premium_m2", self._rates.get("tiling_premium_m2")
        if "tile" in n or "tiling" in n:
            return "tiling_standard_m2", self._rates.get("tiling_standard_m2")
        if "floor" in n and "screed" in n:
            return "flooring_screed_m2", self._rates.get("flooring_screed_m2")
        if "paint" in n:
            return "painting_m2", self._rates.get("painting_m2")
        if "insulation" in n:
            return "insulation_thermal_m2", self._rates.get("insulation_thermal_m2")
        if "hvac" in n or "mechanical" in n or "air" in n:
            return "hvac_medium_m2", self._rates.get("hvac_medium_m2")
        if "fire" in n and "protection" in n:
            return "fire_protection_m2", self._rates.get("fire_protection_m2")
        if "electrical" in n or "lighting" in n:
            return "electrical_standard_m2", self._rates.get("electrical_standard_m2")
        if "plumbing" in n or "sanitary" in n:
            return "plumbing_standard_m2", self._rates.get("plumbing_standard_m2")
        if "external door" in n:
            return "door_external_ea", self._rates.get("door_external_ea")
        if "door" in n:
            return "door_internal_ea", self._rates.get("door_internal_ea")
        if "window" in n:
            return "window_standard_ea", self._rates.get("window_standard_ea")
        if "scaffold" in n:
            return "scaffold_m2", self._rates.get("scaffold_m2")

        return "", None

    def _get_location_factor(self, location: str) -> float:
        loc = location.lower().strip()
        if loc in self._location_factors:
            return self._location_factors[loc]
        for key, factor in self._location_factors.items():
            if key in loc or loc in key:
                return factor
        return 1.0
