try:
    import pandas as pd
except ImportError:
    pd = None

def para_dataframe(dados, chave=None):
    """
    Converte um retorno JSON da API do SUAP em um Pandas DataFrame.
    
    Args:
        dados (dict ou list): Os dados retornados pela chamada à API.
        chave (str, opcional): Se os dados estiverem envelopados em um dicionário, 
                               passe o nome da chave que contém a lista.
                               
    Returns:
        pd.DataFrame: Um dataframe contendo os dados extraídos.
    """
    if pd is None:
        raise ImportError("Pandas não está instalado. Use 'pip install pandas' para usar essa função.")
    
    if chave and isinstance(dados, dict):
        dados = dados.get(chave, [])
    
    if not isinstance(dados, list):
        dados = [dados]
        
    return pd.DataFrame(dados)
