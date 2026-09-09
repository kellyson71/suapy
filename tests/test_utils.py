import builtins
import subprocess
import sys

import pytest

from suapy import para_dataframe, parse_horario


def test_import_does_not_load_pandas():
    subprocess.run([sys.executable, "-c",
                    "import suapy, sys; assert 'pandas' not in sys.modules"], check=True)


def test_dataframe_envelope():
    pd = pytest.importorskip("pandas")
    frame = para_dataframe({"results": [{"nota": "8"}, {"nota": None}, {"nota": "-"}]}, chave="results")
    assert pd.to_numeric(frame["nota"], errors="coerce").mean() == 8
    with pytest.raises(KeyError):
        para_dataframe({}, chave="results")


def test_missing_pandas(monkeypatch):
    original = builtins.__import__
    def importing(name, *args, **kwargs):
        if name == "pandas":
            raise ImportError("missing")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", importing)
    with pytest.raises(ImportError, match="suapy\\[pandas\\]"):
        para_dataframe([])


def test_schedule_parser():
    rows = parse_horario("23V12 / 4N56 / lixo / 2M12INVALIDO")
    assert [r["dia_num"] for r in rows] == [2, 3, 4]
    assert rows[-1]["turno"] == "Noite"
    assert parse_horario(None) == []
