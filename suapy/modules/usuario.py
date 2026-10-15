from .ensino import validar_periodo


class ModuloUsuario:
    """Módulo de dados pessoais e funcionais do usuário autenticado."""

    def __init__(self, cliente):
        self.cliente = cliente

    def obter_meus_dados_resumidos(self):
        """Obtém os dados básicos do usuário logado."""
        return self.cliente.get("/api/rh/eu/")

    def obter_meus_dados(self):
        """Obtém o perfil pessoal completo."""
        return self.cliente.get("/api/rh/meus-dados/")

    def obter_meus_vinculos(self):
        """Lista os vínculos (aluno, servidor) da conta; a resposta é paginada."""
        return self.cliente.get("/api/rh/meus-vinculos/")

    def obter_historico_funcional(self):
        """Obtém o histórico funcional."""
        return self.cliente.get("/api/rh/meu-historico-funcional/")

    def obter_contracheques(self):
        """Obtém a lista de contracheques disponíveis."""
        return self.cliente.get("/api/rh/meus-contracheques/")

    def obter_contracheque_detalhado(self, ano, mes):
        """Obtém detalhes de um contracheque específico por ano e mês."""
        ano, mes = validar_periodo(ano, mes, nome_periodo="mes")
        if mes > 12:
            raise ValueError("mes deve estar entre 1 e 12.")
        return self.cliente.get(f"/api/rh/meu-contracheque/{ano}/{mes}/")
