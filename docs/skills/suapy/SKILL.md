---
name: suapy
description: Use a biblioteca Python Suapy e seu CLI para autenticar contas SUAP, consultar perfis e dados acadêmicos, paginar respostas e exportar CSV ou JSON. Aplicável a integrações com Suapy; não presume compatibilidade com toda instituição SUAP.
---

# Suapy

Referência portátil do Suapy 1.4.1. Use para escrever scripts, integrar identificação de contas, explicar a biblioteca e diagnosticar suas consultas. Este arquivo pode ser lido por agentes que aceitem skills ou fornecido como contexto em uma conversa.

## Instalação e fontes

- Python >= 3.10; `python -m pip install suapy`.
- `python -m pip install 'suapy[pandas]'` somente se precisar de DataFrame.
- Dependências principais: requests e rich. CSV e JSON dispensam Pandas.
- API padrão: `https://suap.ifrn.edu.br`. Endpoints e permissões de outras instituições podem diferir.
- Documentação: https://kellyson71.github.io/suapy/
- Código: https://github.com/kellyson71/suapy
- Para versões diferentes, confirme assinaturas no código instalado ou na documentação correspondente; não invente métodos, endpoints ou campos do JSON.

## Login simples: obter a identidade

```python
from getpass import getpass
from suapy import autenticar

matricula = input("Digite sua matrícula: ")
senha = getpass("Digite sua senha: ")
perfil = autenticar(matricula, senha)
print(f"Olá, {perfil.nome}!")
print(f"E-mail: {perfil.email}")
```

`autenticar(usuario, senha, url_base="https://suap.ifrn.edu.br", timeout=(5, 30))` abre um cliente, autentica, obtém perfil e fecha as conexões. Não devolve um cliente autenticado para consultas posteriores. Não persiste tokens em disco. Não peça senhas em conversas; solicite-as durante a execução, com getpass, ou use o mecanismo de segredos escolhido pelo usuário. Não coloque credenciais em exemplos, logs ou repositórios.

`Perfil` é uma dataclass imutável: `matricula`, `nome`, `email`, `campus`, `tipo_usuario`, `foto`, `vinculos` (tupla). Campos textuais ausentes podem ser strings vazias. `aluno_ativo` é booleano; `vinculo_aluno_ativo` é o primeiro vínculo de aluno ativo ou `None`. Verifique antes de acessar `.curso`.

Cada `Vinculo` expõe `identificador`, `tipo`, `campus`, `ativo`, `curso`, `modalidade`, `nivel_ensino`; vários campos podem ser `None`. `de_aluno` indica se o campo `ativo` foi reconhecido como booleano. O perfil é montado a partir de `/api/rh/eu/` e `/api/rh/meus-vinculos/`. Autenticação bem-sucedida não substitui as regras de autorização do sistema que integra a conta.

## Consultas com cliente aberto

```python
from getpass import getpass
from suapy import Suap, SuapError

try:
    with Suap() as suap:
        suap.login(input("Matrícula: "), getpass("Senha: "))
        periodos = list(suap.iterar_resultados(
            suap.ensino.obter_periodos_letivos()
        ))
        if not periodos:
            print("Nenhum período disponível.")
        else:
            atual = max(periodos, key=lambda p: (
                int(p["ano_letivo"]), int(p["periodo_letivo"])
            ))
            resposta = suap.ensino.obter_boletim(
                atual["ano_letivo"], atual["periodo_letivo"]
            )
            for disciplina in suap.iterar_resultados(resposta):
                print(disciplina.get("disciplina"),
                      disciplina.get("numero_faltas"),
                      disciplina.get("media_final_disciplina"))
except SuapError as erro:
    print(f"Consulta indisponível: {erro}")
```

- `Suap(url_base=..., verificar_ssl=True, timeout=(5, 30))`: timeout de conexão e leitura. Preserve TLS habilitado.
- `login(usuario, senha)` retorna `True` ou lança erro; não retorna perfil.
- `obter_perfil()` fornece a identidade no cliente aberto.
- `with` fecha conexões; sem ele, use `fechar()` em finally.
- `logout()` remove tokens da memória; não revoga no servidor.
- Tokens ficam em memória na biblioteca. Após HTTP 401, renova e repete a chamada uma vez se houver refresh token. Falhas de rede não têm repetição automática.
- Prefixos de instalação em `url_base`, como `/suap`, são preservados. URLs não podem incluir credenciais, query ou fragmento. Redirecionamentos HTTP não são seguidos.
- `get(caminho, params=None)` e `post(caminho, dados=None, json=None)` existem para endpoints conhecidos; apenas URLs da mesma origem são aceitas. Uma ação de escrita depende do pedido do usuário e do contrato do endpoint.

## Métodos públicos por módulo

Todos são chamados a partir de um cliente `suap` autenticado. As respostas são o JSON da API; não suponha uma estrutura uniforme.

| Módulo | Métodos |
| --- | --- |
| `suap.ensino` | `obter_dados_aluno()`, `obter_periodos_letivos()`, `obter_boletim(ano, periodo)`, `obter_turmas_virtuais(ano, periodo)`, `obter_turma_virtual(pk)`, `obter_proximas_avaliacoes()`, `obter_mensagens_aluno(status="nao_lidas")`, `obter_requisitos_conclusao()`, `obter_eventos()`, `obter_horario_aulas()`, `obter_diarios(ano=None, periodo=None)` |
| `suap.usuario` | `obter_meus_dados_resumidos()`, `obter_meus_dados()`, `obter_meus_vinculos()`, `obter_historico_funcional()`, `obter_contracheques()`, `obter_contracheque_detalhado(ano, mes)` |
| `suap.infraestrutura` | `obter_campi()`, `obter_setores()` |
| `suap.pesquisa_extensao` | `obter_projetos_pesquisa()`, `obter_projetos_extensao()` |

- Descubra ano/período em `obter_periodos_letivos()`. Não fixe o semestre como se existisse para toda conta.
- Boletim traz notas e faltas; diários podem exigir perfil de professor. Métodos funcionais podem exigir servidor.
- `obter_horario_aulas()` retorna o campo `horario_aula` dos dados do aluno ou `None`; não agrega horários das turmas.
- Mensagens: status `nao_lidas`, `lidas` ou `todas`.
- Ano: quatro dígitos; período positivo, não restrito a 1 e 2; inteiros e strings decimais ASCII são aceitos, booleanos rejeitados.
- Em diários, ano e período devem ser fornecidos juntos ou ambos omitidos.
- `pk` de turma é inteiro positivo; mês do contracheque entre 1 e 12.

## Respostas e paginação

Use objetos de detalhe diretamente. Para listagens, `suap.iterar_resultados(resposta)` aceita listas e dicionários paginados com `results` e `next`, seguindo as próximas páginas. Não aplique esse iterador a qualquer dicionário de detalhe. Não pressuponha que a primeira página contenha tudo ou que a ordem seja cronológica.

Páginas retornadas pelo cliente preservam a URL de origem como atributo, fora dos campos JSON. Para um JSON carregado externamente com `next` relativo, informe `url_origem`:

```python
registros = suap.iterar_resultados(
    pagina,
    url_origem="https://instituicao.example/suap/api/lista/",
)
```

Links de outra origem e ciclos são rejeitados. Links relativos à raiz seguem a semântica da URL do servidor. A iteração busca páginas sob demanda; `list(...)` reúne todos os registros em memória.

## Conversão e horários

```python
from suapy import para_dataframe, parse_horario

# Com cliente autenticado e período escolhido:
resposta = suap.ensino.obter_boletim(ano, periodo)
df = para_dataframe(list(suap.iterar_resultados(resposta)))

for aula in parse_horario("2V34 / 4V56"):
    print(aula["dia_semana"], aula["turno"], aula["horarios"])
# Segunda Tarde [3, 4]
# Quarta Tarde [5, 6]
```

`para_dataframe(resposta, chave="results")` converte apenas a página fornecida; não pagina. Pandas é importado apenas quando usado. Média simples das notas não equivale necessariamente ao índice acadêmico oficial.

`parse_horario` retorna lista de dicionários com `dia_semana`, `dia_num`, `turno`, `horarios`. Dias: 1 domingo, 2 segunda, até 7 sábado. Turnos: M manhã, V tarde, N noite. Os números são tempos de aula, não horas do relógio; os horários exatos dependem do campus. Trechos inválidos são ignorados.

## CLI e exportação

```bash
suapy
suapy periodos
suapy boletim --ano 2026 --periodo 2
suapy turmas --ano 2026 --periodo 2
suapy avaliacoes
suapy mensagens --status todas
suapy progresso
suapy boletim --ano 2026 --periodo 2 --formato csv --saida boletim.csv
suapy avaliacoes --formato json
suapy --sem-sessao
suapy --logout
```

Ano e período acima são exemplos. Consulte `suapy --help` e o help do subcomando para opções da versão instalada.

- Consultas diretas aceitam `--formato tabela|json|csv`; padrão tabela. `--saida` exige JSON/CSV e cria arquivo sem sobrescrever. Listagens exportadas incluem todas as páginas e são reunidas em memória.
- Prompts e avisos vão para stderr; JSON/CSV para stdout ou arquivo. Redirecionar com `>` pode sobrescrever e usa permissões do shell.
- JSON mantém objetos/listas. CSV reúne as chaves como colunas, serializa valores aninhados em JSON, deixa ausentes vazios e prefixa textos semelhantes a fórmulas com apóstrofo.
- CLI do IFRN salva refresh token em `~/.suapy/session.json`, sem senha. O token é credencial em texto simples. POSIX: pasta 700, arquivo 600.
- Sair mantém a sessão; encerrar sessão ou `--logout` remove o token local, sem revogação remota.
- `--sem-sessao` não lê nem modifica o arquivo, e não pode ser combinado com `--logout`.
- `--url-base URL` seleciona outra instituição e não reutiliza nem grava a sessão do IFRN.
- Códigos de saída: sucesso 0, erro de execução 1, argumentos inválidos 2, interrupção 130.

## Erros

Importe de `suapy`: `SuapError`, `SuapAuthError`, `SuapApiError`.

- `ValueError`: entradas inválidas, como credenciais vazias, URL, ano/período ou status incorreto.
- `SuapAuthError`: HTTP 401/403, falta de token ou resposta de autenticação inválida. Um 403 também pode indicar falta de permissão; não conclua sempre que a senha está errada.
- `SuapApiError`: demais erros HTTP, JSON inválido e problemas de paginação; atributos `status_code` e `response` quando aplicáveis.
- `SuapError`: classe base, também usada para timeout e conexão. Capture subclasses antes da base quando precisar distinguir causas.

## Desenvolvimento e verificação

No repositório: `python -m pip install -e '.[dev,pandas]'` e `python -m pytest -q`. Os testes padrão simulam a API. Exemplos de saídas na documentação são ilustrativos; não descreva uma execução simulada como consulta real.

`scripts/test_live.py` exige conta de teste em `SUAP_TEST_USERNAME` e `SUAP_TEST_PASSWORD`; `SUAP_TEST_URL` é opcional. Não imprime respostas nem salva tokens. Retorna 2 sem credenciais ou períodos (validação incompleta), 1 em erros. Use apenas quando o usuário tiver autorizado acesso real.

Ao atualizar esta skill, confira `suapy/client.py`, `suapy/perfil.py`, `suapy/modules/`, `suapy/cli.py` e `suapy/utils/` para manter os contratos alinhados. Projeto independente, sem afiliação oficial ao IFRN ou SUAP.
