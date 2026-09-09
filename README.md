<p align="center">
  <img src="https://raw.githubusercontent.com/kellyson71/suapy/main/assets/suapy-logo.png" alt="Suapy — biblioteca Python para a API do SUAP" width="520">
</p>

# Suapy

Consulte boletim, faltas, horários e avaliações do SUAP com Python ou pelo terminal.
Os métodos são em português e usam a API do IFRN por padrão. Outras instituições
podem ter endpoints ou permissões diferentes; a compatibilidade não é garantida.

[PyPI](https://pypi.org/project/suapy/) ·
[Código-fonte](https://github.com/kellyson71/suapy) ·
[Relatar problema](https://github.com/kellyson71/suapy/issues)

## Instalação

Requer Python 3.10 ou superior. A versão 1.4 passa a exigir esse mínimo.

```bash
python -m pip install suapy
```

Para usar a conversão de dados com Pandas:

```bash
python -m pip install "suapy[pandas]"
```

## Pelo terminal

```bash
suapy
```

Informe sua matrícula e senha. O menu permite consultar boletim e faltas,
horário do dia, progresso do curso e eventos. A senha não aparece enquanto você digita.

O terminal guarda um refresh token em `~/.suapy/session.json` para restaurar o
acesso. Esse arquivo contém uma credencial em texto simples, embora não contenha
sua senha. Em sistemas POSIX, a pasta tem permissão `700` e o arquivo `600`;
em outros sistemas, o acesso depende das permissões da conta e do diretório.

A opção **Sair** mantém a sessão. Para removê-la deste computador, use a opção
**Encerrar sessão e sair** ou execute:

```bash
suapy --logout
```

Isso remove o token local; não o revoga no servidor.

## Em Python

O exemplo consulta os períodos disponíveis e busca o boletim do mais recente.
A senha é solicitada no terminal, sem ficar escrita no código.

```python
from getpass import getpass
from suapy import Suap, SuapError

try:
    with Suap() as suap:
        suap.login(input("Matrícula: "), getpass("Senha: "))

        periodos = list(suap.iterar_resultados(
            suap.ensino.obter_periodos_letivos()
        ))
        if periodos:
            atual = max(periodos, key=lambda p: (
                int(p["ano_letivo"]), int(p["periodo_letivo"])
            ))
            resposta = suap.ensino.obter_boletim(
                atual["ano_letivo"], atual["periodo_letivo"]
            )
            for disciplina in suap.iterar_resultados(resposta):
                print(
                    disciplina.get("disciplina", "Sem nome"),
                    "— faltas:", disciplina.get("numero_faltas", "—"),
                    "— média:", disciplina.get("media_final_disciplina", "—"),
                )
        else:
            print("Nenhum período letivo disponível.")
except SuapError as erro:
    print(f"Não foi possível consultar o SUAP: {erro}")
```

O bloco `with` fecha as conexões ao terminar. Sem ele, chame `suap.fechar()`.
A biblioteca mantém tokens somente em memória; a gravação em disco é uma função do CLI.

## Consultas disponíveis

Os retornos dependem do perfil da conta e dos dados cadastrados na instituição.

| Método de `suap.ensino` | Consulta |
| --- | --- |
| `obter_dados_aluno()` | Dados institucionais do aluno |
| `obter_periodos_letivos()` | Períodos disponíveis para consulta |
| `obter_boletim(ano, periodo)` | Notas, faltas e situação por disciplina |
| `obter_proximas_avaliacoes()` | Avaliações cadastradas |
| `obter_turmas_virtuais(ano, periodo)` | Turmas, horários e locais de aula |
| `obter_turma_virtual(pk)` | Detalhes de uma turma |
| `obter_mensagens_aluno(status="nao_lidas")` | Mensagens: `nao_lidas`, `lidas` ou `todas` |
| `obter_requisitos_conclusao()` | Progresso e carga horária do curso |
| `obter_eventos()` | Eventos institucionais |
| `obter_diarios(ano=None, periodo=None)` | Diários; pode exigir perfil de professor |

Para faltas e notas de alunos, use `obter_boletim()`. A biblioteca também expõe
os módulos `usuario`, `infraestrutura` e `pesquisa_extensao`; consulte os
[métodos no código](https://github.com/kellyson71/suapy/tree/main/suapy/modules).

## Respostas e paginação

Os métodos devolvem o JSON da API sem alterar sua estrutura. Uma consulta pode
retornar uma lista, um objeto ou uma página com `results` e `next`.

Para uma consulta de listagem, `suap.iterar_resultados(resposta)` aceita tanto
listas quanto páginas e busca as páginas seguintes conforme você itera.
Objetos de detalhe, como os dados do aluno, devem ser usados diretamente.

```python
# Com suap já autenticado:
resposta = suap.ensino.obter_proximas_avaliacoes()
for avaliacao in suap.iterar_resultados(resposta):
    print(avaliacao.get("disciplina"), avaliacao.get("data_avaliacao"))
```

O iterador rejeita links de outra origem e ciclos de paginação. Ele não ordena
os registros; a primeira avaliação recebida não é necessariamente a próxima por data.

## Análise com Pandas

```python
import pandas as pd
from suapy import para_dataframe

# Com suap autenticado e ano/periodo escolhidos:
resposta = suap.ensino.obter_boletim(ano, periodo)
df = para_dataframe(list(suap.iterar_resultados(resposta)))

if "media_final_disciplina" in df.columns:
    notas = pd.to_numeric(df["media_final_disciplina"], errors="coerce")
    if notas.notna().any():
        print(f"Média simples das notas disponíveis: {notas.mean():.2f}")
```

Essa média não representa necessariamente o índice acadêmico da instituição.
Para converter apenas uma página envelopada, use
`para_dataframe(resposta, chave="results")`. A conversão não busca outras páginas.
O Pandas só é importado quando essa função é chamada.

## Horários

```python
from suapy import parse_horario

for aula in parse_horario("2V34 / 4V56"):
    print(aula["dia_semana"], aula["turno"], aula["horarios"])
# Segunda Tarde [3, 4]
# Quarta Tarde [5, 6]
```

Os números indicam tempos de aula, não horas do relógio. Os horários exatos
dependem do campus. Trechos que não correspondem ao formato são ignorados.

## Conexão e erros

```python
from suapy import Suap

suap = Suap(
    url_base="https://suap.ifrn.edu.br",
    timeout=(5, 30),  # conexão e espera de leitura, em segundos
)
suap.fechar()
```

A verificação TLS fica habilitada. Redirecionamentos HTTP não são seguidos.
Ao receber `401`, o cliente tenta renovar o token e repetir a chamada uma vez,
se houver refresh token. Não há repetição automática para falhas de rede.

| Exceção | Situação |
| --- | --- |
| `SuapAuthError` | Autenticação inválida, token ausente ou acesso negado (`401`/`403`) |
| `SuapApiError` | Outros erros HTTP, JSON inválido ou paginação inválida |
| `SuapError` | Classe base; também cobre timeout e falha de conexão |

Capture as exceções específicas antes de `SuapError` quando precisar distinguir
as causas. `SuapApiError` disponibiliza `status_code` e `response` quando aplicáveis.

## Desenvolvimento

Veja o [guia de contribuição](https://github.com/kellyson71/suapy/blob/main/CONTRIBUTING.md)
para instalar o projeto, executar os testes e preparar uma distribuição.
As mudanças estão no [changelog](https://github.com/kellyson71/suapy/blob/main/CHANGELOG.md).

Projeto independente, sem afiliação oficial ao IFRN ou ao SUAP.
Distribuído sob a [licença MIT](https://github.com/kellyson71/suapy/blob/main/LICENSE).
