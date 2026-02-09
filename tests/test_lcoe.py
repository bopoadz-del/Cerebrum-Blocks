from mssdppg.economics.lcoe import lcoe_table


def test_lcoe_table_outputs():
    result = lcoe_table(
        {
            "mechanical_usd": 1000000.0,
            "electrical_usd": 200000.0,
            "civil_bos_usd": 100000.0,
            "soft_costs_usd": 50000.0,
            "contingency_pct": 5.0,
            "aep_kwh": 1500000.0,
            "project_life_years": 20,
            "wacc_pct": 8.0,
            "fixed_om_usd_per_year": 10000.0,
            "variable_om_usd_per_kwh": 0.01,
        }
    )
    assert result["capex_total_usd"] > 0
    assert result["lcoe_usd_per_kwh"] > 0
