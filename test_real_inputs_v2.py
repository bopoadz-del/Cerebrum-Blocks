#!/usr/bin/env python3
import asyncio, sys
sys.path.insert(0, '.')
from app.blocks import BLOCK_REGISTRY

TEST_INPUTS = {
    "chat":       {"input": {"message": "What is concrete curing time?"}, "params": {}},
    "pdf":        {"input": {"file_path": "/tmp/test.pdf", "text": "Sample content"}, "params": {"action": "extract_text"}},
    "pdf_v2":     {"input": {"text": "Sample content"}, "params": {"action": "extract_text"}},
    "ocr":        {"input": {"file_path": "/tmp/test.png", "text": "Sample text"}, "params": {"action": "extract"}},
    "ocr_v2":     {"input": {"text": "Sample text"}, "params": {"action": "extract"}},
    "image":      {"input": {"prompt": "construction site"}, "params": {}},
    "document_engine": {"input": {"text": "Building specs"}, "params": {"action": "process"}},
    "translate":  {"input": {"text": "Hello", "target": "ar"}, "params": {}},
    "voice":      {"input": {"text": "Safety reminder"}, "params": {"action": "tts"}},
    "web":        {"input": {"url": "https://example.com"}, "params": {"action": "scrape"}},
    "construction": {"input": {"text": "Area: 1500 m2. Concrete: 300 m3."}, "params": {"action": "auto_pipeline"}},
    "construction_v2": {"input": {"text": "Area: 1500 m2. Concrete: 300 m3."}, "params": {"action": "auto_pipeline"}},
    "boq_processor": {"input": {"text": "Concrete 300 m3"}, "params": {"action": "process_boq"}},
    "bim":        {"input": {"text": "IFC data"}, "params": {"action": "status"}},
    "bim_extractor": {"input": {"file_path": "/tmp/test.ifc"}, "params": {"action": "extract"}},
    "drawing_qto": {"input": {"file_path": "/tmp/test.pdf"}, "params": {"action": "extract_quantities"}},
    "primavera_parser": {"input": {"file_path": "/tmp/test.xer"}, "params": {"action": "parse"}},
    "spec_analyzer": {"input": {"text": "Material: Concrete C30"}, "params": {"action": "analyze"}},
    "formula_executor": {"input": {"expression": "300*45"}, "params": {}},
    "sympy_reasoning": {"input": {"expression": "x**2-4"}, "params": {}},
    "historical_benchmark": {"input": {"text": "Compare costs"}, "params": {"action": "benchmark"}},
    "smart_orchestrator": {"input": {"text": "Process doc"}, "params": {"action": "route"}},
    "local_drive": {"input": {"path": "/tmp"}, "params": {"action": "list"}},
    "google_drive": {"input": {"action": "list"}, "params": {}},
    "onedrive":   {"input": {"action": "list"}, "params": {}},
    "android_drive": {"input": {"action": "list"}, "params": {}},
    "vector_search": {"input": {"text": "concrete curing"}, "params": {"action": "search"}},
    "zvec":       {"input": {"text": "concrete curing"}, "params": {"action": "search"}},
    "cache_manager": {"input": {"action": "get", "key": "test"}, "params": {}},
    "capture":    {"input": {"text": "screenshot desc"}, "params": {"action": "describe"}},
    "agent_swarm": {"input": {"objective": "Analyze", "agents": [{"name": "a1"}], "tasks": [{"agent": "a1", "description": "calc"}]}, "params": {}},
    "workflow":   {"input": {"steps": [{"block": "chat", "params": {}}]}, "params": {"action": "run"}},
    "notification": {"input": {"channel": "webhook", "message": "test", "url": "https://httpbin.org/post"}, "params": {"action": "send"}},
    "knowledge":  {"input": {"question": "What is concrete?"}, "params": {}},
}

async def main():
    print("="*80)
    print("BLOCK TEST V2 — CORRECTED INPUTS")
    print("="*80 + "\n")
    
    real_success = []
    api_key_needed = []
    file_needed = []
    graceful_error = []
    broken = []
    
    for name in sorted(BLOCK_REGISTRY.keys()):
        test = TEST_INPUTS.get(name, {"input": {}, "params": {}})
        block = BLOCK_REGISTRY[name]()
        
        try:
            result = await block.execute(test["input"], test["params"])
            status = result.get("status", "unknown")
            
            if status == "success":
                real_success.append(name)
            elif status == "error":
                err = str(result.get("error", result.get("result", {})))
                if any(x in err.lower() for x in ["api key", "api_key", "not authenticated", "not set"]):
                    api_key_needed.append((name, err[:50]))
                elif any(x in err.lower() for x in ["file_path", "file not found", "no file", "no input files"]):
                    file_needed.append((name, err[:50]))
                else:
                    graceful_error.append((name, err[:50]))
            else:
                graceful_error.append((name, f"status={status}"))
        except Exception as e:
            broken.append((name, f"{type(e).__name__}: {str(e)[:50]}"))
    
    print(f"✅ REAL SUCCESS ({len(real_success)}): {', '.join(real_success)}")
    print(f"\n🔑 NEEDS API KEY ({len(api_key_needed)}):")
    for name, err in api_key_needed:
        print(f"   {name:25} → {err}")
    print(f"\n📄 NEEDS REAL FILE ({len(file_needed)}):")
    for name, err in file_needed:
        print(f"   {name:25} → {err}")
    print(f"\n⚠️  GRACEFUL ERROR ({len(graceful_error)}):")
    for name, err in graceful_error:
        print(f"   {name:25} → {err}")
    print(f"\n❌ BROKEN ({len(broken)}):")
    for name, err in broken:
        print(f"   {name:25} → {err}")
    
    print(f"\n{'='*80}")
    print(f"{len(real_success)} real success | {len(api_key_needed)} need API key | {len(file_needed)} need file | {len(graceful_error)} graceful error | {len(broken)} broken")
    print(f"{'='*80}")

asyncio.run(main())
