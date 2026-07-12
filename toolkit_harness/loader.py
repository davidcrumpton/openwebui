"""Dynamic loader for OpenWebUI-style single-file tool modules."""
from __future__ import annotations

import importlib.util
import inspect
import sys
import types
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock


def load_toolkit_module(path: str | Path) -> types.ModuleType:
    """Load a tool .py file as a module by path.

    Temporarily puts the tool's own directory on sys.path so sibling
    imports inside that tool dir (e.g. a local helper module) resolve.
    """
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    mod_name = f"_toolkit_{path.parent.name}_{path.stem}".replace("-", "_")
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create spec for {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module

    tool_dir = str(path.parent)
    inserted = tool_dir not in sys.path
    if inserted:
        sys.path.insert(0, tool_dir)
    try:
        spec.loader.exec_module(module)
    finally:
        if inserted:
            sys.path.remove(tool_dir)
    return module


def get_tools_class(module: types.ModuleType) -> type:
    if not hasattr(module, "Tools"):
        raise AttributeError(f"{module.__name__} has no Tools class")
    return module.Tools


def instantiate_tools(module: types.ModuleType, valve_overrides: Optional[Dict[str, Any]] = None):
    instance = get_tools_class(module)()
    if valve_overrides and hasattr(instance, "valves"):
        for key, value in valve_overrides.items():
            setattr(instance.valves, key, value)
    return instance


class MockEventEmitter:
    """Captures __event_emitter__ calls instead of no-op'ing them."""

    def __init__(self) -> None:
        self.events: list[dict] = []

    async def __call__(self, event: dict) -> None:
        self.events.append(event)

    def of_type(self, t: str) -> list[dict]:
        return [e for e in self.events if e.get("type") == t]


def mock_user(id: str = "test-user-id", name: str = "Test User", role: str = "admin", **extra) -> dict:
    return {"id": id, "name": name, "role": role, **extra}


def call_kwargs(instance, method_name: str, **explicit) -> dict:
    """Build kwargs for a Tools method call, injecting OpenWebUI's dunder
    params only if the method signature actually declares them."""
    method = getattr(instance, method_name)
    sig = inspect.signature(method)
    injectable = {
        "__user__": explicit.pop("__user__", None) or mock_user(),
        "__event_emitter__": explicit.pop("__event_emitter__", None) or MockEventEmitter(),
        "__event_call__": explicit.pop("__event_call__", None) or AsyncMock(return_value=None),
        "__metadata__": explicit.pop("__metadata__", None) or {},
        "__oauth_token__": explicit.pop("__oauth_token__", None),
        "__files__": explicit.pop("__files__", None) or [],
        "__messages__": explicit.pop("__messages__", None) or [],
    }
    kwargs = dict(explicit)
    for name, value in injectable.items():
        if name in sig.parameters:
            kwargs[name] = value
    return kwargs