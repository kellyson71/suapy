"""Cliente HTTP do SUAP."""

from urllib.parse import urljoin, urlsplit

import requests

from .exceptions import SuapAuthError, SuapApiError, SuapError
from .modules.usuario import ModuloUsuario
from .modules.ensino import ModuloEnsino
from .modules.infra import ModuloInfraestrutura
from .modules.projects import ModuloPesquisaExtensao


class _Pagina(dict):
    """Dicionário JSON com a URL de origem, fora dos campos da API."""

    def __init__(self, dados, url):
        super().__init__(dados)
        self.url_origem = url


class Suap:
    """Cliente da API. O timeout limita conexão e leitura, em segundos."""

    def __init__(self, url_base="https://suap.ifrn.edu.br", verificar_ssl=True,
                 timeout=(5, 30)):
        self.url_base = url_base.rstrip('/')
        base = urlsplit(self.url_base)
        if (base.scheme not in ("http", "https") or not base.netloc
                or base.username or base.password or base.query or base.fragment):
            raise ValueError("url_base deve ser uma URL HTTP(S), sem credenciais, query ou fragmento.")
        self.verificar_ssl = verificar_ssl
        self.timeout = timeout
        self.sessao = requests.Session()
        self.token = None
        self.refresh_token = None
        self.usuario = ModuloUsuario(self)
        self.ensino = ModuloEnsino(self)
        self.infraestrutura = ModuloInfraestrutura(self)
        self.pesquisa_extensao = ModuloPesquisaExtensao(self)

    def fechar(self):
        """Libera conexões HTTP; não revoga tokens no servidor."""
        self.sessao.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.fechar()

    def logout(self):
        """Remove credenciais da memória; não revoga tokens no servidor."""
        self.token = self.refresh_token = None
        self.sessao.headers.pop("Authorization", None)

    def _url(self, caminho):
        if not isinstance(caminho, str):
            raise ValueError("O caminho deve ser uma string.")
        partes = urlsplit(caminho)
        url = (caminho if partes.scheme or partes.netloc
               else urljoin(self.url_base + '/', caminho.lstrip('/')))
        base, destino = urlsplit(self.url_base), urlsplit(url)
        if ((base.scheme, base.netloc) != (destino.scheme, destino.netloc)
                or destino.username or destino.password):
            raise SuapError("A URL deve pertencer à mesma origem do SUAP configurado.")
        return url

    def _enviar(self, metodo, caminho, **kwargs):
        try:
            return self.sessao.request(
                metodo, self._url(caminho), verify=self.verificar_ssl,
                timeout=self.timeout, allow_redirects=False, **kwargs)
        except requests.exceptions.Timeout as exc:
            raise SuapError("Tempo limite excedido ao acessar o SUAP.") from exc
        except requests.exceptions.RequestException as exc:
            raise SuapError("Falha de conexão com o SUAP.") from exc

    @staticmethod
    def _decodificar(resposta):
        if resposta.status_code in (401, 403):
            raise SuapAuthError("Acesso negado: verifique a sessão e as permissões da conta.")
        if not 200 <= resposta.status_code < 300:
            raise SuapApiError("Erro na API do SUAP (HTTP {}).".format(resposta.status_code),
                               status_code=resposta.status_code, response=resposta)
        if resposta.status_code == 204:
            return None
        try:
            return resposta.json()
        except ValueError as exc:
            raise SuapApiError("A API não retornou JSON válido.",
                               status_code=resposta.status_code, response=resposta) from exc

    @staticmethod
    def _validar_tokens(dados, exigir_refresh=False):
        if not isinstance(dados, dict):
            raise SuapAuthError("Resposta de autenticação inválida.")
        for chave in ("access", "refresh") if exigir_refresh else ("access",):
            if not isinstance(dados.get(chave), str) or not dados[chave].strip():
                raise SuapAuthError("Resposta de autenticação sem token válido.")
        if "refresh" in dados and (not isinstance(dados["refresh"], str)
                                   or not dados["refresh"].strip()):
            raise SuapAuthError("Refresh token inválido.")

    def login(self, usuario, senha):
        """Autentica uma conta e guarda seus tokens em memória."""
        self.logout()
        dados = self._decodificar(self._enviar(
            "POST", "/api/token/pair", json={"username": usuario, "password": senha}))
        self._validar_tokens(dados, exigir_refresh=True)
        self.token, self.refresh_token = dados["access"], dados["refresh"]
        self._atualizar_cabecalho_auth()
        return True

    def renovar_token(self):
        """Renova o acesso e preserva eventual rotação do refresh token."""
        if not self.refresh_token:
            raise SuapAuthError("Nenhum refresh token disponível para renovação.")
        dados = self._decodificar(self._enviar(
            "POST", "/api/token/refresh", json={"refresh": self.refresh_token}))
        self._validar_tokens(dados)
        self.token = dados["access"]
        self.refresh_token = dados.get("refresh", self.refresh_token)
        self._atualizar_cabecalho_auth()
        return True

    def _atualizar_cabecalho_auth(self):
        if self.token:
            self.sessao.headers.update({"Authorization": "Bearer " + self.token})

    def get(self, caminho, params=None):
        return self._requisicao("GET", caminho, params=params)

    def post(self, caminho, dados=None, json=None):
        return self._requisicao("POST", caminho, data=dados, json=json)

    def _requisicao(self, metodo, caminho, **kwargs):
        resposta = self._enviar(metodo, caminho, **kwargs)
        if resposta.status_code == 401 and self.refresh_token:
            self.renovar_token()
            resposta = self._enviar(metodo, caminho, **kwargs)
        dados = self._decodificar(resposta)
        if isinstance(dados, dict) and isinstance(dados.get("results"), list):
            # Use a URL preparada pelo requests, incluindo parâmetros de consulta.
            origem = resposta.url if isinstance(resposta.url, str) else self._url(caminho)
            return _Pagina(dados, origem)
        return dados

    def iterar_resultados(self, resposta, url_origem=None):
        """Itera uma lista ou todas as páginas de um envelope results/next.

        Recebe o retorno de um método de consulta. Os métodos existentes
        continuam devolvendo o JSON original, sem normalização implícita.
        """
        origem = url_origem or getattr(resposta, "url_origem", None)
        visitadas = {self._url(origem)} if origem else set()
        while True:
            if isinstance(resposta, list):
                yield from resposta
                return
            if not isinstance(resposta, dict) or not isinstance(resposta.get("results"), list):
                raise SuapApiError("Esperada uma lista ou uma resposta com results.")
            yield from resposta["results"]
            proxima = resposta.get("next")
            if not proxima:
                return
            if not isinstance(proxima, str):
                raise SuapApiError("Link de paginação inválido.")
            if origem:
                url = self._url(urljoin(origem, proxima))
            elif proxima.startswith('/') or urlsplit(proxima).scheme:
                # Links relativos à raiz do servidor não são endpoints do cliente.
                base = urlsplit(self.url_base)
                url = self._url(urljoin(f"{base.scheme}://{base.netloc}/", proxima))
            else:
                raise SuapApiError("Paginação relativa exige url_origem para um JSON externo.")
            if url in visitadas:
                raise SuapApiError("Ciclo detectado na paginação.")
            visitadas.add(url)
            resposta = self.get(url)
            origem = url
