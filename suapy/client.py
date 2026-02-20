import requests
from .exceptions import SuapAuthError, SuapApiError, SuapError

from .modules.usuario import ModuloUsuario
from .modules.ensino import ModuloEnsino
from .modules.infra import ModuloInfraestrutura
from .modules.projects import ModuloPesquisaExtensao

class Suap:
    """
    Cliente principal para integração com a API do SUAP.
    
    Permite autenticação via token JWT e oferece acesso organizado
    aos módulos da plataforma (Ensino, Usuário, RH, Infraestrutura).
    """
    def __init__(self, url_base="https://suap.ifrn.edu.br", verificar_ssl=True):
        self.url_base = url_base.rstrip('/')
        self.verificar_ssl = verificar_ssl
        self.sessao = requests.Session()
        self.token = None
        self.refresh_token = None
        
        # Módulos traduzidos e expostos
        self.usuario = ModuloUsuario(self)
        self.ensino = ModuloEnsino(self)
        self.infraestrutura = ModuloInfraestrutura(self)
        self.pesquisa_extensao = ModuloPesquisaExtensao(self)

    def login(self, usuario, senha):
        """
        Realiza a autenticação e guarda o token de acesso.
        """
        endpoint = f"{self.url_base}/api/token/pair"
        dados = {
            "username": usuario,
            "password": senha
        }
        
        try:
            resposta = self.sessao.post(endpoint, json=dados, verify=self.verificar_ssl)
            resposta.raise_for_status()
            tokens = resposta.json()
            self.token = tokens.get("access")
            self.refresh_token = tokens.get("refresh")
            self._atualizar_cabecalho_auth()
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise SuapAuthError("Usuário ou senha inválidos.")
            raise SuapApiError(f"Erro na autenticação: {e}", status_code=e.response.status_code)
        except Exception as e:
            raise SuapError(f"Erro inesperado no login: {e}")

    def renovar_token(self):
        """
        Renova o token de acesso (access token) se estiver expirado.
        """
        if not self.refresh_token:
            raise SuapAuthError("Nenhum refresh token disponível para renovação.")

        endpoint = f"{self.url_base}/api/token/refresh"
        try:
            resposta = self.sessao.post(endpoint, json={"refresh": self.refresh_token}, verify=self.verificar_ssl)
            resposta.raise_for_status()
            self.token = resposta.json().get("access")
            self._atualizar_cabecalho_auth()
            return True
        except Exception as e:
            raise SuapAuthError(f"Falha ao renovar o token: {e}")

    def _atualizar_cabecalho_auth(self):
        if self.token:
            self.sessao.headers.update({"Authorization": f"Bearer {self.token}"})

    def get(self, caminho, params=None):
        return self._requisicao("GET", caminho, params=params)

    def post(self, caminho, dados=None, json=None):
        return self._requisicao("POST", caminho, data=dados, json=json)

    def _requisicao(self, metodo, caminho, **kwargs):
        url = f"{self.url_base}/{caminho.lstrip('/')}"
        try:
            resposta = self.sessao.request(metodo, url, verify=self.verificar_ssl, **kwargs)
            if resposta.status_code == 401 and self.refresh_token:
                self.renovar_token()
                resposta = self.sessao.request(metodo, url, verify=self.verificar_ssl, **kwargs)
            
            resposta.raise_for_status()
            return resposta.json()
        except requests.exceptions.HTTPError as e:
            raise SuapApiError(f"Erro na API ({metodo} {caminho}): {e}", 
                               status_code=e.response.status_code, 
                               response=e.response)
        except Exception as e:
            raise SuapError(f"Falha ao realizar requisição: {e}")
