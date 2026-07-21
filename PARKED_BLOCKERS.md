# Parked Blockers

- Insurance kit v2 block signing is parked: `scripts/sign_block.py` exists, but
  no publisher private key is present (only `data/publishers/cerebrum_platform.pub`).
  New distribution block `signature` fields remain empty until a private key is
  provided. Do not invent a replacement platform key in-repo.
- `CEREBRUM_DOMAIN_KITS=insurance` capability declaration warnings for
  `insurance` / `insurance_v2`: **resolved** by adding
  `block_registry/insurance/block.json` and
  `block_registry/insurance_v2/block.json`.
- Starlette pytest filter: **resolved** in `pytest.ini` (use
  `ignore::DeprecationWarning:starlette`).
