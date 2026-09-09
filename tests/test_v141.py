import csv
import io
import json
from unittest.mock import Mock

import pytest

from suapy import Suap, SuapApiError, SuapError, cli
from suapy.modules.ensino import validar_periodo


def http(data, url):
    result = Mock(status_code=200, url=url)
    result.json.return_value = data
    return result


def test_prefix_preserved_for_login_and_endpoints():
    with Suap("https://example.org/suap/") as client:
        client.sessao.request = Mock(side_effect=[
            http({"access": "a", "refresh": "r"}, "https://example.org/suap/api/token/pair"),
            http([], "https://example.org/suap/api/ensino/meu-boletim/2026/2/")])
        client.login("u", "p")
        client.ensino.obter_boletim(2026, 2)
        assert [c.args[1] for c in client.sessao.request.call_args_list] == [
            "https://example.org/suap/api/token/pair",
            "https://example.org/suap/api/ensino/meu-boletim/2026/2/"]


def test_relative_pagination_keeps_own_origin_after_other_request():
    with Suap("https://example.org/suap") as client:
        endpoint = "https://example.org/suap/api/list/"
        client.sessao.request = Mock(side_effect=[
            http({"results": [1], "next": "?page=2"}, endpoint + "?page=1"),
            http({"name": "profile"}, "https://example.org/suap/api/profile/"),
            http({"results": [2], "next": "?page=3"}, endpoint + "?page=2"),
            http({"results": [3], "next": None}, endpoint + "?page=3")])
        page = client.get("/api/list/", params={"page": 1})
        assert json.loads(json.dumps(page)) == {"results": [1], "next": "?page=2"}
        client.get("/api/profile/")
        assert list(client.iterar_resultados(page)) == [1, 2, 3]
        assert client.sessao.request.call_args_list[2].args[1] == endpoint + "?page=2"


def test_external_page_requires_origin_for_query():
    with Suap() as client:
        with pytest.raises(SuapApiError, match="url_origem"):
            list(client.iterar_resultados({"results": [], "next": "?page=2"}))


def test_explicit_origin_and_server_root_links():
    with Suap("https://example.org/suap") as client:
        client.sessao.request = Mock(return_value=http([], "https://example.org/suap/api/list/?page=2"))
        list(client.iterar_resultados({"results": [], "next": "?page=2"},
                                     url_origem="https://example.org/suap/api/list/"))
        assert client.sessao.request.call_args.args[1] == "https://example.org/suap/api/list/?page=2"
        list(client.iterar_resultados({"results": [], "next": "/suap/api/list/?page=2"}))
        assert client.sessao.request.call_args.args[1] == "https://example.org/suap/api/list/?page=2"


@pytest.mark.parametrize("url", ["https://elsewhere.org/", "//elsewhere.org/", "http://example.org/"])
def test_relative_page_cannot_escape_origin(url):
    with Suap("https://example.org/suap") as client:
        client.sessao.request = Mock()
        with pytest.raises(SuapError):
            list(client.iterar_resultados({"results": [], "next": url},
                                         url_origem="https://example.org/suap/api/list/"))
        client.sessao.request.assert_not_called()


@pytest.mark.parametrize("ano,periodo", [(True, 1), (2026, False), (2026.0, 1),
    ("2026/x", 1), (2026, 0), (26, 1), (2026, "../"), (2026, -1)])
def test_period_rejected_before_network(ano, periodo):
    with Suap() as client:
        client.sessao.request = Mock()
        for method in (client.ensino.obter_boletim, client.ensino.obter_turmas_virtuais,
                       client.ensino.obter_diarios):
            with pytest.raises(ValueError):
                method(ano, periodo)
        client.sessao.request.assert_not_called()


def test_period_validation_and_optional_diaries():
    assert validar_periodo("2026", "3") == (2026, 3)
    with Suap() as client:
        with pytest.raises(ValueError):
            client.ensino.obter_diarios(2026)
        with pytest.raises(ValueError):
            client.ensino.obter_mensagens_aluno("bad/status")


def test_csv_union_nested_and_formula():
    rows = [{"disciplina": "=formula", "nota": 8, "obj": {"a": 1}},
            {"disciplina": "Português", "faltas": 2}]
    parsed = list(csv.DictReader(io.StringIO(cli.exportar(rows, "csv"))))
    assert parsed[0]["disciplina"] == "'=formula"
    assert json.loads(parsed[0]["obj"]) == {"a": 1}
    assert parsed[1]["nota"] == ""
    assert json.loads(cli.exportar(rows, "json")) == rows


@pytest.fixture
def mocked_cli(monkeypatch):
    monkeypatch.setattr(cli, "load_session", Mock(return_value="old"))
    monkeypatch.setattr(cli, "save_session", Mock())
    monkeypatch.setattr(cli, "clear_session", Mock())
    def renew(client):
        client.token, client.refresh_token = "a", "rotated"
    monkeypatch.setattr(Suap, "renovar_token", renew)
    def login(client, *args):
        client.token, client.refresh_token = "a", "new"
    monkeypatch.setattr(Suap, "login", login)
    monkeypatch.setattr(cli.console, "input", lambda _: "u")
    monkeypatch.setattr(cli.getpass, "getpass", lambda _: "p")
    monkeypatch.setattr("suapy.modules.ensino.ModuloEnsino.obter_boletim",
                        lambda *args: [{"disciplina": "Matemática", "nota": 8}])


def test_cli_json_stdout(mocked_cli, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["suapy", "boletim", "--ano", "2026", "--periodo", "2", "--formato", "json"])
    cli.main()
    assert json.loads(capsys.readouterr().out) == [{"disciplina": "Matemática", "nota": 8}]
    cli.save_session.assert_called_with("rotated")


@pytest.mark.parametrize("options", [["--sem-sessao"], ["--url-base", "https://example.org/suap"]])
def test_cli_no_persistence(mocked_cli, monkeypatch, options):
    monkeypatch.setattr("sys.argv", ["suapy", "boletim", "--ano", "2026", "--periodo", "2", *options])
    cli.main()
    cli.load_session.assert_not_called()
    cli.save_session.assert_not_called()
    cli.clear_session.assert_not_called()


def test_no_session_interactive_logout_preserves_existing(mocked_cli, monkeypatch):
    monkeypatch.setattr(cli.console, "input", lambda _: "5")
    monkeypatch.setattr("sys.argv", ["suapy", "--sem-sessao"])
    cli.main()
    cli.clear_session.assert_not_called()
    cli.save_session.assert_not_called()


def test_export_file_and_no_overwrite(mocked_cli, monkeypatch, tmp_path):
    path = tmp_path / "boletim.csv"
    monkeypatch.setattr("sys.argv", ["suapy", "boletim", "--ano", "2026", "--periodo", "2",
                                    "--formato", "csv", "--saida", str(path)])
    cli.main()
    original = path.read_bytes()
    assert list(csv.DictReader(io.StringIO(original.decode())))[0]["nota"] == "8"
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    assert path.read_bytes() == original


def test_invalid_cli_period_does_not_authenticate(mocked_cli, monkeypatch):
    monkeypatch.setattr("sys.argv", ["suapy", "boletim", "--ano", "26", "--periodo", "2"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    cli.load_session.assert_not_called()
