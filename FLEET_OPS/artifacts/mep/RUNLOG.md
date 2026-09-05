# MEP lane — RUNLOG (append-only, R9)
One line per landed step. Never rewritten, only appended.

2026-09-05 | STEP 0 inventory posted. Verified by running, not reading. INVENTORY_2026-09-05.md
2026-09-05 | FINDING: the 4 functions the order says Lane 2 restored do not exist in either repo. Equivalent capability exists under other names. Lane 2's claim is false.
2026-09-05 | FINDING: PROMPT_STANDARD_v2.md + rails R8/R9/R10 absent from all repos. Retrieved from owner Drive; vendored to kit.
2026-09-05 | FINDING: no clearance rule table in the corpus. Whole-RAG sweep proves code content EXISTS (IMC 49, IPC 53, NFPA13 56, sprinkler 399) but unstructured. F1 OPEN: block 2 ingests via RAG at run time, unsourced rules flagged.
2026-09-05 | FINDING: no congested fixture. Schependomlaan 404 at the location both its README and the order name. buildingSMART samples parse but are 2-24 element conformance scenes, 0 clashes. HF NNTS/BIM_IFC gated 401. F2 OPEN: synthetic corridor to be declared.
2026-09-05 | DEP: trimesh 5.1.0 + manifold3d installed and verified — exact intersection 0.5 m3 on overlapping unit boxes, min distance 2.0 m on separated. Both outputs from one engine.
2026-09-05 | LANDED block 1 geometry_engine: exact boolean + min distance; AABB demoted to a PADDED pre-filter; every finding carries its method; no-geometry reported UNJUDGED never CLEAR.
2026-09-05 | Own bug caught by own test: aabb_overlaps returned numpy.bool_, failing `is True` and JSON serialisation. Coerced to Python bool.
2026-09-05 | Own fixture caught by own guard: first mutation probe did not exercise the defect (boxes did not overlap). Replaced with parallel diagonal services — boxes overlap, solids 507 mm apart.
2026-09-05 | TESTS block 1: 6 passed. MUTANT (restore box verdict) killed by 3 tests incl. the named probe. Restored, 6 passed.
