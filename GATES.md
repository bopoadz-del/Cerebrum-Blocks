# GATES.md — Platform Build Gates

The gate checklist every platform build must pass before it is pushed,
and the improvement loop that runs after every build.

**Owner**: Codewhale + the platform owner.
**Use**: read before starting a build; check every gate before shipping;
after the run, update this file with every new failure mode found, and
update the Cerebrum-Blocks store blocks/patterns that would have
prevented it.

---

## G0 — Grounding (store-first)

- [ ] Pin the Cerebrum-Blocks commit; vendor the kit into `blocks/vendor/store` **byte-exact**.
- [ ] Generate `VENDOR.lock` (per-file sha256) with `__pycache__` excluded; `.gitattributes -text` on the vendored tree so hashes match on every OS.
- [ ] CI fails on any in-place edit under the vendored tree (`scripts/check_vendor_lock.py`).
- [ ] Kit provenance (commit, kit manifest version) recorded in `VENDOR_BLOCKS.md`.

## G1 — Domain truth

- [ ] Every surfaced answer carries its `evidence_class` + `source`. Class B (expert recall) is never presented as Class A.
- [ ] Verdicts are three-valued (PASS / FAIL / UNPROVABLE) — never bare booleans.
- [ ] Constraints are **computed, not hardcoded** (critical path, pacing constraint, cascade) — the test proves a graph change moves the answer.
- [ ] Refusal-class responses exist for the known traps: generic PPM tables, unsupported markets, construction-PM sources, raw media past the edge.

## G2 — Security

- [ ] Fail-closed auth on **every** route: reviewer (read) / operator (mutate); only `/health` is anonymous.
- [ ] Constant-time token compare (`hmac.compare_digest`), never `==`.
- [ ] CORS is an explicit allowlist; production never defaults to `*`.
- [ ] Audit journal is append-only and stores digests, never secrets or plaintext payloads.
- [ ] No secrets in the repo; `.env.example` + `secrets_guide.md` only.

## G3 — Honesty

- [ ] No fabricated data: connectors without a live system declare `mock_unavailable` and fail closed.
- [ ] Normalisers are real, tested code even when the adapter is a mock.
- [ ] Every placeholder is named, self-documenting, and off the critical path (`KNOWN_LIMITATIONS.md`).
- [ ] Agents are deterministic-first; LLM output (OpenRouter) is keyed-optional and never silently replaces grounded answers.

## G4 — Tests

- [ ] Unit tests cover every reasoning rule, the cascade/slip math, and the three-valued logic.
- [ ] API tests include a per-route 401 matrix and role separation (reviewer cannot mutate).
- [ ] Mutation probes: each probe breaks one safety property; **all must go red** (`tests/mutation_probes.py`).
- [ ] CI runs: pytest + vendor lock check + mutation probes. Red CI blocks the merge.

## G5 — Retrieval

- [ ] Uploaded documents are actually indexed and retrievable (round-trip test), with citations.
- [ ] Uploaded docs carry `A_sourced_document`; domain-sheet chunks carry Class B — never conflated.
- [ ] If embeddings are used: embedding fingerprint guard (model + dim mismatch refuses).

## G6 — Deployment

- [ ] docker-compose (sovereign profile) + secrets guide + Jetson/edge contract (metadata only).
- [ ] Vision/edge: raw media fails closed at the boundary (tested).
- [ ] Render fallback is optional and labelled non-sovereign.

## G7 — Delivery

- [ ] CI green on push (the only gate that counts at handoff).
- [ ] README states markets, honesty posture, and how to run; ACCEPTANCE lists criteria with the proving test; RUNLOG records findings.
- [ ] Every new verdict/refusal is a named reason string.

---

## Post-run improvement loop (runs every build)

1. **Gates**: every failure found this run that a gate would have caught is added here.
2. **Store**: the block/pattern that would have prevented it is updated in Cerebrum-Blocks (kit manifest, block docs, shared runtime), with a new pinned commit.
3. **Product**: the product repo re-vendors at the new commit and regenerates its lock.

### Run history (latest first)

- **2026-09-14 — HotelOps v2 fresh build**: found that a fresh scaffold can lose to a mature first PR on security — added G2 per-route 401 matrix + `compare_digest` + CORS allowlist; G5 wired document ingestion (A-class citations) because decorative "uploaded docs" is a tie-breaker loser.
