# Parked Blockers

- `python3 -m pytest tests/insurance` fails during pytest configuration because `pytest.ini` references `starlette.exceptions.StarletteDeprecationWarning`, which is not present in the installed Starlette version. Verification succeeded with `python3 -m pytest -o filterwarnings= tests/insurance`.
- `CEREBRUM_DOMAIN_KITS=insurance` registration logs pre-existing capability declaration warnings for `insurance` and `insurance_v2` because `block_registry/insurance/block.json` and `block_registry/insurance_v2/block.json` are absent. The new `channel_router`, `attrition_scorer`, and `incentive_targeting` blocks have declarations and load successfully.
