import importlib.util
from pathlib import Path
from unittest.mock import Mock


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_oidc_only_mints_without_upload(monkeypatch, capsys):
    mod = load("check_pypi_auth")
    monkeypatch.setenv("ACTIONS_ID_TOKEN_REQUEST_URL", "https://runner.example/token?job=1")
    monkeypatch.setenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "runner-secret")
    calls = Mock(side_effect=[{"value": "oidc-secret"}, {"token": "pypi-secret"}])
    monkeypatch.setattr(mod, "request_json", calls)
    assert mod.main() == 0
    assert calls.call_count == 2
    assert calls.call_args_list[1].args[0].full_url == "https://pypi.org/_/oidc/mint-token"
    assert "secret" not in capsys.readouterr().out


def test_live_missing_credentials(monkeypatch):
    monkeypatch.delenv("SUAP_TEST_USERNAME", raising=False)
    monkeypatch.delenv("SUAP_TEST_PASSWORD", raising=False)
    mod = load("test_live")
    assert mod.main() == 2
