# Known Limitations — Cerebrum-Blocks

Leading with the worst honest number, per house standard.

## The worst number first

**Blind retrieval hit@5 is 0.25 (3/12).** When questions are written by
someone who has never seen the corpus (evals/blind_construction_eval.json,
authored blind and committed before the runner existed), the construction
knowledge base returns a fully relevant entry in the top 5 only one time in
four. Corpus-sighted (golden) queries score 1.00 (47/47) — the gap is the
honest measure of coverage: 47 entries do not cover a domain. Reproduce with
`python scripts/run_retrieval_eval.py`.

## Retrieval and embeddings

- The `zvec` semantic path requires the model2vec model to be downloadable at
  first use. Without it, zvec falls back to TF-IDF, and single-text TF-IDF
  vectors are **not comparable across calls** — the planted-truth tests fail
  in offline environments for exactly this reason. Do not score retrieval
  quality on the fallback.
- The vector-index adapters are validation-only by design: no production ANN
  index, no similarity search at scale.
- The aviation RAG pack references a source corpus
  (`block_store/kits/aviation_faa_core_rag/`) that is not present in a fresh
  clone; its corpus test fails until the corpus is fetched.

## Signing and provenance

- **Block signing is not operating.** Ed25519 signing code exists
  (`scripts/sign_block.py`, `app/core/block_validation.py`) but no publisher
  private key is present and kit signature fields are empty (0 of 19 domain
  kits signed) — see `PARKED_BLOCKERS.md`. Kit installs verify sha256
  `provenance.json` manifests **when present**; kits without one install
  labeled `absent — unverified`.

## Grounding coverage

- The mandatory grounding stage covers the answer-producing paths: `chat`
  and `knowledge` on `/v1/execute`, and `aviation_chat_server` end to end.
  Other blocks' outputs are schema-validated (fail-closed) but not
  grounding-verified.
- The grounding checks are lexical (URLs and figures traced to sources).
  They catch invented links and uncited numbers; they do not catch fluent
  prose that is wrong without containing a checkable claim.

## Execution environment

- The Kimi workbench block requires an external Kimi CLI binary; `/health`
  reports `cli_ok: false` where none is installed (most deployments today).
- Blocks with elevated capabilities need the out-of-process sandbox runner
  service; without it they return 503 rather than running unsafely.

## Test suite

Five failures are known and pre-date the free-trial hardening, reproduced on
a clean tree: planted-truth ×2 (offline embedder, above), the aviation
corpus test (corpus absent, above), a block-validation line-endings case,
and the cache_manager e2e (requires Redis). Everything else is green:
785 passed at the time of writing.
