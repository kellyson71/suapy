"""Teste opt-in de consultas reais. Não imprime nem persiste dados da conta."""
import os

from suapy import Suap, SuapError


def check_live():
    username = os.environ.get("SUAP_TEST_USERNAME")
    password = os.environ.get("SUAP_TEST_PASSWORD")
    if not username or not password:
        print("PENDENTE: defina SUAP_TEST_USERNAME e SUAP_TEST_PASSWORD localmente.")
        return 2
    with Suap(url_base=os.environ.get("SUAP_TEST_URL", "https://suap.ifrn.edu.br")) as client:
        client.login(username, password)
        client.renovar_token()
        aluno = client.ensino.obter_dados_aluno()
        if not isinstance(aluno, dict) or not aluno:
            raise ValueError("Formato inesperado nos dados do aluno.")
        periodos = list(client.iterar_resultados(client.ensino.obter_periodos_letivos()))
        if not periodos:
            print("INCOMPLETO: conta sem períodos; boletim e turmas não foram testados.")
            return 2
        atual = max(periodos, key=lambda p: (int(p["ano_letivo"]), int(p["periodo_letivo"])))
        ano, periodo = atual["ano_letivo"], atual["periodo_letivo"]
        for nome, dados, campos in (
            ("boletim", client.ensino.obter_boletim(ano, periodo), {"disciplina", "numero_faltas"}),
            ("turmas", client.ensino.obter_turmas_virtuais(ano, periodo), {"descricao", "horarios_de_aula"}),
            ("avaliacoes", client.ensino.obter_proximas_avaliacoes(), {"disciplina", "data_avaliacao"}),
        ):
            registros = list(client.iterar_resultados(dados))
            if not all(isinstance(r, dict) and campos <= r.keys() for r in registros):
                raise ValueError("Campos inesperados: " + nome)
            print(nome + (": consulta e campos validados." if registros
                          else ": consulta válida, sem registros para validar campos."))
    print("Consultas concluídas. Nenhum dado pessoal foi impresso ou salvo.")
    return 0


def main():
    try:
        return check_live()
    except (SuapError, ValueError, KeyError, TypeError):
        print("FALHOU: verifique a conta de teste, permissões, conectividade e contrato da API.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
