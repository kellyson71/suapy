from unittest.mock import Mock

import pytest

from suapy import Suap


@pytest.fixture
def client():
    with Suap(timeout=(1, 2)) as suap:
        suap.sessao.request = Mock()
        yield suap


@pytest.mark.parametrize("ano, mes", [(2026, 0), (2026, 13), (2026, "abc"), (26, 5), (2026, True)])
def test_contracheque_rejeita_ano_ou_mes_invalido(client, ano, mes):
    with pytest.raises(ValueError):
        client.usuario.obter_contracheque_detalhado(ano, mes)
    client.sessao.request.assert_not_called()


@pytest.mark.parametrize("pk", [0, -1, "abc", "../eu", None, True, 1.5])
def test_turma_virtual_rejeita_pk_invalido(client, pk):
    with pytest.raises(ValueError):
        client.ensino.obter_turma_virtual(pk)
    client.sessao.request.assert_not_called()
