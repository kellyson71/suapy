from unittest.mock import Mock

import pytest
import requests

from suapy import Suap, SuapApiError, SuapAuthError, SuapError


def response(status=200, data=None):
    result = Mock(status_code=status)
    result.json.return_value = data
    return result


@pytest.fixture
def client():
    with Suap(timeout=(1, 2)) as suap:
        suap.sessao.request = Mock()
        yield suap


def test_login(client):
    client.sessao.request.return_value = response(data={"access": "access", "refresh": "refresh"})
    assert client.login("user", "password")
    assert client.sessao.headers["Authorization"] == "Bearer access"
    assert client.refresh_token == "refresh"
    kwargs = client.sessao.request.call_args.kwargs
    assert kwargs["timeout"] == (1, 2)
    assert kwargs["verify"] is True
    assert kwargs["allow_redirects"] is False


@pytest.mark.parametrize("data", [None, [], {}, {"access": "a"},
                                     {"access": "", "refresh": "r"},
                                     {"access": "a", "refresh": 123}])
def test_invalid_login(client, data):
    client.sessao.request.return_value = response(data=data)
    with pytest.raises(SuapAuthError):
        client.login("user", "password")
    assert client.token is None
    assert "Authorization" not in client.sessao.headers


def test_refresh_and_retry(client):
    client.refresh_token = "old"
    client.sessao.request.side_effect = [response(401),
        response(data={"access": "new", "refresh": "rotated"}), response(data={"ok": True})]
    assert client.get("/api/test") == {"ok": True}
    assert client.refresh_token == "rotated"
    assert client.sessao.request.call_count == 3


def test_refresh_failure_keeps_auth_error(client):
    client.refresh_token = "old"
    client.sessao.request.side_effect = [response(401), response(401)]
    with pytest.raises(SuapAuthError):
        client.get("/api/test")
    assert client.sessao.request.call_count == 2


def test_only_one_retry(client):
    client.refresh_token = "old"
    client.sessao.request.side_effect = [response(401), response(data={"access": "new"}), response(401)]
    with pytest.raises(SuapAuthError):
        client.get("/api/test")
    assert client.sessao.request.call_count == 3
    assert client.refresh_token == "old"


@pytest.mark.parametrize("status,error", [(401, SuapAuthError), (403, SuapAuthError),
                                           (500, SuapApiError), (302, SuapApiError)])
def test_http_errors(client, status, error):
    client.sessao.request.return_value = response(status)
    with pytest.raises(error):
        client.get("/api/test")


@pytest.mark.parametrize("error", [requests.Timeout, requests.ConnectionError])
def test_network_errors(client, error):
    client.sessao.request.side_effect = error("network")
    with pytest.raises(SuapError) as caught:
        client.login("user", "password")
    assert isinstance(caught.value.__cause__, error)


def test_bad_json(client):
    result = response()
    result.json.side_effect = ValueError("bad json")
    client.sessao.request.return_value = result
    with pytest.raises(SuapApiError):
        client.get("/api/test")


def test_empty_response(client):
    client.sessao.request.return_value = response(204)
    assert client.post("/api/test") is None


def test_pagination(client):
    client.sessao.request.return_value = response(data={"results": [2], "next": None})
    assert list(client.iterar_resultados({"results": [1], "next": "/api/list?page=2"})) == [1, 2]
    assert list(client.iterar_resultados([3])) == [3]


@pytest.mark.parametrize("url", ["https://example.com/api", "//example.com/api",
                                  "http://suap.ifrn.edu.br/api"])
def test_external_pagination_blocked(client, url):
    with pytest.raises(SuapError):
        list(client.iterar_resultados({"results": [], "next": url}))
    client.sessao.request.assert_not_called()


def test_pagination_cycle(client):
    page = {"results": [], "next": "/api/list?page=2"}
    client.sessao.request.return_value = response(data=page)
    with pytest.raises(SuapApiError, match="Ciclo"):
        list(client.iterar_resultados(page))
    assert client.sessao.request.call_count == 1


def test_context_and_logout():
    with Suap() as client:
        client.sessao.close = Mock()
        client.token = client.refresh_token = "test"
        client._atualizar_cabecalho_auth()
        client.logout()
        assert client.token is client.refresh_token is None
        assert "Authorization" not in client.sessao.headers
    client.sessao.close.assert_called_once()
