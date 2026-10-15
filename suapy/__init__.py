from importlib.metadata import PackageNotFoundError, version

from .client import Suap
from .exceptions import SuapError, SuapAuthError, SuapApiError
from .perfil import Perfil, Vinculo, autenticar
from .utils.dados import para_dataframe
from .utils.parser import parse_horario

try:
    __version__ = version("suapy")
except PackageNotFoundError:  # executando direto do código-fonte, sem instalar
    __version__ = "0+desconhecida"

__all__ = ["Suap", "SuapError", "SuapAuthError", "SuapApiError", "Perfil", "Vinculo",
           "autenticar", "para_dataframe", "parse_horario"]
