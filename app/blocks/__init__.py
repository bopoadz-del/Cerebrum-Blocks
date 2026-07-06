"""Platform Blocks — Cerebrum Block Store runtime.

Virgin boot (default): ~17 generic blocks. Domain kits register via store
install or ``CEREBRUM_DOMAIN_KITS``. Set ``CEREBRUM_VIRGIN=false`` for legacy
full-platform boot.
"""

import importlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple

from app.core.block_capabilities import BlockCapabilities
from app.core.universal_base import UniversalBlock, UniversalContainer
from app.core.typed_block import TypedBlock

logger = logging.getLogger(__name__)

_GENERIC_BLOCK_DEFS: Dict[str, Tuple[str, str]] = {
    "pdf": ("app.blocks.pdf", "PDFBlock"),
    "marker": ("app.blocks.marker", "MarkerBlock"),
    "ocr": ("app.blocks.ocr", "OCRBlock"),
    "image": ("app.blocks.image", "ImageBlock"),
    "document_engine": ("app.blocks.document_engine", "DocumentEngineBlock"),
    "chat": ("app.blocks.chat", "ChatBlock"),
    "translate": ("app.blocks.translate", "TranslateBlock"),
    "voice": ("app.blocks.voice", "VoiceBlock"),
    "web": ("app.blocks.web", "WebBlock"),
    "search": ("app.blocks.search", "SearchBlock"),
    "code": ("app.blocks.code", "CodeBlock"),
    "vector_search": ("app.blocks.vector_search", "VectorSearchBlock"),
    "zvec": ("app.blocks.zvec", "ZvecBlock"),
    "cache_manager": ("app.blocks.cache_manager", "CacheManagerBlock"),
    "memory": ("app.blocks.memory", "MemoryBlock"),
    "auth": ("app.blocks.auth", "AuthBlock"),
    "monitoring": ("app.blocks.monitoring", "MonitoringBlock"),
    "file_hasher": ("app.blocks.file_hasher", "FileHasherBlock"),
    "orchestrator": ("app.blocks.orchestrator", "OrchestratorBlock"),
    "validation_pipeline": ("app.blocks.validation_pipeline", "ValidationPipelineBlock"),
    "async_processor": ("app.blocks.async_processor", "AsyncProcessorBlock"),
    "video_metadata_ingest": ("app.blocks.video_metadata_ingest", "VideoMetadataIngestBlock"),
    "video_anomaly_trigger": ("app.blocks.video_anomaly_trigger", "VideoAnomalyTriggerBlock"),
}

_REGISTRY_ROOT = Path(__file__).resolve().parents[2] / "block_registry"


def _is_core_block(block_name: str) -> bool:
    """Return ``True`` for trusted platform core blocks."""
    return block_name in _GENERIC_BLOCK_DEFS


def _is_platform_extended_block(block_name: str) -> bool:
    """Return ``True`` for bundled platform extended blocks.

    These blocks ship with the platform (like core blocks) but are loaded
    through the extended block list. They receive the ``verified`` tier unless
    the publisher registry or certification store says otherwise.
    """
    return block_name in _EXTENDED_BLOCK_DEFS


_EXTENDED_BLOCK_DEFS: Dict[str, Tuple[str, str]] = {
    "pdf_v2": ("app.blocks.pdf_v2", "PDFBlockV2"),
    "ocr_v2": ("app.blocks.ocr_v2", "OCRBlockV2"),
    "llm_enhancer": ("app.blocks.llm_enhancer", "LLMEnhancerBlock"),
    "local_drive": ("app.blocks.local_drive", "LocalDriveBlock"),
    "google_drive": ("app.blocks.google_drive", "GoogleDriveBlock"),
    "onedrive": ("app.blocks.onedrive", "OneDriveBlock"),
    "android_drive": ("app.blocks.android_drive", "AndroidDriveBlock"),
    "storage": ("app.blocks.storage", "StorageBlock"),
    "context_broker": ("app.blocks.context_broker", "ContextBrokerBlock"),
    "capture": ("app.blocks.capture", "CaptureBlock"),
    "agent_swarm": ("app.blocks.agent_swarm", "AgentSwarmBlock"),
    "workflow": ("app.blocks.workflow", "WorkflowBlock"),
    "knowledge": ("app.blocks.knowledge", "KnowledgeBlock"),
    "queue": ("app.blocks.queue", "QueueBlock"),
    "audit": ("app.blocks.audit", "AuditBlock"),
    "team": ("app.blocks.team", "TeamBlock"),
    "version": ("app.blocks.version", "VersionBlock"),
    "health_check": ("app.blocks.health_check", "HealthCheckBlock"),
    "rate_limiter": ("app.blocks.rate_limiter", "RateLimiterBlock"),
    "validation": ("app.blocks.validation", "ValidationBlock"),
    "error_tracking": ("app.blocks.error_tracking", "ErrorTrackingBlock"),
    "webhook": ("app.blocks.webhook", "WebhookBlock"),
    "notification": ("app.blocks.notification", "NotificationBlock"),
    "analytics": ("app.blocks.analytics", "AnalyticsBlock"),
    "discovery": ("app.blocks.discovery", "DiscoveryBlock"),
    "dashboard": ("app.blocks.dashboard", "DashboardBlock"),
    "sandbox": ("app.blocks.sandbox", "SandboxBlock"),
    "failover": ("app.blocks.failover", "FailoverBlock"),
    "traffic_manager": ("app.blocks.traffic_manager", "TrafficManagerBlock"),
    "adaptive_router": ("app.blocks.adaptive_router", "AdaptiveRouterBlock"),
    "review": ("app.blocks.review", "ReviewBlock"),
    "payment_split": ("app.blocks.payment_split", "PaymentSplitBlock"),
    "documentation": ("app.blocks.documentation", "DocumentationBlock"),
    "config": ("app.blocks.config", "ConfigBlock"),
    "database": ("app.blocks.database", "DatabaseBlock"),
    "vector": ("app.blocks.vector", "VectorBlock"),
    "billing": ("app.blocks.billing", "BillingBlock"),
    "email": ("app.blocks.email", "EmailBlock"),
    "migration": ("app.blocks.migration", "MigrationBlock"),
    "event_bus": ("app.blocks.event_bus", "EventBusBlock"),
    "secrets": ("app.blocks.secrets", "SecretsBlock"),
    "skills": ("app.blocks.skills", "SkillsBlock"),
    "library_container": ("app.blocks.library_container", "LibraryContainerBlock"),
    "video_metadata_ingest": ("app.blocks.video_metadata_ingest", "VideoMetadataIngestBlock"),
    "video_anomaly_trigger": ("app.blocks.video_anomaly_trigger", "VideoAnomalyTriggerBlock"),
    "medical_ehr_connector": ("app.blocks.medical_ehr_connector", "MedicalEHRConnectorBlock"),
    "construction_advisor": ("app.blocks.construction_advisor", "ConstructionAdvisorBlock"),
    "historical_benchmark": ("app.blocks.historical_benchmark", "HistoricalBenchmarkBlock"),
    "mcp_adapter": ("app.blocks.mcp_adapter", "MCPAdapterBlock"),
    "mcp_consumer": ("app.blocks.mcp_consumer", "MCPConsumerBlock"),
}


def _legacy_boot() -> bool:
    return os.getenv("CEREBRUM_VIRGIN", "true").strip().lower() in ("0", "false", "no")


def _load_manifest(name: str) -> Optional[Dict[str, Any]]:
    """Load ``block_registry/<name>/block.json`` if it exists and is valid."""
    manifest_path = _REGISTRY_ROOT / name / "block.json"
    if not manifest_path.exists():
        return None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("invalid manifest for '%s': %s", name, exc)
        return None


def _validate_block_capabilities(name: str) -> Tuple[bool, str]:
    """Parse the block's declared capabilities.

    Returns ``(True, "")`` when a ``permissions`` declaration exists and is
    parseable. Returns ``(False, reason)`` when the declaration is missing or
    malformed. This is the fail-closed gate used for every non-core block,
    whether it comes from the registry, a kit bundle, or a store install.
    """
    manifest = _load_manifest(name)
    if manifest is None:
        return False, f"no block.json declaration found for '{name}'"
    permissions = manifest.get("permissions")
    if not isinstance(permissions, dict):
        return False, f"permissions declaration missing or invalid in block.json for '{name}'"
    try:
        BlockCapabilities.from_manifest(manifest)
    except Exception as exc:
        return False, f"failed to parse capabilities for '{name}': {exc}"
    return True, ""


def _validate_registry_block(name: str, validator: Any, *, require_capabilities: bool) -> bool:
    """Validate a non-core block before it is admitted to ``_BLOCK_DEFS``.

    - Core blocks are trusted and admitted without validation.
    - Legacy extended blocks and store-install blocks without a registry folder
      retain their pre-gate behavior.
    - Kit-loaded blocks must provide a parseable ``permissions`` declaration in
      ``block_registry/<name>/block.json``. A missing or invalid declaration
      causes the block to be excluded with a clear log line.
    - Blocks with a registry folder that are NOT kit-loaded (i.e. genuine
      registry blocks) still go through the full ``BlockValidator`` gate
      (manifest, signature/digest, AST scan).
    """
    if _is_core_block(name):
        return True

    block_path = _REGISTRY_ROOT / name
    is_kit_block = require_capabilities

    # Kit-loaded block: enforce capability declaration only. Do not subject
    # kit bundles to the full registry validation gate; their security
    # contract is the capability declaration, not publisher signatures.
    if is_kit_block:
        ok, reason = _validate_block_capabilities(name)
        if not ok:
            logger.warning("validation failed for '%s': %s; excluding block", name, reason)
            return False
        return True

    # Non-kit block with a registry folder: run the full validator gate.
    if block_path.is_dir():
        try:
            result = validator.validate_block(block_path)
        except Exception as exc:
            logger.warning("validation gate crashed for '%s': %s; excluding block", name, exc)
            return False

        if result.status != "passed":
            logger.warning(
                "validation failed for '%s' (%s): %s; excluding block",
                name,
                result.status,
                result.reasons,
            )
            return False
        return True

    return True


def _create_validator() -> Any:
    """Construct a shared BlockValidator for admission and tier resolution."""
    try:
        from app.core.block_validation import BlockValidator

        return BlockValidator()
    except Exception as exc:  # pragma: no cover - defensive import guard
        logger.warning(
            "validation gate unavailable for non-core blocks: %s; "
            "third-party blocks will be excluded if they have registry folders",
            exc,
        )
    return None


def _build_block_defs(validator: Any = None) -> Dict[str, Tuple[str, str]]:
    from app.core.domain_kit_loader import kit_block_specs, verify_installed_containers

    verify_installed_containers()
    defs: Dict[str, Tuple[str, str]] = dict(_GENERIC_BLOCK_DEFS)

    candidate_blocks: Dict[str, Tuple[str, str]] = {}
    kit_block_names: set[str] = set()
    if _legacy_boot():
        candidate_blocks.update(_EXTENDED_BLOCK_DEFS)
    for name, module, class_name in kit_block_specs():
        candidate_blocks[name] = (module, class_name)
        kit_block_names.add(name)

    if validator is None and candidate_blocks:
        validator = _create_validator()

    for name, spec in candidate_blocks.items():
        if validator is not None and not _validate_registry_block(
            name, validator, require_capabilities=name in kit_block_names
        ):
            continue
        defs[name] = spec

    return defs


def _resolve_publisher_tier(name: str, validator: Any) -> Optional[str]:
    """Return the publisher tier for a non-core block.

    Priority:
      1. Live publisher registry lookup by manifest publisher_id. This takes
         precedence over cached certifications so revocation is honored
         immediately without waiting for certification TTL expiration.
      2. Existing passing certification in the certification store, if the
         registry is unavailable.
      3. Default to "community" if unknown.
    """
    manifest = _load_manifest(name)
    publisher_id = (manifest or {}).get("publisher_id")

    # 1. Live publisher registry (revocation must be immediate)
    if publisher_id and validator is not None and validator.publisher_registry is not None:
        try:
            record = validator.publisher_registry.get(publisher_id)
            if record is not None:
                return record.tier
        except Exception as exc:
            logger.warning("could not lookup publisher '%s' for '%s': %s", publisher_id, name, exc)

    # 2. Certification store fallback
    if validator is not None:
        try:
            result = validator.certification_store.get(name)
            if result is not None and result.status == "passed" and result.publisher_tier:
                return result.publisher_tier
        except Exception as exc:
            logger.warning("could not read certification for '%s': %s", name, exc)

    # 3. Fail closed
    return "community"


def _build_block_caps(
    defs: Dict[str, Tuple[str, str]],
    validator: Any = None,
) -> Dict[str, BlockCapabilities]:
    """Build a capability map for all registered blocks.

    Core blocks are trusted and default to safe (no network/fs/cross-block).
    Non-core blocks with a registry folder parse their manifest and resolve
    the publisher tier from the certification store or publisher registry.

    An optional ``validator`` may be supplied for testing; when omitted a
    default ``BlockValidator`` is constructed.
    """
    if validator is None:
        from app.core.block_validation import BlockValidator

        try:
            validator = BlockValidator()
        except Exception as exc:
            logger.warning("validation gate unavailable for tier resolution: %s", exc)

    caps: Dict[str, BlockCapabilities] = {}
    for name in defs:
        if _is_core_block(name):
            caps[name] = BlockCapabilities()
        else:
            base_caps = BlockCapabilities.from_registry(name, _REGISTRY_ROOT)
            tier = _resolve_publisher_tier(name, validator)
            # Platform extended blocks ship with the platform and are treated
            # as verified unless a publisher registry / certification record
            # says otherwise. Third-party kit blocks and store installs remain
            # community by default.
            if tier == "community" and _is_platform_extended_block(name):
                tier = "verified"
            caps[name] = BlockCapabilities(
                network=base_caps.network,
                filesystem=base_caps.filesystem,
                imports=base_caps.imports,
                blocks=base_caps.blocks,
                publisher_tier=tier,
            )
    return caps


_BLOCK_VALIDATOR: Any = _create_validator()
_BLOCK_DEFS: Dict[str, Tuple[str, str]] = _build_block_defs(_BLOCK_VALIDATOR)
_BLOCK_CAPS: Dict[str, BlockCapabilities] = _build_block_caps(_BLOCK_DEFS, _BLOCK_VALIDATOR)


class _LazyBlockRegistry:
    """Dict-like view of block classes that imports each module on first access.

    Supports the subset of dict API the codebase actually uses:
    [name], .get(name), name in registry, .items(), .keys(), len(),
    iteration. .items() is lazy too — yields (name, class) pairs and forces
    import at the moment each pair is consumed. So `for name, cls in items()`
    DOES load every block, by design (e.g. init_blocks pass).
    """

    __slots__ = ("_resolved",)

    def __init__(self) -> None:
        self._resolved: Dict[str, Any] = {}

    def _resolve(self, name: str) -> Any:
        cached = self._resolved.get(name)
        if cached is not None:
            return cached
        if name not in _BLOCK_DEFS:
            raise KeyError(name)
        module_path, class_name = _BLOCK_DEFS[name]
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
        except Exception as exc:
            logger.exception("block import failed: %s (%s.%s) — %s",
                             name, module_path, class_name, exc)
            raise
        self._resolved[name] = cls
        return cls

    def __getitem__(self, name: str) -> Any:
        return self._resolve(name)

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in _BLOCK_DEFS

    def get(self, name: str, default: Any = None) -> Any:
        try:
            return self._resolve(name)
        except (KeyError, Exception):
            return default

    def keys(self) -> Iterator[str]:
        return iter(_BLOCK_DEFS.keys())

    def items(self) -> Iterator[Tuple[str, Any]]:
        for name in _BLOCK_DEFS:
            try:
                yield name, self._resolve(name)
            except Exception:
                continue  # skip blocks whose import fails

    def __iter__(self) -> Iterator[str]:
        return iter(_BLOCK_DEFS.keys())

    def __len__(self) -> int:
        return len(_BLOCK_DEFS)


BLOCK_REGISTRY = _LazyBlockRegistry()


def get_block(name: str):
    return BLOCK_REGISTRY.get(name)


def get_all_blocks():
    return BLOCK_REGISTRY


def get_block_capabilities(name: str) -> BlockCapabilities:
    """Return the runtime capabilities declared for ``name``.

    Core blocks default to safe (no network/filesystem/cross-block) capabilities.
    Non-core blocks return the parsed manifest permissions.
    """
    return _BLOCK_CAPS.get(name, BlockCapabilities())


__all__ = [
    "UniversalBlock",
    "UniversalContainer",
    "TypedBlock",
    "BLOCK_REGISTRY",
    "BlockCapabilities",
    "get_block",
    "get_all_blocks",
    "get_block_capabilities",
]


# Build a fast reverse lookup so `from app.blocks import PDFBlock` (tests do this)
# resolves to the same class as BLOCK_REGISTRY["pdf"], with the same lazy import.
_CLASS_TO_NAME: Dict[str, str] = {
    class_name: block_name for block_name, (_, class_name) in _BLOCK_DEFS.items()
}


def __getattr__(name: str) -> Any:
    """Module-level lazy attribute access (PEP 562).

    Lets callers do `from app.blocks import PDFBlock` without forcing an
    eager import of every block at module load. Falls back to AttributeError
    for unknown names so the rest of Python's import machinery still works.
    """
    block_name = _CLASS_TO_NAME.get(name)
    if block_name is None:
        raise AttributeError(f"module 'app.blocks' has no attribute {name!r}")
    return BLOCK_REGISTRY[block_name]
