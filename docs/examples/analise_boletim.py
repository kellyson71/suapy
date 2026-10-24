from getpass import getpass
from suapy import Suap, SuapError, para_dataframe

try:
    with Suap() as suap:
        suap.login(input("Matrícula: "), getpass("Senha: "))
        periodos = list(suap.iterar_resultados(
            suap.ensino.obter_periodos_letivos()
        ))
        if not periodos:
            print("Nenhum período disponível.")
        else:
            atual = max(periodos, key=lambda p: (
                int(p["ano_letivo"]), int(p["periodo_letivo"])
            ))
            resposta = suap.ensino.obter_boletim(
                atual["ano_letivo"], atual["periodo_letivo"]
            )
            registros = list(suap.iterar_resultados(resposta))
            if not registros:
                print("Nenhuma disciplina disponível neste período.")
            else:
                df = para_dataframe(registros)
                tabela = df.reindex(columns=[
                    "disciplina", "media_final_disciplina", "numero_faltas"
                ]).rename(columns={
                    "disciplina": "Disciplina",
                    "media_final_disciplina": "Média",
                    "numero_faltas": "Faltas",
                })
                print(tabela.to_string(index=False, na_rep="—"))
                tabela.to_csv("boletim.csv", index=False, mode="x")
                print("Arquivo criado: boletim.csv")
except FileExistsError:
    print("boletim.csv já existe. Escolha outro nome para exportar.")
except SuapError as erro:
    print(f"Consulta indisponível: {erro}")
