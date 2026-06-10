"""Security & Surveillance Suite — domain container stub.

Subclasses ``DomainContainer`` (``app/containers/base.py``). When this kit is
published, ``container.py`` is copied to ``app/containers/security.py`` per
manifest ``skeleton_artifacts`` / ``artifacts``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

from app.containers.base import DomainContainer


class SecurityContainer(DomainContainer):
    name = "security"
    description = "Physical security, access control, and threat monitoring blocks."
    version = "0.0.0-skeleton"
    system_prompt_file = "security_expert.txt"

    def __init__(self, kit_root: Path | None = None) -> None:
        self.kit_root = kit_root or Path(__file__).resolve().parent

    def get_actions(self) -> Dict[str, Callable]:
        # TODO: wire domain actions (e.g. analyze, summarize, route_to_block)
        return {}
