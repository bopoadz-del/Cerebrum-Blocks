# Design Review Brief: Commit 61b465d9
## Capability-aware block validation, proxy dispatch, and registry refresh

**Commit:** `61b465d9b6e1bb9b0c11b987427bb7c5fe75c957`  
**Title:** `feat(sandbox): capability-aware block validation, proxy dispatch, and registry refresh`  
**Repo:** Cerebrum-Blocks  
**Date:** 2026-07-05

---

## 1. Trust model: who/what is trusted after this commit?

### 1.1 Core platform blocks are trusted by default

`app/blocks/__init__.py:_is_core_block()` treats the ~17 generic blocks in `_GENERIC_BLOCK_DEFS` as trusted:

```python
_GENERIC_BLOCK_DEFS: Dict[str, Tuple[str, str]] = {
    "pdf": ("app.blocks.pdf", "PDFBlock"),
    "marker": ("app.blocks.marker", "MarkerBlock"),
    "ocr": ("app.blocks.ocr", "OCRBlock"),
    ...
}

def _is_core_block(block_name: str) -> bool:
    return block_name in _GENERIC_BLOCK_DEFS
```

They bypass the validation gate and receive full platform access (`set_platform(BLOCK_REGISTRY, block_instances, ...)`).

### 1.2 Non-core blocks are untrusted until declared and/or validated

There are two sub-classes:

- **Registry blocks with a `block_registry/<name>/` folder** — must pass the full `BlockValidator` gate (manifest required fields, Ed25519 signature, file digests, AST scan) before admission.
- **Kit-loaded blocks** — only required to provide a parseable `permissions` declaration in `block_registry/<name>/block.json` (PR #22 closed this path). They are not signature-checked.

### 1.3 The sandbox runner is the execution boundary

Any non-core block that declares network, filesystem, privileged imports, or cross-block access is wrapped by `CapabilityProxy` and dispatched to the sandbox runner. The runner itself is trusted to enforce container-level isolation (the Docker Compose template launches it with `--network=none`).

### 1.4 What an untrusted block can and cannot do

| Capability | In-process | Out-of-process via runner |
|---|---|---|
| No network, fs, privileged imports, no cross-block | Allowed | N/A (not sent) |
| Network | Denied | Allowed inside sandbox container |
| Filesystem | Denied | Allowed inside sandbox container |
| Privileged import (`os`, `subprocess`, `requests`, etc.) | Denied | Allowed inside sandbox container |
| Cross-block access (`requires=["memory"]`) | Denied unless declared in `permissions.blocks` | N/A; runner runs the adapter in isolation |
| Direct access to `BLOCK_REGISTRY` / `block_instances` | Denied for non-core | Denied |

---

## 2. Capabilities: declaration, validation, and propagation

### 2.1 Declaration format

`BlockCapabilities.from_manifest()` parses a `permissions` dict from `block.json`:

```python
@dataclass(frozen=True)
class BlockCapabilities:
    network: bool = False
    filesystem: bool | List[str] = False
    imports: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)
```

Example from `block_registry/zvec/block.json`:

```json
"permissions": {
  "blocks": [],
  "filesystem": false,
  "imports": [],
  "network": false
}
```

### 2.2 Validation gate (`app/core/block_validation.py`)

`BlockValidator.validate_block()` enforces:

1. **Required manifest fields:** `id`, `name`, `version`, `publisher_id`, `signature`, `digests`, `permissions`.
2. **Publisher signature and digests:** Ed25519 signature over `{publisher_id, digests}`; file digests must match.
3. **Publisher trust:** publisher must exist in `PublisherRegistry` and not be `revoked`.
4. **AST scan:** `block.py` is parsed and checked for forbidden imports/modules and forbidden builtins/names.

Forbidden imports/modules:

```python
FORBIDDEN_MODULES: Set[str] = {
    "os", "subprocess", "socket", "requests", "urllib",
    "pickle", "ctypes", "sys",
}
```

Forbidden builtins: `eval`, `exec`, `compile`, `open`, `__import__`.

Forbidden names: `BLOCK_REGISTRY`, `block_instances`, `get_memory_block`.

Result statuses:

- `passed` — signature and AST valid.
- `failed` — manifest/AST/signature/digest error.
- `unverified` — manifest/AST passed but `cryptography` not installed, so signature could not be checked.

Results are cached in `data/block_certifications.json` with a 30-day TTL.

### 2.3 Admission gate (`app/blocks/__init__.py`)

`_validate_registry_block()` decides admission:

```python
def _validate_registry_block(name: str, validator: Any, *, require_capabilities: bool) -> bool:
    if _is_core_block(name):
        return True

    block_path = _REGISTRY_ROOT / name
    is_kit_block = require_capabilities

    if is_kit_block:
        ok, reason = _validate_block_capabilities(name)
        if not ok:
            logger.warning("validation failed for '%s': %s; excluding block", name, reason)
            return False
        return True

    if block_path.is_dir():
        result = validator.validate_block(block_path)
        if result.status != "passed":
            logger.warning(...)
            return False
        return True

    return True
```

Key points:
- Core blocks: admitted unconditionally.
- Kit blocks: must have parseable `permissions` (fail-closed after PR #22).
- Registry-folder blocks: must pass full `BlockValidator`.
- Legacy extended blocks without a registry folder: retain old behavior (admitted).

### 2.4 Propagation to execution

`app/dependencies.py:get_block_instance()`:

```python
caps = get_block_capabilities(block_name)
instance = _create_block_instance(block_class, config, allow_platform=is_core)
if not is_core:
    instance = CapabilityProxy(instance, caps)
block_instances[block_name] = instance
_wire_block_dependencies(block_instances[block_name], block_class, block_name, caps)
```

`CapabilityProxy.execute()` raises if the block is not safe for in-process:

```python
async def execute(self, input_data: Any = None, params: Dict = None) -> Dict:
    if self.requires_out_of_process:
        raise RuntimeError(
            f"block {self._instance.name!r} requires out-of-process execution ..."
        )
    return await self._instance.execute(input_data, params or {})
```

`app/routers/execute.py:_run_block()` dispatches:

```python
capabilities = get_block_capabilities(block_name)
use_runner = not capabilities.is_safe_for_in_process

if use_runner:
    return await _run_block_via_runner(block_name, request.input, request.params or {})
```

---

## 3. Sandbox-runner interaction and failure modes

### 3.1 How blocks reach the runner

`app/routers/execute.py:_run_block_via_runner()` POSTs to `SANDBOX_RUNNER_URL/run_block`:

```python
payload = {
    "block_name": block_name,
    "input": input_data,
    "params": params or {},
    "timeout_s": 60,
}
```

### 3.2 What the runner does

`sandbox-runner/server.py:run_block_endpoint()`:

1. Validates `block_name` (no `..`, `/`).
2. Locates `BLOCK_REGISTRY_ROOT/<block_name>/block.py`.
3. Spawns a subprocess with minimal env (`PATH`, `LANG`, `PYTHONDONTWRITEBYTECODE`, `PYTHONPATH`).
4. Feeds JSON input via stdin.
5. Returns stdout/stderr/result/exit_code/elapsed_ms.
6. Cleans up per-request scratch directory.

On Unix, `preexec_fn=_rlimit` caps address space (256 MB), CPU time (60s), file descriptors (64), and processes (16), and calls `os.setsid()`.

### 3.3 Failure modes

| Scenario | Behavior | Observable |
|---|---|---|
| Block declares unsafe capability | Routed to sandbox runner | `/v1/execute` returns runner output |
| Runner is down | `httpx.ConnectError` → HTTP 503 | Caller sees "Sandbox runner unavailable" |
| Runner times out | HTTP 504 | Caller sees timeout message |
| Runner returns non-zero | HTTP 500 with stderr | Caller sees runner stderr |
| Block lies about capabilities (e.g. imports `os` but doesn't declare it) | AST scan catches it at validation → `failed` | Block excluded from `BLOCK_REGISTRY` |
| Block passes validation but does something malicious at runtime | Runner container isolation is the backstop | Container/network/fs limits apply |
| Cryptography not installed | Status `unverified`, block excluded from registry-folder admission | Log line + excluded |
| Publisher revoked | `BlockVerifier` returns `publisher revoked` | Block excluded |
| Kit block missing `permissions` | `_validate_block_capabilities()` fails | Block excluded from in-process loading |

### 3.4 Gaps in runtime enforcement

- The runner trusts the adapter it finds under `BLOCK_REGISTRY_ROOT`. If an attacker can write to that path, they can execute arbitrary code inside the sandbox container.
- The runner does not re-validate the manifest or AST at execution time; it relies on the main API having done so.
- The runner's subprocess gets the full `BLOCK_REGISTRY_ROOT.parent` on `PYTHONPATH`, so a malicious adapter can import sibling adapters.

---

## 4. Test coverage

### 4.1 New tests added by 61b465d9

- `tests/core/test_block_capabilities.py` — 10 tests covering default safety, network/filesystem/privileged-import/cross-block flags, manifest parsing, registry loading.
- `tests/core/test_block_proxy.py` — 6 tests covering safe delegation, out-of-process rejection, dependency checks, attribute delegation.
- `tests/core/test_block_validation.py` — 9 tests covering passing signed blocks, missing permissions, forbidden imports/builtins, tampered files, certification store persistence.
- `tests/core/test_execute_dispatch.py` — 5 tests covering in-process vs out-of-process dispatch decisions.
- `tests/core/test_sandbox_runner_block.py` — 3 tests covering the `/run_block` endpoint, missing adapter, invalid name.

### 4.2 What is not well covered

- End-to-end runner isolation: no test verifies that a block running in the sandbox cannot reach the network or escape the scratch directory.
- Tampering with `data/block_certifications.json`: no test verifies behavior when the certification store is corrupted or rolled back.
- Publisher revocation at runtime: revocation is tested in `publisher_registry.py` but not integrated with block admission.
- Cross-block dependency enforcement beyond unit tests: `_wire_block_dependencies()` skips undeclared deps with a log, but no integration test confirms a malicious block cannot access them.

---

## 5. Open questions / risks for store trust-tier work

### 5.1 Trust tiers are declared but not enforced

`PublisherRegistry` has tiers (`verified`, `community`, `revoked`), and `BlockValidator` checks revocation. However, the admission gate does not differentiate between `verified` and `community` publishers at runtime. A store trust-tier feature would need to map tiers to execution privileges (e.g., community blocks always run in sandbox, verified blocks may run in-process if safe).

### 5.2 Kit blocks vs. store blocks share the same security contract

Kit-loaded blocks only need a `permissions` dict; they are not signed. If the store allows unsigned "community" blocks, the same code path could be reused, but it conflates "shipped by us in a kit" with "installed from the store by a user." The store will likely need stronger provenance.

### 5.3 No runtime re-validation

Certifications are cached for 30 days. If a publisher is revoked after a block is admitted, the running process continues to use the cached certification. A store with revocation requirements needs either TTL shortening, explicit revocation checks, or online certificate status lookups.

### 5.4 Sandbox runner is a single point of failure

If `SANDBOX_RUNNER_URL` is unreachable, all unsafe blocks fail with HTTP 503. A production store needs runner pooling, health checks, or graceful degradation.

### 5.5 `block.py` adapters are generated stubs

`scripts/regenerate_safe_adapters.py` regenerated all `block_registry/*/block.py` files. These adapters are thin wrappers around the real block classes. The trust model depends on these stubs being immutable and correctly relaying inputs/outputs. If a block author can supply a custom adapter, the model breaks.

### 5.6 Capability declarations are self-reported

A block declares its own `permissions`. While AST scanning catches some lies (forbidden imports), it does not catch runtime dynamic imports, network via non-forbidden modules (e.g. `http.client`), or filesystem access via pathlib/ tempfile unless those are also forbidden. The current forbidden-module list is a starting point, not a complete sandbox policy.

---

## 6. Verdict for store trust-tier implementation

The 61b465d9 commit provides a solid foundation:
- A parseable capability model.
- A validation gate with signature/digest/AST checks.
- A proxy that prevents unsafe in-process execution.
- A sandbox runner for out-of-process isolation.

What is still needed for a production store trust tier:
1. **Enforce publisher tiers at admission and execution** (verified vs community vs revoked).
2. **Add store-specific provenance** (signed store packages, not just kit bundles).
3. **Runtime revocation checks** beyond the 30-day certification TTL.
4. **Sandbox policy hardening** (forbidden-module whitelist expansion, network egress logging, fs chroot).
5. **Runner resilience** (health checks, fallback, pooling).
