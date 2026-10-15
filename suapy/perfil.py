"""Perfil normalizado do usuário autenticado, para identificar contas em outros sistemas."""

from dataclasses import dataclass

from .exceptions import SuapApiError


@dataclass(frozen=True)
class Vinculo:
    """Vínculo institucional. ``ativo`` e ``curso`` só existem para vínculos de aluno."""

    identificador: str
    tipo: str
    campus: str | None
    ativo: bool | None = None
    curso: str | None = None
    modalidade: str | None = None
    nivel_ensino: str | None = None

    @property
    def de_aluno(self):
        return self.ativo is not None


@dataclass(frozen=True)
class Perfil:
    """Dados de identificação vindos de /api/rh/eu/ e /api/rh/meus-vinculos/."""

    matricula: str
    nome: str
    email: str
    campus: str
    tipo_usuario: str
    foto: str
    vinculos: tuple

    @property
    def vinculo_aluno_ativo(self):
        """Primeiro vínculo de aluno ativo, ou None."""
        return next((v for v in self.vinculos if v.de_aluno and v.ativo), None)

    @property
    def aluno_ativo(self):
        return self.vinculo_aluno_ativo is not None


def _texto(dados, *chaves):
    for chave in chaves:
        valor = dados.get(chave)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    return ""


def montar_vinculo(dados):
    if not isinstance(dados, dict):
        raise SuapApiError("Vínculo em formato inesperado.")
    detalhe = dados.get("detalhamento") if isinstance(dados.get("detalhamento"), dict) else {}
    ativo = detalhe.get("ativo")
    return Vinculo(
        identificador=_texto(dados, "identificador"),
        tipo=_texto(dados, "tipo"),
        campus=_texto(dados, "campus") or None,
        ativo=ativo if isinstance(ativo, bool) else None,
        curso=_texto(detalhe, "curso") or None,
        modalidade=_texto(detalhe, "modalidade") or None,
        nivel_ensino=_texto(detalhe, "nivel_ensino") or None,
    )


def montar_perfil(eu, vinculos=()):
    """Converte as respostas de /api/rh/eu/ e dos vínculos em um Perfil."""
    if not isinstance(eu, dict) or not _texto(eu, "identificacao"):
        raise SuapApiError("Dados do usuário sem identificação.")
    return Perfil(
        matricula=_texto(eu, "identificacao"),
        nome=_texto(eu, "nome_usual", "nome", "nome_social", "nome_registro"),
        email=_texto(eu, "email_academico", "email_preferencial", "email", "email_secundario"),
        campus=_texto(eu, "campus"),
        tipo_usuario=_texto(eu, "tipo_usuario"),
        foto=_texto(eu, "foto"),
        vinculos=tuple(montar_vinculo(v) for v in vinculos),
    )


def autenticar(usuario, senha, url_base="https://suap.ifrn.edu.br", timeout=(5, 30)):
    """Faz login, devolve o Perfil e fecha a conexão; nenhum token é guardado.

    Útil para validar uma conta no login de outro sistema. Credenciais inválidas
    levantam SuapAuthError.
    """
    from .client import Suap

    with Suap(url_base=url_base, timeout=timeout) as suap:
        suap.login(usuario, senha)
        return suap.obter_perfil()
