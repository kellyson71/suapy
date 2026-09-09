def para_dataframe(dados, chave=None):
    """Converte JSON em DataFrame; use chave='results' para uma página.

    Não busca páginas adicionais. Para isso, use Suap.iterar_resultados().
    """
    try:
        import pandas as pd
    except ImportError as exc:
        raise ImportError('Instale o extra: pip install "suapy[pandas]".') from exc
    if chave is not None:
        if not isinstance(dados, dict):
            raise TypeError("O argumento chave exige um dicionário.")
        dados = dados[chave]
    if not isinstance(dados, list):
        dados = [dados]
    return pd.DataFrame(dados)
