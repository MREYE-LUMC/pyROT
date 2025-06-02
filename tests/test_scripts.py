from __future__ import annotations

import logging
import sys
from importlib import import_module
from importlib.util import find_spec, module_from_spec, spec_from_loader

import pytest


@pytest.fixture(autouse=True)
def mock_dotnet_imports(monkeypatch):
    try:
        import_module("clr")
    except RuntimeError:

        class MockModule:
            def __getattr__(self, name):
                return lambda *args, **kwargs: None  # noqa: ARG005

        mock_module = MockModule()

        monkeypatch.setitem(sys.modules, "clr", mock_module)
        monkeypatch.setitem(sys.modules, "System.Windows.Forms", mock_module)


@pytest.fixture
def scripts_cwd(monkeypatch, request):
    scripts_path = request.path.parent.parent / "scripts"

    assert scripts_path.exists()

    monkeypatch.chdir(scripts_path)

    return scripts_path


def test_common_updates_sys_path(monkeypatch, scripts_cwd):
    root = str(scripts_cwd.parent)

    # Remove the root directory from sys.path and add the current working directory
    # sys.path.remove doesn't always work, because root may be present in sys.path multiple times
    sys_path = [p for p in sys.path if p != root]

    # Remove pyrot from sys.path and sys.modules
    monkeypatch.setattr(sys, "path", sys_path)
    monkeypatch.delitem(sys.modules, "pyrot", raising=False)

    # Add the scripts working directory to sys.path for importing __common__
    monkeypatch.syspath_prepend(scripts_cwd)

    assert root not in sys.path
    assert find_spec("pyrot") is None

    import_module("__common__")

    assert root in sys.path
    assert find_spec("pyrot") is not None


def test_common_loads_customization(caplog, monkeypatch, scripts_cwd):
    caplog.set_level(logging.DEBUG)

    # Add the scripts working directory to sys.path for importing __common__
    monkeypatch.syspath_prepend(scripts_cwd)

    # Create a dummy customization module
    monkeypatch.setitem(
        sys.modules,
        "customization",
        module_from_spec(spec_from_loader("customization", loader=None, origin="test")),
    )

    # Remove the __common__ module from sys.modules to force re-import
    monkeypatch.delitem(sys.modules, "__common__", raising=False)

    import_module("__common__")

    assert "Customization loaded from test" in caplog.text
