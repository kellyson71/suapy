"""Exemplo executável; exige uma conta SUAP do IFRN."""
from getpass import getpass
from suapy import Suap, SuapError


def main():
    try:
        with Suap() as cliente:
            cliente.login(input("Matrícula: "), getpass("Senha: "))
            periodos = list(cliente.iterar_resultados(cliente.ensino.obter_periodos_letivos()))
            if not periodos:
                print("Nenhum período disponível.")
                return
            atual = max(periodos, key=lambda p: (int(p["ano_letivo"]), int(p["periodo_letivo"])))
            boletim = cliente.ensino.obter_boletim(atual["ano_letivo"], atual["periodo_letivo"])
            for disciplina in cliente.iterar_resultados(boletim):
                print(disciplina.get("disciplina"), disciplina.get("numero_faltas"),
                      disciplina.get("media_final_disciplina"))
    except SuapError as erro:
        print(f"Erro: {erro}")


if __name__ == "__main__":
    main()
