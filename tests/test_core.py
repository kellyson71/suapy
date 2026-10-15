from suapy import Suap
import pytest

def test_suap_instance():
    """Testa se a classe Suap pode ser instanciada."""
    s = Suap()
    assert s is not None
    assert hasattr(s, 'ensino')
    assert hasattr(s, 'usuario')


def test_version_matches_pyproject():
    import re
    from pathlib import Path

    import suapy

    # tomllib só existe a partir do Python 3.11; o projeto ainda suporta 3.10.
    texto = (Path(__file__).parent.parent / "pyproject.toml").read_text(encoding="utf-8")
    versao = re.search(r'^version\s*=\s*"([^"]+)"', texto, re.MULTILINE).group(1)
    assert suapy.__version__ == versao
