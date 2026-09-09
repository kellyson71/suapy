import json
import os
from unittest.mock import Mock

import pytest

from suapy import cli, Suap, SuapAuthError, SuapError


@pytest.fixture
def session_file(tmp_path, monkeypatch):
    path = tmp_path / "session" / "session.json"
    monkeypatch.setattr(cli, "SESSION_FILE", path)
    return path


def test_session_roundtrip_and_logout(session_file):
    assert cli.load_session() is None
    cli.save_session("refresh")
    assert cli.load_session() == "refresh"
    if os.name == "posix":
        assert session_file.stat().st_mode & 0o777 == 0o600
        assert session_file.parent.stat().st_mode & 0o777 == 0o700
    cli.save_session("rotated")
    assert cli.load_session() == "rotated"
    assert len(list(session_file.parent.iterdir())) == 1
    cli.clear_session()
    cli.clear_session()
    assert cli.load_session() is None


@pytest.mark.parametrize("data", ["not json", "[]", "null", '{"refresh": 12}', '{"refresh": ""}'])
def test_invalid_session(session_file, data):
    session_file.parent.mkdir()
    session_file.write_text(data)
    assert cli.load_session() is None


def test_atomic_failure_preserves_session(session_file, monkeypatch):
    cli.save_session("old")
    monkeypatch.setattr(cli.os, "replace", Mock(side_effect=OSError("disk")))
    with pytest.raises(OSError):
        cli.save_session("new")
    assert cli.load_session() == "old"
    assert len(list(session_file.parent.iterdir())) == 1


def test_turn_order():
    rows = [{"turno": t, "horarios": [1]} for t in ["Noite", "Tarde", "Manhã"]]
    assert [h["turno"] for h in cli.ordenar_horarios(rows)] == ["Manhã", "Tarde", "Noite"]


def test_period_order(monkeypatch):
    client = Suap()
    client.ensino.obter_periodos_letivos = Mock(return_value=[
        {"ano_letivo": 2024, "periodo_letivo": 1},
        {"ano_letivo": 2026, "periodo_letivo": 2}])
    monkeypatch.setattr(cli.console, "input", Mock(side_effect=["99", ""]))
    assert cli.escolher_periodo(client) == (2026, 2)
    client.fechar()


def test_menu_logout(session_file, monkeypatch):
    cli.save_session("r")
    with Suap() as client:
        client.refresh_token = "r"
        monkeypatch.setattr(cli.console, "input", lambda _: "5")
        cli.menu(client)
        assert client.refresh_token is None
    assert not session_file.exists()


def test_main_saves_rotated_refresh(session_file, monkeypatch):
    cli.save_session("old")
    def renew(client):
        client.token, client.refresh_token = "access", "new"
    monkeypatch.setattr(Suap, "renovar_token", renew)
    monkeypatch.setattr(cli, "menu", lambda _: None)
    monkeypatch.setattr("sys.argv", ["suapy"])
    cli.main()
    assert cli.load_session() == "new"


def test_network_failure_does_not_delete_session(session_file, monkeypatch):
    cli.save_session("old")
    monkeypatch.setattr(Suap, "renovar_token", Mock(side_effect=SuapError("network")))
    monkeypatch.setattr("sys.argv", ["suapy"])
    with pytest.raises(SystemExit):
        cli.main()
    assert cli.load_session() == "old"
