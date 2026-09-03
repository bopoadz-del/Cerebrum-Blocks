"""The contract fields on ``block.json``: what a block needs, what it
produces, and how it fails.

KERNEL_DEFAULTS 1.2, extending #84. Every field here is **optional**. A
manifest that declares none of them is valid, which is why all 114 manifests
in this repo still pass unchanged.

WHY OPTIONAL, AND WHAT BREAKS WHEN THEY ARE NOT
-----------------------------------------------
"If you assign it, you feed it" is only enforceable at plan time if
``requires_inputs`` and ``preconditions`` are declared. But the planner
cannot be taught to require a field that no manifest carries yet, and only a
kit's author can honestly assert what their block needs -- inferring it from
code would manufacture exactly the confident-but-unsourced claim this whole
contract exists to prevent.

So the field lands first, empty, and is filled by authors. The flip from
optional to required is a separate PR, after P7, with the owner's tick.

THE SIGNATURE PROBLEM, AND WHY THESE FIELDS ARE EXCLUDED FROM THE DIGEST
------------------------------------------------------------------------
``BlockSigner._compute_digests`` hashes the canonical JSON of ``block.json``.
Any new key changes that JSON, which would invalidate all 114 existing
signatures -- and the private key is not in this repo, so nothing could be
re-signed.

#84 hit this with ``trust_tier`` and solved it by stripping the field before
hashing. The same treatment is applied here, for the same reason and with the
same limit: the fields are checked by the validator but not yet covered by
the signature, until the operator re-signs.

Because no manifest in the repo carries any of these fields today, adding
them to the strip list leaves every existing digest byte-for-byte identical.
There is a test that recomputes all 114 and proves it.

RELATIONSHIP TO THE FIELDS THAT ALREADY EXIST
---------------------------------------------
``inputs`` / ``outputs`` are already on every manifest, and are NOT the same
claim. They are UI-and-config derived -- generated from a block's
``default_config``, with ``required: false`` on essentially everything -- and
they describe what the form should render. ``requires_inputs`` and
``produces`` are the runtime contract: what must be present for the block to
do its work at all, and what a caller can rely on getting back. Conflating
them is why a planner can assign a block it cannot feed.

``version`` is already required on all 114 manifests (see
``scripts/audit_block_standards.REQUIRED_MANIFEST_KEYS``) and is therefore
not redefined here.

``trust_tier`` is pinned in :mod:`app.core.trust_tier` and consumed, never
restated -- two copies of an accepted-value set drift, and the failure mode
of that drift is a block that one checker admits and another rejects.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

try:  # normal import, inside the running application
    from app.core.block_result import STATUSES
except ImportError:  # pragma: no cover - standalone load
    # ``scripts/audit_block_standards.py`` deliberately does not import
    # ``app.core``: that package pulls the whole API stack. It loads the
    # trust_tier pin by path instead, and this module has to survive the
    # same treatment. Loading block_result.py by path keeps ONE definition
    # of the four statuses -- restating them here is the drift AGENTS.md
    # warns about, and the failure mode is a manifest one checker admits
    # and another rejects.
    _NAME = "_block_result_standalone"
    _spec = importlib.util.spec_from_file_location(
        _NAME, Path(__file__).with_name("block_result.py")
    )
    _block_result = importlib.util.module_from_spec(_spec)
    # Registered BEFORE exec: @dataclass resolves annotations via
    # sys.modules[cls.__module__], and an unregistered module makes that a
    # None lookup.
    sys.modules[_NAME] = _block_result
    _spec.loader.exec_module(_block_result)
    STATUSES = _block_result.STATUSES

# -- field names -----------------------------------------------------------

REQUIRES_INPUTS = "requires_inputs"
PRODUCES = "produces"
PRECONDITIONS = "preconditions"
FAILURE_MODES = "failure_modes"
KILL_SWITCH = "kill_switch"
SOURCE_COMMIT = "source_commit"
PROVENANCE_POLICY = "provenance_policy"

#: Training-eligibility label. KERNEL_DEFAULTS names this for
#: ``learning_engine``: only independently labeled samples may train.
#: Other blocks may still declare a free-text policy; this pin is the
#: one value that is store-enforced for the learning block.
TRAINING_ELIGIBILITY_POLICY = "independently_labeled_only"

#: Every contract field, all optional. Ordered as KERNEL_DEFAULTS 1.2 lists
#: them. ``trust_tier`` and ``version`` are absent on purpose: both already
#: exist and are already required.
CONTRACT_MANIFEST_KEYS = (
    REQUIRES_INPUTS,
    PRODUCES,
    PRECONDITIONS,
    FAILURE_MODES,
    KILL_SWITCH,
    SOURCE_COMMIT,
    PROVENANCE_POLICY,
)

#: Fields stripped before the manifest is hashed. See "THE SIGNATURE
#: PROBLEM" above. Consumed by ``BlockSigner._compute_digests``.
UNSIGNED_CONTRACT_KEYS = frozenset(CONTRACT_MANIFEST_KEYS)


# -- vocabularies ----------------------------------------------------------

#: Type names, taken from what the 114 manifests in this repo actually use
#: rather than invented. The set is untidy on purpose: ``list`` and ``array``
#: both appear, as do ``text`` and ``string``. Normalising them would mean
#: rewriting existing manifests, which this lane does not do while Cowork is
#: booting zips from the store.
DECLARED_TYPES = frozenset(
    {
        "json",
        "string",
        "text",
        "boolean",
        "number",
        "percentage",
        "file",
        "array",
        "list",
        "object",
        "code",
        "markdown",
        "any",
    }
)

#: What a precondition can require to exist before the block runs.
#: KERNEL_DEFAULTS names team, file and index; the rest are the other
#: resources blocks in this store actually wait on.
PRECONDITION_KINDS = frozenset(
    {"team", "file", "index", "service", "dataset", "credential", "block"}
)

#: An environment variable name: upper snake case.
_ENV_VAR = re.compile(r"^[A-Z][A-Z0-9_]*$")

#: A git SHA, abbreviated or full.
_SHA = re.compile(r"^[0-9a-f]{7,40}$")


# -- helpers ---------------------------------------------------------------


def _entries(value: Any, field: str) -> List[str]:
    """Every list-shaped field has the same two ways of being wrong."""
    if not isinstance(value, list):
        return ["%s must be a list, got %s" % (field, type(value).__name__)]
    reasons = []
    for index, entry in enumerate(value):
        if not isinstance(entry, dict):
            reasons.append(
                "%s[%d] must be an object, got %s" % (field, index, type(entry).__name__)
            )
    return reasons


def _named_typed(value: Any, field: str) -> List[str]:
    """Shape shared by ``requires_inputs`` and ``produces``."""
    reasons = _entries(value, field)
    if reasons:
        return reasons
    for index, entry in enumerate(value):
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            reasons.append("%s[%d] has no name" % (field, index))
        declared = entry.get("type")
        if declared is None:
            reasons.append(
                "%s[%d] (%s) declares no type" % (field, index, name or "?")
            )
        elif declared not in DECLARED_TYPES:
            reasons.append(
                "%s[%d] (%s) has unknown type %r (accepted: %s)"
                % (field, index, name or "?", declared, ", ".join(sorted(DECLARED_TYPES)))
            )
        if field == REQUIRES_INPUTS and "required" in entry:
            if not isinstance(entry["required"], bool):
                reasons.append(
                    "%s[%d] (%s) has a non-boolean 'required'"
                    % (field, index, name or "?")
                )
    return reasons


# -- per-field checks ------------------------------------------------------


def check_requires_inputs(value: Any) -> List[str]:
    """What must be fed to this block for it to do its work.

    Not ``inputs``: that field is form-rendering metadata. This one is the
    claim a planner checks before it assigns the block.
    """
    return _named_typed(value, REQUIRES_INPUTS)


def check_produces(value: Any) -> List[str]:
    """What a caller can rely on getting back."""
    return _named_typed(value, PRODUCES)


def check_preconditions(value: Any) -> List[str]:
    """Resources that must already exist: a team, a file, a built index."""
    reasons = _entries(value, PRECONDITIONS)
    if reasons:
        return reasons
    for index, entry in enumerate(value):
        kind = entry.get("kind")
        if kind not in PRECONDITION_KINDS:
            reasons.append(
                "%s[%d] has unknown kind %r (accepted: %s)"
                % (PRECONDITIONS, index, kind, ", ".join(sorted(PRECONDITION_KINDS)))
            )
        ref = entry.get("ref")
        if not isinstance(ref, str) or not ref.strip():
            reasons.append(
                "%s[%d] names no ref -- a precondition nobody can check is not "
                "a precondition" % (PRECONDITIONS, index)
            )
    return reasons


def check_failure_modes(value: Any) -> List[str]:
    """How this block is known to fail, enumerated.

    Each mode names the :class:`~app.core.block_result.BlockResult` status it
    surfaces as, which is what stops "it failed" and "it refused" collapsing
    into the same line on a report.
    """
    reasons = _entries(value, FAILURE_MODES)
    if reasons:
        return reasons
    for index, entry in enumerate(value):
        mode = entry.get("mode")
        if not isinstance(mode, str) or not mode.strip():
            reasons.append("%s[%d] has no mode name" % (FAILURE_MODES, index))
        status = entry.get("status")
        if status not in STATUSES:
            reasons.append(
                "%s[%d] (%s) declares status %r, which is not a BlockResult "
                "status (accepted: %s)"
                % (
                    FAILURE_MODES,
                    index,
                    mode or "?",
                    status,
                    ", ".join(sorted(STATUSES)),
                )
            )
        elif status == "ok":
            reasons.append(
                "%s[%d] (%s) declares status 'ok' -- a failure mode that "
                "reports success is the defect this field exists to surface"
                % (FAILURE_MODES, index, mode or "?")
            )
    return reasons


def check_kill_switch(value: Any) -> List[str]:
    """The environment variable that turns this block off.

    A name, never a value: this field says which switch exists, and putting a
    secret or a state in a committed manifest is a different mistake.
    """
    if not isinstance(value, str) or not value.strip():
        return ["%s must be a non-empty environment variable name" % KILL_SWITCH]
    if not _ENV_VAR.match(value.strip()):
        return [
            "%s %r is not an environment variable name (expected upper snake "
            "case)" % (KILL_SWITCH, value)
        ]
    return []


def check_source_commit(value: Any) -> List[str]:
    """Where harvested code came from: repo plus SHA. The drift answer.

    Without it, a block copied from another repository is indistinguishable
    from one written here, and nobody can tell whether an upstream fix has
    been picked up.
    """
    if not isinstance(value, dict):
        return [
            "%s must be an object with 'repo' and 'sha', got %s"
            % (SOURCE_COMMIT, type(value).__name__)
        ]
    reasons = []
    repo = value.get("repo")
    if not isinstance(repo, str) or not repo.strip():
        reasons.append("%s names no repo" % SOURCE_COMMIT)
    sha = value.get("sha")
    if not isinstance(sha, str) or not _SHA.match(sha.strip().lower()):
        reasons.append(
            "%s has no usable sha (expected 7-40 hex characters, got %r)"
            % (SOURCE_COMMIT, sha)
        )
    return reasons


def check_provenance_policy(value: Any) -> List[str]:
    """How this block is required to source what it returns.

    KERNEL_DEFAULTS 1.2 names this field but does not define its vocabulary,
    so the check is deliberately shallow: a non-empty string. Pinning an
    accepted set is a later PR and needs the owner -- inventing one here
    would put a value in the contract that no spec backs, which is the shape
    of mistake the contract is for.
    """
    if not isinstance(value, str) or not value.strip():
        return [
            "%s must be a non-empty string (its vocabulary is not yet pinned)"
            % PROVENANCE_POLICY
        ]
    return []


_CHECKS = {
    REQUIRES_INPUTS: check_requires_inputs,
    PRODUCES: check_produces,
    PRECONDITIONS: check_preconditions,
    FAILURE_MODES: check_failure_modes,
    KILL_SWITCH: check_kill_switch,
    SOURCE_COMMIT: check_source_commit,
    PROVENANCE_POLICY: check_provenance_policy,
}


def check_contract_fields(manifest: Dict[str, Any]) -> List[str]:
    """Validate whichever contract fields a manifest declares.

    Absence is never an error -- every field is optional in this phase. A
    field that IS present is checked, because a half-filled declaration is
    worse than none: a planner that reads ``requires_inputs`` and finds an
    entry with no type will either guess or crash, and both are worse than
    knowing the block never said.
    """
    reasons: List[str] = []
    for field in CONTRACT_MANIFEST_KEYS:
        if field not in manifest:
            continue
        value = manifest[field]
        if value is None:
            reasons.append(
                "%s is present but null; omit the field instead of declaring "
                "nothing with it" % field
            )
            continue
        reasons.extend(_CHECKS[field](value))
    return reasons


def declared_contract_fields(manifest: Dict[str, Any]) -> List[str]:
    """Which contract fields this manifest actually carries.

    Used by the report-only conformance table: the interesting number during
    this phase is how many manifests have adopted anything at all.
    """
    return [field for field in CONTRACT_MANIFEST_KEYS if field in manifest]
