class ModuloPesquisaExtensao:
    def __init__(self, cliente):
        self.cliente = cliente

    def obter_projetos_pesquisa(self):
        """Lista os projetos de pesquisa da instituição."""
        return self.cliente.get("/api/pesquisa/projetos/")

    def obter_projetos_extensao(self):
        """Lista os projetos de extensão ativos."""
        return self.cliente.get("/api/extensao/projetos/")
