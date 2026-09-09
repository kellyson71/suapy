class SuapError(Exception):
    """Exceção base da biblioteca suapy."""
    pass

class SuapAuthError(SuapError):
    """Erro de autenticação (login ou token inválido)."""
    pass

class SuapApiError(SuapError):
    """Erro retornado pela API do SUAP."""
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response
