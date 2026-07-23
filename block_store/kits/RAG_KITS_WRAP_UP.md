# RAG Kits Wrap-Up — Completed

## Mission
Audit downloaded datasets, classify them, reject unsuitable ones, index approved RAW_RAG corpora, build kits, update store inventory, and wrap up.

## Final status
- **Rejected kits deleted**: Yes
- **Approved RAW_RAG kits indexed**: 8 collections
- **Approved evaluation kits registered**: 2 kits
- **Store inventory updated**: `indexed_rag_collections.json`, `eval_packs.json`; `rag_packs.json` kept metadata-only per store standards
- **Verification**: All indexed kits have `kernel_manifest.json`, `<kit>_indexed.json`, `vector_store.pkl`, and `<kit>_verification.json`. Small kits were load-verified against chunk counts.

## Indexed RAW_RAG collections

| Kit | Project ID | Domain | Chunks indexed | Vector store | Verification |
|---|---|---|---|---|---|
| confusable_pharma_benchmark | prebuilt_pharma_core | pharma | 7,123 | Yes | Yes |
| danragbench_benchmark | prebuilt_danish_public_sector_core | danish_public_sector | 349 | Yes | Yes |
| obliqa_mp_benchmark | prebuilt_legal_adgm_core | legal | 1,419 | Yes | Yes |
| parsebench_benchmark | prebuilt_document_parsing_core | document_parsing | 168,943 | Yes | Yes |
| recor_benchmark | prebuilt_multi_domain_qa_core | multi-domain | 507,141 | Yes | Yes |
| t2ragbench_benchmark | prebuilt_finance_sec_core | finance | 23,088 | Yes | Yes |
| enterpriserag_benchmark | prebuilt_enterprise_rag_core | enterprise_rag | 350,000* | Yes | Yes |
| mtrag_benchmark | prebuilt_universal_multiturn_core | universal | 366,479 | Yes | Yes |

**Total indexed chunks:** 1,424,542

\* EnterpriseRAG was capped at **350,000 chunks** from 511,963 synthetic documents because a single in-memory `VectorStore` process exceeds available RAM beyond ~430,000 chunks. The cap is deterministic and preserves all source types. To index the full corpus, shard by `source_type` or move to a persisted vector backend.

## Approved evaluation kits (not indexed as RAG)

| Kit | Domain | Role | Records | Licence | Notes |
|---|---|---|---|---|---|
| aec_benchmark | construction | REASONING_EVAL / PRODUCT_WORKFLOW_TEST / VISION_DATA | 196 tasks | Apache-2.0 harness; document rights unclear | Task harness only; external PDFs excluded |
| techmanualqa700_benchmark | technical_manuals | RETRIEVAL_EVAL / REASONING_EVAL | 700 QA pairs | CC-BY-4.0 | Source PDFs not included; must be obtained separately |

## Rejected and deleted

| Kit | Reason |
|---|---|
| finder_benchmark | CC-BY-NC-4.0 commercial use prohibited |
| finmragbench_benchmark | Dataset not released ("coming soon") |
| garage_benchmark | CC-BY-NC-4.0 + unclear redistribution |
| construction_code_clause_benchmark | Dataset assets excluded by .gitignore |
| lofin_benchmark | CC-BY-NC-ND-4.0 + 95% duplicates |
| bioasq_benchmark | Registration-gated download |

## Key files created / updated

- `block_store/kits/index_one_kit.py` — single-kit indexer with in-memory verification and `max_chunks` guard
- `block_store/kits/index_approved_rags_summary.json` — canonical index summary
- `block_store/kits/build_kits.py` — manifest and `rag_packs.json` builder
- `block_store/shelves/rag_packs.json` — indexed RAG pack shelf
- `block_store/shelves/indexed_rag_collections.json` — operational indexed collection inventory
- `block_store/shelves/eval_packs.json` — evaluation kit shelf
- `block_store/kits/<kit>/kernel_manifest.json` — per-kit manifest
- `block_store/kits/<kit>/<kit>_indexed.json` — per-kit index record
- `block_store/kits/<kit>/<kit>_verification.json` — per-kit retrieval verification
- `block_store/kits/<kit>/vector_store.pkl` — per-kit VectorStore pickle

## Indexing method

```text
VectorStore.upsert(tenant_id, project_id, chunks)
hybrid_search(store, tenant_id, project_id, query, query_vector, top_k)
```

Embedding provider: fast deterministic hash fallback (`mmh3 + numpy`, 384-dim) for bulk offline indexing. Swap to a semantic embedding model for production retrieval.

## Notes

- Domain-specific names, brands, cities and manual references were kept as-is because they are the value of the corpora.
- Large vector-store pickles (>600 MB) were not reloaded during final verification to avoid memory pressure; their chunk counts are derived from the in-memory indexing run and matched the live `store.count()` before pickling.
- `rag_packs.json` remains metadata-only (`status: "metadata_only"`, `ingestion_status.state: "not_ingested"`) per store standards.
- `indexed_rag_collections.json` is the operational inventory for the 8 indexed collections.
- `app/core/indexed_rag_collections.py` provides a typed loader/validator for the indexed shelf.
- Ready for commit and PR.
