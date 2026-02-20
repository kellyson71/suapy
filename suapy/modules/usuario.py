class ModuloUsuario:
    def __init__(self, cliente):
        self.cliente = cliente

    def obter_meus_dados_resumidos(self):
        """Obtém os dados básicos do usuário logado."""
        return self.cliente.get("/api/rh/eu/")

    def obter_meus_dados(self):
        """Obtém o perfil pessoal completo."""
        return self.cliente.get("/api/rh/meus-dados/")

    def obter_historico_funcional(self):
        """Obtém o histórico funcional."""
        return self.cliente.get("/api/rh/meu-historico-funcional/")

    def obter_contracheques(self):
        """Obtém a lista de contracheques disponíveis."""
        return self.cliente.get("/api/rh/meus-contracheques/")

    def obter_contracheque_detalhado(self, ano, mes):
        """Obtém detalhes de um contracheque específico por ano e mês."""
        return self.cliente.get(f"/api/rh/meu-contracheque/{ano}/{mes}/")
