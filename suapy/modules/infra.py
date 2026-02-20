class ModuloInfraestrutura:
    def __init__(self, cliente):
        self.cliente = cliente

    def obter_campi(self):
        """Obtém a lista de campi ou unidades organizacionais do IF."""
        return self.cliente.get("/api/rh/unidades-organizacionais/")

    def obter_setores(self):
        """Listagem de setores da instituição."""
        return self.cliente.get("/api/rh/setores/")
