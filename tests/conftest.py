import sys
from pathlib import Path
from typing import Optional

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from toolkit_harness.loader import (
    load_toolkit_module,
    instantiate_tools,
    MockEventEmitter,
    mock_user,
    call_kwargs,
)

TOOLS_ROOT = REPO_ROOT / "tools"


@pytest.fixture
def load_tool():
    """load_tool("gitlab/gitlab.py", valve_overrides={...}) -> Tools() instance"""

    def _load(relative_path: str, valve_overrides: Optional[dict] = None):
        module = load_toolkit_module(TOOLS_ROOT / relative_path)
        return instantiate_tools(module, valve_overrides)

    return _load


@pytest.fixture
def emitter():
    return MockEventEmitter()


@pytest.fixture
def user():
    return mock_user()


@pytest.fixture
def kwargs_for():
    return call_kwargs