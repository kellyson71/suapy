from unittest.mock import Mock

import pytest

import suapy
from suapy import Perfil, Suap, SuapApiError, SuapAuthError
from suapy.perfil import montar_perfil

BASE = "https://suap.ifrn.edu.br"

EU = {
    "identificacao": "20231014040001", "nome_usual": "Ana Souza", "nome": "Ana Maria Souza",
    "email_academico": "ana.souza@escolar.ifrn.edu.br", "email": "ana@exemplo.com",
    "campus": "PF", "tipo_usuario": "Aluno", "foto": "/media/fotos/ana.jpg",
}
VINCULO_ALUNO = {
    "id": 1, "identificador": "20231014040001", "tipo": "Aluno", "campus": "PF",
    "estrangeiro": False,
    "detalhamento": {"modalidade": "Integrado", "nivel_ensino": "Médio",
                     "curso": "Informática", "ativo": True},
}
VINCULO_SERVIDOR = {
    "id": 2, "identificador": "1234567", "tipo": "Servidor", "campus": "PF",
    "estrangeiro": False, "detalhamento": {"cargo": "Professor", "categoria": "Docente"},
}


def http(data, url, status=200):
    result = Mock(status_code=status, url=url)
    result.json.return_value = data
    return result


def test_montar_perfil_normaliza_campos():
    perfil = montar_perfil(EU, [VINCULO_SERVIDOR, VINCULO_ALUNO])
    assert perfil.matricula == "20231014040001"
    assert perfil.nome == "Ana Souza"
    assert perfil.email == "ana.souza@escolar.ifrn.edu.br"
    assert perfil.aluno_ativo
    assert perfil.vinculo_aluno_ativo.curso == "Informática"
    assert not perfil.vinculos[0].de_aluno


def test_perfil_sem_vinculo_de_aluno_ativo():
    inativo = {**VINCULO_ALUNO, "detalhamento": {**VINCULO_ALUNO["detalhamento"], "ativo": False}}
    assert not montar_perfil(EU, [inativo]).aluno_ativo
    assert not montar_perfil(EU, [VINCULO_SERVIDOR]).aluno_ativo
    assert not montar_perfil(EU).aluno_ativo


def test_nome_e_email_usam_alternativas():
    perfil = montar_perfil({"identificacao": "1", "nome_usual": " ", "nome": "Ana",
                            "email_academico": "", "email": "ana@exemplo.com"})
    assert (perfil.nome, perfil.email, perfil.campus) == ("Ana", "ana@exemplo.com", "")


@pytest.mark.parametrize("eu", [None, [], {}, {"identificacao": ""}])
def test_dados_sem_identificacao(eu):
    with pytest.raises(SuapApiError):
        montar_perfil(eu)


def test_vinculo_invalido():
    with pytest.raises(SuapApiError):
        montar_perfil(EU, ["texto"])


def test_obter_perfil_percorre_paginas_de_vinculos():
    with Suap() as suap:
        suap.sessao.request = Mock(side_effect=[
            http(EU, BASE + "/api/rh/eu/"),
            http({"results": [VINCULO_SERVIDOR], "next": "?page=2"}, BASE + "/api/rh/meus-vinculos/"),
            http({"results": [VINCULO_ALUNO], "next": None}, BASE + "/api/rh/meus-vinculos/?page=2"),
        ])
        perfil = suap.obter_perfil()
    assert isinstance(perfil, Perfil)
    assert perfil.aluno_ativo and len(perfil.vinculos) == 2
    assert [c.args[1] for c in suap.sessao.request.call_args_list] == [
        BASE + "/api/rh/eu/", BASE + "/api/rh/meus-vinculos/", BASE + "/api/rh/meus-vinculos/?page=2"]


def test_autenticar_faz_login_e_fecha(monkeypatch):
    sessao = Mock()
    sessao.headers = {}
    sessao.request.side_effect = [
        http({"access": "a", "refresh": "r"}, BASE + "/api/token/pair"),
        http(EU, BASE + "/api/rh/eu/"),
        http({"results": [VINCULO_ALUNO], "next": None}, BASE + "/api/rh/meus-vinculos/"),
    ]
    monkeypatch.setattr("suapy.client.requests.Session", lambda: sessao)
    perfil = suapy.autenticar("20231014040001", "senha")
    assert perfil.matricula == "20231014040001" and perfil.aluno_ativo
    sessao.close.assert_called_once()


def test_autenticar_com_senha_errada(monkeypatch):
    sessao = Mock()
    sessao.headers = {}
    sessao.request.return_value = http({"detail": "inválido"}, BASE + "/api/token/pair", status=401)
    monkeypatch.setattr("suapy.client.requests.Session", lambda: sessao)
    with pytest.raises(SuapAuthError):
        suapy.autenticar("20231014040001", "errada")
    sessao.close.assert_called_once()
