"""Which commit is actually serving.

Every fleet report about this service has had to write COULD NOT VERIFY
against the deployed SHA, because no HTTP route exposed it and only the
Render dashboard could settle it — while the Factory next door publishes
exactly this route. That gap is the difference between "the fix is merged"
and "the fix is live", and it is one route wide.

Unauthenticated on purpose: a deploy fact is not a secret, and a probe that
needs a credential is a probe an uptime monitor cannot make.

HTTP tests mount the health router on a bare FastAPI app. They must not
construct ``TestClient(app.main)``: a second portal + lifespan on the
already-warmed process deadlocks the Full suite at ~96% (PR #112 hung 21
minutes after every other file had finished). The assembled app is
covered by ``tests/integration/test_api.py``, whose module-level client
already exists.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import health


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(health.router)
    with TestClient(app) as c:
        yield c


def test_version_is_public(client, monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "a" * 40)
    assert client.get("/version").status_code == 200


def test_version_names_the_service_and_a_sha(client, monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "a" * 40)
    body = client.get("/version").json()
    assert body["service"] == "cerebrum-blocks"
    assert body["git_sha"] == "a" * 40
    assert body["git_sha_short"] == "a" * 7


def test_an_unknown_sha_is_null_not_invented(client, monkeypatch):
    """Reported as unknown rather than guessed.

    A route that returns a plausible-looking wrong SHA is worse than one
    that returns nothing: the first is trusted.
    """
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    monkeypatch.delenv("GIT_COMMIT", raising=False)
    monkeypatch.setattr(health, "_build_sha", lambda: None)
    body = client.get("/version").json()
    assert body["git_sha"] is None
    assert body["git_sha_short"] is None
    assert body["service"] == "cerebrum-blocks"


def test_the_sha_probe_never_raises(monkeypatch):
    """A broken git or a missing binary must not take the route down."""
    import subprocess

    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    monkeypatch.delenv("GIT_COMMIT", raising=False)

    def boom(*a, **k):
        raise OSError("git not found")

    monkeypatch.setattr(subprocess, "run", boom)
    assert health._sha_from_git() is None


def test_version_route_does_not_shell_out(client, monkeypatch):
    """GET /version must not call subprocess on the request path."""
    import subprocess

    monkeypatch.setenv("RENDER_GIT_COMMIT", "d" * 40)

    def boom(*a, **k):
        raise AssertionError("GET /version must not call subprocess.run")

    monkeypatch.setattr(subprocess, "run", boom)
    assert client.get("/version").status_code == 200


def test_the_platform_env_wins_over_git(monkeypatch):
    """On Render the checkout may be shallow or absent; the env is truth."""
    monkeypatch.setenv("RENDER_GIT_COMMIT", "b" * 40)
    assert health._build_sha() == "b" * 40


def test_version_carries_no_secret_shaped_field(client, monkeypatch):
    """It is public, so it may only say what is safe to say publicly."""
    monkeypatch.setenv("RENDER_GIT_COMMIT", "c" * 40)
    body = client.get("/version").json()
    assert set(body) == {"service", "git_sha", "git_sha_short", "env"}


def test_version_is_mounted_ungated_on_the_real_app():
    """The live app has the route and does not wrap it in require_api_key.

    Inspect only — do not open TestClient against app.main here.
    """
    from app.main import app

    routes = [r for r in app.routes if getattr(r, "path", None) == "/version"]
    assert routes, "/version is missing from the assembled app"
    route = routes[0]
    assert "GET" in getattr(route, "methods", set())
    names = []
    dependant = getattr(route, "dependant", None)
    if dependant is not None:
        for dep in dependant.dependencies:
            call = getattr(dep, "call", None)
            if call is not None:
                names.append(getattr(call, "__name__", ""))
    assert "require_api_key" not in names
