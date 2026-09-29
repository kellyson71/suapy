from suapy import Suap
import pytest

def test_suap_instance():
    """Testa se a classe Suap pode ser instanciada."""
    s = Suap()
    assert s is not None
    assert hasattr(s, 'ensino')
    assert hasattr(s, 'usuario')


def test_version_matches_pyproject():
    import tomllib
    from pathlib import Path

    import suapy

    projeto = tomllib.loads((Path(__file__).parent.parent / "pyproject.toml").read_text())
    assert suapy.__version__ == projeto["project"]["version"]
