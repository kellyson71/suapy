class ModuloEnsino:
    """Módulo responsável por dados acadêmicos e estudantis."""
    def __init__(self, cliente):
        self.cliente = cliente

    def obter_dados_aluno(self):
        """Obtém os dados institucionais do aluno."""
        return self.cliente.get("/api/ensino/meus-dados-aluno/")

    def obter_boletim(self, ano, periodo):
        """Obtém o boletim do aluno para um ano e semestre letivo específicos."""
        return self.cliente.get(f"/api/ensino/meu-boletim/{ano}/{periodo}/")

    def obter_horario_aulas(self):
        """Obtém o horário de aulas (extraído dos dados do aluno ou turmas)."""
        dados = self.obter_dados_aluno()
        return dados.get("horario_aula") if dados else None

    def obter_periodos_letivos(self):
        """Obtém o histórico de períodos letivos do aluno."""
        return self.cliente.get("/api/ensino/meus-periodos-letivos/")

    def obter_diarios(self, ano=None, periodo=None):
        """
        Lista as disciplinas/diários do semestre (Nota: Frequentemente restrito a professores).
        Para alunos, recomenda-se usar obter_turmas_virtuais ou obter_boletim.
        """
        if ano and periodo:
            return self.cliente.get(f"/api/ensino/meus-diarios/{ano}/{periodo}/")
        return self.cliente.get("/api/ensino/meus-diarios/")
        
    def obter_turmas_virtuais(self, ano, periodo):
        """Obtém as turmas virtuais (materiais de aula, professores, participantes)."""
        return self.cliente.get(f"/api/ensino/minhas-turmas-virtuais/{ano}/{periodo}/")

    def obter_turma_virtual(self, pk):
        """Obtém detalhes de uma turma virtual específica."""
        return self.cliente.get(f"/api/ensino/minha-turma-virtual/{pk}/")
        
    def obter_proximas_avaliacoes(self):
        """Lista as próximas provas, trabalhos ou avaliações cadastradas."""
        return self.cliente.get("/api/ensino/minhas-proximas-avaliacoes/")
        
    def obter_mensagens_aluno(self, status='nao_lidas'):
        """
        Lista as mensagens na caixa de entrada do SUAP.
        status: 'nao_lidas', 'lidas' ou 'todas'
        """
        return self.cliente.get(f"/api/ensino/mensagens/entrada/{status}/")

    def obter_requisitos_conclusao(self):
        """Verifica os requisitos para conclusão do curso atual (horas formativas e disciplinas)."""
        return self.cliente.get("/api/ensino/requisitos-conclusao/")

    def obter_eventos(self):
        """Obtém todos os eventos institucionais ativos e deferidos."""
        return self.cliente.get("/api/midia/eventos/ativos-deferidos/")
