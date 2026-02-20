from suapy import Suap
import getpass

def main():
    print("🎓 --- SUAPY : Portal do Aluno --- 🎓")
    usuario = input("Sua Matrícula SUAP: ")
    senha = getpass.getpass("Sua Senha: ")

    cliente = Suap()

    try:
        print("\n⏳ Autenticando...")
        cliente.login(usuario, senha)
        
        # 1. Dados Básicos do Aluno
        aluno = cliente.ensino.obter_dados_aluno()
        print(f"\n✅ Sucesso! Bem-vindo(a), {aluno.get('nome_usual')}!")
        print(f"📚 Curso: {aluno.get('curso')} - {aluno.get('campus')}")

        # Pega o ano e semestre atuais para as próximas buscas
        periodos = cliente.ensino.obter_periodos_letivos()
        if not periodos:
            print("Nenhum período letivo encontrado.")
            return
            
        ultimo = periodos[0]
        ano, semestre = ultimo.get('ano_letivo'), ultimo.get('periodo_letivo')
        print(f"\nBuscaremos dados do semestre atual: {ano}.{semestre}")

        # 2. Quando é a próxima prova?
        print("\n📅 Suas Próximas Avaliações:")
        avaliacoes = cliente.ensino.obter_proximas_avaliacoes()
        if avaliacoes:
            for aval in avaliacoes:
                print(f" ⚠️  {aval.get('data_avaliacao')} - {aval.get('disciplina')}")
        else:
            print(" Nenhuma avaliação próxima cadastrada! 🎉")

        # 3. Faltas e Diários
        print("\n📋 Suas Matérias e Faltas no Semestre (Cuidado!):")
        diarios = cliente.ensino.obter_diarios(ano, semestre)
        if diarios:
            for diario in diarios:
                disciplina = diario.get('disciplina')
                faltas = diario.get('numero_faltas', 0)
                situacao = diario.get('situacao')
                
                # Destaca se tiver muitas faltas (ex: mais de 10)
                alerta = "🚨" if faltas > 10 else "🟢"
                print(f" {alerta} {disciplina}")
                print(f"    - Faltas: {faltas} | Situação: {situacao}")
        else:
            print(" Nenhum diário/matéria encontrado para este semestre.")

    except Exception as e:
        print(f"\n❌ [ERRO DE EXECUÇÃO] {e}")

if __name__ == "__main__":
    main()
