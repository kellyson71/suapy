from suapy import Suap
import pytest

def test_suap_instance():
    """Testa se a classe Suap pode ser instanciada."""
    s = Suap()
    assert s is not None
    assert hasattr(s, 'ensino')
    assert hasattr(s, 'usuario')
