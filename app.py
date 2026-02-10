from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List

from flask import Flask, jsonify, redirect, render_template, request, url_for

from mssdppg.scenarios import DEFAULT_SCENARIO, INVESTOR_SCENARIOS, scenario_dict
from mssdppg.configurations import CONFIGS
from mssdppg.physics.dp2d import DPParams, simulate as simulate_2d
from mssdppg.physics.energy import downsample_frames
from mssdppg.wind.weibull import bin_probabilities
from mssdppg.wind.histogram import parse_histogram
from mssdppg.wind.presets import WEIBULL_PRESETS
from mssdppg.powercurve.builder import build_power_curve
from mssdppg.powercurve.cache import make_key, read_cache, write_cache
from mssdppg.economics.capex import total_capex
from mssdppg.economics.lcoe import lcoe_from_system, lcoe_table
from mssdppg.economics.land import land_metrics
from mssdppg.economics.aep import annual_energy_kwh
from mssdppg.economics.smoothing import smoothing_curve


def aep_from_bins(curve: List[List[float]], bins: List[tuple[float, float]]) -> float:
    power_by_speed = {float(speed): float(power) for speed, power in curve}
    total_kw = 0.0
    for speed, prob in bins:
        total_kw += power_by_speed.get(float(speed), 0.0) * float(prob)
    return total_kw * 8760.0


def _scenario_value(key: str) -> Any:
    if isinstance(DEFAULT_SCENARIO, dict):
        return DEFAULT_SCENARIO[key]
    return getattr(DEFAULT_SCENARIO, key)


def _resolve_config(payload: Dict[str, Any]) -> Dict[str, Any] | None:
    config_name = payload.get("config_name")
    if not config_name:
        return None
    return CONFIGS.get(str(config_name))


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index() -> str:
        return redirect(url_for("ui"))

    @app.route("/ui")
    def ui() -> str:
        return render_template("custom_ui.html")

    @app.get("/api/scenarios")
    def scenarios() -> Any:
        return jsonify(
            {
                "configs": CONFIGS,
                "default": scenario_dict(),
                "weibull_presets": WEIBULL_PRESETS,
                "investor_scenarios": INVESTOR_SCENARIOS,
            }
        )

    @app.post("/api/power_curve")
    def power_curve() -> Any:
        payload = request.get_json(force=True)
        speeds = payload.get("speeds") or list(range(0, 26))
        mode = payload.get("mode", "aero")
        aero_params = payload.get("aero_params", {})
        sim_inputs = payload.get("sim_params", {})
        cache_payload = {
            "speeds": speeds,
            "mode": mode,
            "aero_params": aero_params,
            "sim_params": sim_inputs,
        }
        key = make_key(cache_payload)
        cached = read_cache(key)
        if cached:
            return jsonify({"cache_key": key, "curve": cached["curve"], "cached": True})
        sim_params = DPParams(
            l1=sim_inputs.get("l1", _scenario_value("l1")),
            l2=sim_inputs.get("l2", _scenario_value("l2")),
            m_upper_arm=sim_inputs.get("m_upper_arm", _scenario_value("m_upper_arm")),
            m_middle=sim_inputs.get("m_middle", _scenario_value("m_middle")),
            m_lower_arm=sim_inputs.get("m_lower_arm", _scenario_value("m_lower_arm")),
            m_tip=sim_inputs.get("m_tip", _scenario_value("m_tip")),
            n_pendulums=int(sim_inputs.get("n_pendulums", _scenario_value("n_pendulums"))),
        )
        curve = build_power_curve(speeds, mode, aero_params, sim_params)
        write_cache(key, {"curve": curve})
        return jsonify({"cache_key": key, "curve": curve, "cached": False})

    @app.post("/api/aep")
    def aep() -> Any:
        payload = request.get_json(force=True)
        config = _resolve_config(payload)
        if config:
            modules_count = int(payload.get("modules_count", 1))
            capacity_factor = float(payload.get("capacity_factor", 0.30))
            per_module_aep_kwh = annual_energy_kwh(config["expected_power"], capacity_factor)
            return jsonify(
                {
                    "aep_kwh": per_module_aep_kwh * modules_count,
                    "per_module_aep_kwh": per_module_aep_kwh,
                }
            )

        curve = payload.get("curve", [])
        wind_mode = payload.get("wind_mode", "weibull")
        if wind_mode == "histogram":
            histogram = payload.get("histogram", [])
            bins = [(float(v), float(p)) for v, p in histogram]
        else:
            k = float(payload.get("weibull_k", _scenario_value("weibull_k")))
            c = float(payload.get("weibull_c", _scenario_value("weibull_c")))
            speeds = [v for v, _ in curve]
            bins = bin_probabilities(speeds, k, c)
        aep_kwh = aep_from_bins(curve, bins)
        return jsonify({"aep_kwh": aep_kwh, "per_module_aep_kwh": aep_kwh, "bins": bins})

    @app.post("/api/lcoe")
    def lcoe() -> Any:
        payload = request.get_json(force=True)
        config = _resolve_config(payload)

        if config:
            modules_count = int(payload.get("modules_count", 1))
            capacity_factor = float(payload.get("capacity_factor", 0.30))
            project_life_years = int(payload.get("project_life_years", 20))
            wacc_pct = float(payload.get("wacc_pct", 8.0))
            fixed_om = float(payload.get("fixed_om_usd_per_year", 0.0))
            variable_om = float(payload.get("variable_om_usd_per_kwh", 0.0))
            system_cost_usd = float(config["cost"]) * modules_count
            aep_kwh = annual_energy_kwh(config["expected_power"], capacity_factor) * modules_count
            base_table = lcoe_from_system(
                system_cost_usd=system_cost_usd,
                aep_kwh=aep_kwh,
                project_life_years=project_life_years,
                wacc_pct=wacc_pct,
                fixed_om_usd_per_year=fixed_om,
                variable_om_usd_per_kwh=variable_om,
            )
            investor_rows = []
            for scenario in INVESTOR_SCENARIOS:
                multiplier = float(scenario.get("multiplier", scenario.get("capex_multiplier", 1.0)))
                row = lcoe_from_system(
                    system_cost_usd=system_cost_usd * multiplier,
                    aep_kwh=aep_kwh,
                    project_life_years=project_life_years,
                    wacc_pct=float(scenario.get("wacc_pct", wacc_pct)),
                    fixed_om_usd_per_year=fixed_om,
                    variable_om_usd_per_kwh=variable_om,
                )
                row["name"] = scenario["name"]
                investor_rows.append(row)
            return jsonify(
                {
                    "lcoe": base_table,
                    "investor_scenarios": investor_rows,
                    "capex_total_usd": base_table["capex_total_usd"],
                    "annualized_capex_usd": base_table["annualized_capex_usd"],
                    "annual_om_usd": base_table["annual_om_usd"],
                    "aep_kwh": base_table["aep_kwh"],
                }
            )

        base_table = lcoe_table(payload)
        investor_rows = []
        for scenario in INVESTOR_SCENARIOS:
            inputs = dict(payload)
            multiplier = float(scenario.get("multiplier", scenario.get("capex_multiplier", 1.0)))
            inputs["wacc_pct"] = float(scenario.get("wacc_pct", payload.get("wacc_pct", 8.0)))
            if "system_cost_usd" in inputs:
                inputs["system_cost_usd"] = float(inputs.get("system_cost_usd", 0.0)) * multiplier
            else:
                inputs["mechanical_usd"] = inputs.get("mechanical_usd", 0.0) * multiplier
                inputs["electrical_usd"] = inputs.get("electrical_usd", 0.0) * multiplier
                inputs["civil_bos_usd"] = inputs.get("civil_bos_usd", 0.0) * multiplier
                inputs["soft_costs_usd"] = inputs.get("soft_costs_usd", 0.0) * multiplier
            land_cost = float(scenario.get("land_cost_usd_per_m2", 0.0)) * payload.get("land_area_m2", 0.0)
            if "system_cost_usd" in inputs:
                inputs["system_cost_usd"] = float(inputs.get("system_cost_usd", 0.0)) + land_cost
            else:
                inputs["mechanical_usd"] = inputs.get("mechanical_usd", 0.0) + land_cost
            row = lcoe_table(inputs)
            row["name"] = scenario["name"]
            investor_rows.append(row)
        return jsonify(
            {
                "lcoe": base_table,
                "investor_scenarios": investor_rows,
                "capex_total_usd": base_table.get("capex_total_usd", 0.0),
                "annualized_capex_usd": base_table.get("annualized_capex_usd", 0.0),
                "annual_om_usd": base_table.get("annual_om_usd", 0.0),
                "aep_kwh": base_table.get("aep_kwh", 0.0),
            }
        )

    @app.post("/api/site_rollup")
    def site_rollup() -> Any:
        payload = request.get_json(force=True)
        modules_count = int(payload.get("modules_count", 1))
        config = _resolve_config(payload)

        if config:
            capacity_factor = float(payload.get("capacity_factor", 0.30))
            land_cost_usd_per_m2 = float(payload.get("land_cost_usd_per_m2", 3.0))
            project_life_years = int(payload.get("project_life_years", 20))
            wacc_pct = float(payload.get("wacc_pct", 8.0))
            fixed_om = float(payload.get("fixed_om_usd_per_year", 0.0))
            variable_om = float(payload.get("variable_om_usd_per_kwh", 0.0))

            module_area_m2 = float(config.get("module_area_m2", payload.get("module_area_m2", 57.6)))
            land = land_metrics(
                modules_count=modules_count,
                module_area_m2=module_area_m2,
                land_cost_usd_per_m2=land_cost_usd_per_m2,
            )
            system_capex_usd = total_capex(float(config["cost"])) * modules_count
            total_capex_usd = system_capex_usd + land["land_cost_usd"]
            per_module_aep_kwh = annual_energy_kwh(float(config["expected_power"]), capacity_factor)
            total_aep_kwh = per_module_aep_kwh * modules_count
            total_avg_kw = total_aep_kwh / 8760.0 if total_aep_kwh else 0.0
            lcoe_output = lcoe_from_system(
                system_cost_usd=total_capex_usd,
                aep_kwh=total_aep_kwh,
                project_life_years=project_life_years,
                wacc_pct=wacc_pct,
                fixed_om_usd_per_year=fixed_om,
                variable_om_usd_per_kwh=variable_om,
            )
            return jsonify(
                {
                    "total_capex_usd": total_capex_usd,
                    "total_aep_kwh": total_aep_kwh,
                    "total_avg_kw": total_avg_kw,
                    "land_area_m2": land["land_area_m2"],
                    "land_area_ha": land["land_area_ha"],
                    "land_cost_usd": land["land_cost_usd"],
                    "lcoe": lcoe_output,
                }
            )

        module_aep_kwh = float(payload.get("module_aep_kwh", 0.0))
        module_avg_kw = module_aep_kwh / 8760 if module_aep_kwh else 0.0
        module_area_m2 = float(payload.get("module_area_m2", 57.6))
        land_cost_usd_per_m2 = float(payload.get("land_cost_usd_per_m2", 3.0))
        land = land_metrics(
            modules_count=modules_count,
            module_area_m2=module_area_m2,
            land_cost_usd_per_m2=land_cost_usd_per_m2,
        )
        system_cost_usd = float(payload.get("system_cost_usd", 0.0))
        if system_cost_usd <= 0.0:
            capex_inputs = payload.get("capex_inputs", {})
            contingency_pct = float(capex_inputs.get("contingency_pct", 0.0))
            direct_cost = (
                float(capex_inputs.get("mechanical_usd", 0.0))
                + float(capex_inputs.get("electrical_usd", 0.0))
                + float(capex_inputs.get("civil_bos_usd", 0.0))
                + float(capex_inputs.get("soft_costs_usd", 0.0))
            )
            system_cost_usd = direct_cost * (1.0 + contingency_pct / 100.0)
        capex_total = total_capex(system_cost_usd) * modules_count + land["land_cost_usd"]
        total_aep_kwh = module_aep_kwh * modules_count
        total_avg_kw = module_avg_kw * modules_count
        lcoe_output = lcoe_from_system(
            system_cost_usd=capex_total,
            aep_kwh=total_aep_kwh,
            project_life_years=int(payload.get("project_life_years", 20)),
            wacc_pct=float(payload.get("wacc_pct", 8.0)),
            fixed_om_usd_per_year=float(payload.get("fixed_om_usd_per_year", 0.0)),
            variable_om_usd_per_kwh=float(payload.get("variable_om_usd_per_kwh", 0.0)),
        )
        return jsonify(
            {
                "total_capex_usd": capex_total,
                "total_aep_kwh": total_aep_kwh,
                "total_avg_kw": total_avg_kw,
                "land_area_m2": land["land_area_m2"],
                "land_area_ha": land["land_area_ha"],
                "land_cost_usd": land["land_cost_usd"],
                "lcoe": lcoe_output,
            }
        )

    @app.post("/api/simulate")
    def simulate() -> Any:
        payload = request.get_json(force=True)
        wind_speed = float(payload.get("wind_speed", 8.0))
        params = DPParams(
            l1=payload.get("l1", _scenario_value("l1")),
            l2=payload.get("l2", _scenario_value("l2")),
            m_upper_arm=payload.get("m_upper_arm", _scenario_value("m_upper_arm")),
            m_middle=payload.get("m_middle", _scenario_value("m_middle")),
            m_lower_arm=payload.get("m_lower_arm", _scenario_value("m_lower_arm")),
            m_tip=payload.get("m_tip", _scenario_value("m_tip")),
            n_pendulums=int(payload.get("n_pendulums", _scenario_value("n_pendulums"))),
        )
        frames = simulate_2d(wind_speed, params, duration_s=payload.get("duration_s", 20.0))
        frames = downsample_frames(frames, step=payload.get("downsample", 5))
        return jsonify({"frames": frames})

    @app.post("/api/smoothing")
    def smoothing() -> Any:
        payload = request.get_json(force=True)
        curve = smoothing_curve(
            modules=int(payload.get("number_of_modules", 4)),
            phase_offset_deg=float(payload.get("phase_offset_deg", 30.0)),
            inverter_rating_kw=float(payload.get("inverter_rating_kw", 250.0)),
            base_power_kw=float(payload.get("base_power_kw", 120.0)),
        )
        return jsonify(curve)

    @app.post("/api/histogram_parse")
    def histogram_parse() -> Any:
        payload = request.get_json(force=True)
        parsed = parse_histogram(payload.get("csv_text", ""))
        return jsonify({"histogram": parsed})

    return app


def cli() -> None:
    parser = argparse.ArgumentParser(description="MSSDPPG Live Simulator CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scenarios")
    lcoe_cmd = sub.add_parser("lcoe")
    lcoe_cmd.add_argument("--aep-kwh", type=float, default=1500000)
    lcoe_cmd.add_argument("--capex", type=float, default=1200000)
    args = parser.parse_args()
    if args.command == "scenarios":
        print(json.dumps(scenario_dict(), indent=2))
        return
    if args.command == "lcoe":
        table = lcoe_table(
            {
                "mechanical_usd": args.capex,
                "electrical_usd": 0.0,
                "civil_bos_usd": 0.0,
                "soft_costs_usd": 0.0,
                "contingency_pct": 0.0,
                "aep_kwh": args.aep_kwh,
                "project_life_years": 20,
                "wacc_pct": 8.0,
                "fixed_om_usd_per_year": 0.0,
                "variable_om_usd_per_kwh": 0.0,
            }
        )
        print(json.dumps(table, indent=2))


app = create_app()


if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] in {"scenarios", "lcoe"}:
        cli()
    else:
        port = int(os.environ.get("PORT", "5000"))
        app.run(host="0.0.0.0", port=port, debug=True)
