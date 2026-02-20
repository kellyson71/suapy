# Suapy 🎓🐍

Uma biblioteca Python **moderna, fácil e 100% em português brasileiro (pt-BR)** para acessar a API pública do **SUAP**.

O nome mudou e as ferramentas também! O **Suapy** foi criado pensando especialmente no **ALUNO**. Quer saber quantas **faltas** você tem em uma matéria? Extrair suas médias para um DataFrame do Pandas? Verificar suas **próximas provas** ou ver requisitos de formatura? O Suapy resolve com poucas linhas de código.

## 📦 Instalação

Instale pelo pip diretamente:

```bash
pip install suapy
```

> **Dica aos Alunos (Data Science)**: Se quiser análises fantásticas de suas notas e frequências usando o Pandas, instale assim:
>
> ```bash
> pip install suapy[pandas]
> ```

---

## 🚀 Como Usar (Exemplo Estudantil)

A vida acadêmica ficou mais fácil. Vamos mostrar como acessar seus dados de falhas e avaliações:

```python
from suapy import Suap

suap = Suap()
suap.login("20201014040001", "senha123")

# 1. Suas Informações Básicas
aluno = suap.ensino.obter_dados_aluno()
print(f"E aí, {aluno['nome_usual']}!")

# 2. Quando é a próxima prova?
provas = suap.ensino.obter_proximas_avaliacoes()
if provas:
    prox = provas[0]
    print(f"Lembrete: Prova de {prox['disciplina']} dia {prox['data_avaliacao']}")

# 3. Faltas e Notas (Diários do Semestre)
diarios = suap.ensino.obter_diarios(2023, 1)

print("\nMaterias - Situação de Faltas:")
for d in diarios:
    nome = d['disciplina']
    faltas = d['numero_faltas']
    situacao = d['situacao']
    print(f"- {nome}: {faltas} faltas. Status: {situacao}")
```

---

## 🎒 Funções do Aluno (`suap.ensino`)

O módulo `suap.ensino` contém tudo o que um aluno precisa para interagir com a faculdade/escola:

| Função                            | O que faz?                                                                        |
| --------------------------------- | --------------------------------------------------------------------------------- |
| `obter_dados_aluno()`             | Retorna matrícula, curso, dados de cota e contatos do aluno.                      |
| `obter_diarios(ano, periodo)`     | Extrai as **faltas**, notas e situação do diário no semestre atual.               |
| `obter_boletim(ano, periodo)`     | Pega o seu boletim oficial (médias finais e carga horária consolidadas).          |
| `obter_proximas_avaliacoes()`     | Cuidado pra não reprovar! Avisa data das próximas provas e trabalhos cadastrados. |
| `obter_mensagens_aluno()`         | Vê os recados do SUAP (usando `'nao_lidas'`, `'lidas'` ou `'todas'`).             |
| `obter_turmas_virtuais(ano, per)` | Links e participantes que compõem sua turma virtual.                              |
| `obter_requisitos_conclusao()`    | Quantas horas faltam para formar? Quais matérias estão devendo?                   |

---

## 📊 Trabalhando com Pandas

Você é tech e quer brincar com seus dados acadêmicos matematicamente?

```python
from suapy import para_dataframe

boletim = suap.ensino.obter_boletim(2023, 1)
df_notas = para_dataframe(boletim)

# Calcular a média do seu semestre com 1 comando de Pandas:
minha_media_geral = df_notas['media_final_disciplina'].astype(float).mean()
print(f"Média Geral do Semestre: {minha_media_geral}")
```

## ⚙️ Tratamento de Erros

Trate logins inválidos de imediato na sua automação (bot no telegram, dashboard, etc.):

```python
from suapy import Suap, SuapAuthError

suap = Suap()
try:
    suap.login("usuario", "senha_errada")
except SuapAuthError:
    print("Vish... Usuário ou senha incorretos.")
```

---

_Feito com 💚 para facilitar a vida do estudante do IF e de todos que utilizam o SUAP._
