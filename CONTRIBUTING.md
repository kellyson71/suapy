# Desenvolvimento

Use Python 3.10 a 3.14. Crie um ambiente virtual e instale as dependências:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,pandas]"
python -m pytest
python -m build
python -m twine check dist/*
```

No Windows, ative com `.venv\Scripts\activate`. Os testes usam respostas simuladas;
não precisam de matrícula, senha nem acesso ao SUAP. Não inclua dados de alunos em
fixtures ou relatos de erro. A CI testa Python 3.10–3.14, com e sem Pandas.

## Publicação

O README é usado diretamente como descrição do PyPI. Sua logo usa a URL pública
do arquivo em `assets/`; envie esse arquivo ao branch main antes da publicação.

O workflow `.github/workflows/release.yml` publica quando uma release do GitHub
é publicada. Ele executa a matriz de testes, confere a tag contra a versão,
constrói e valida os pacotes e só então solicita a credencial temporária.

Configure o Trusted Publisher do projeto suapy no PyPI com:

- Owner: `kellyson71` (proprietário do repositório GitHub).
- Repository: `suapy`.
- Workflow: `release.yml`.
- Environment: `pypi`.

Crie também o environment `pypi` no GitHub. Depois de enviar as alterações,
atualize a versão em `pyproject.toml`, finalize o changelog e publique uma release
com tag correspondente, por exemplo `v1.4.0`. Versões já publicadas não podem ser
sobrescritas. Configurar os arquivos localmente não publica um pacote.

Referência: [Trusted Publishing do PyPI](https://docs.pypi.org/trusted-publishers/using-a-publisher/).

## Credenciais

Arquivos locais em `.private/` são ignorados pelo Git e excluídos da distribuição.
Não force sua inclusão. Tokens compartilhados devem ser revogados; para publicação
manual, crie um token restrito a suapy e forneça-o pelo mecanismo de autenticação
do Twine, sem colocá-lo em comandos versionados. O workflow usa Trusted Publishing
e não depende desse arquivo local.
