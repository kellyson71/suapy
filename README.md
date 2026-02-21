<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=32&pause=1000&color=2E9E4F&center=true&vCenter=true&width=500&lines=Suapy+%F0%9F%90%8D;Seu+SUAP%2C+em+Python%2C+em+portugu%C3%AAs." alt="Typing SVG" />

**A biblioteca Python feita para estudantes brasileiros que usam o SUAP.**  
Acesse faltas, notas, provas e muito mais — com código limpo e em português.

[![PyPI version](https://img.shields.io/pypi/v/suapy?color=2e9e4f&style=flat-square&label=suapy)](https://pypi.org/project/suapy/)
[![Python](https://img.shields.io/pypi/pyversions/suapy?style=flat-square&color=3572A5)](https://python.org)
[![License](https://img.shields.io/pypi/l/suapy?style=flat-square&color=orange)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/suapy?style=flat-square&color=blueviolet)](https://pypi.org/project/suapy/)

</div>

---

## ✨ Por que o Suapy?

> Você quer saber **quantas faltas** tem antes de reprovar. Quer ver **quando é sua próxima prova**. Quer jogar suas notas num DataFrame do Pandas e entender de vez o semestre. O Suapy faz isso tudo — em português, com poucas linhas.

---

## 📦 Instalação

```bash
pip install suapy
```

### 💻 Usando o Terminal

```bash
suapy

```

Isso abrirá uma interface interativa para ver seu boletim, horário e eventos sem precisar escrever uma linha de código.

<details>
<summary>🐼 Usando Pandas? Instale com o extra</summary>

```bash
pip install suapy[pandas]
```

</details>

---

## 🚀 Primeiros passos (Biblioteca)

```python
from suapy import Suap

suap = Suap()
suap.login("20201014040001", "sua_senha")

# 👤 Quem sou eu?
aluno = suap.ensino.obter_dados_aluno()
print(f"E aí, {aluno['nome_usual']}! 👋")

# 📅 Próxima prova
provas = suap.ensino.obter_proximas_avaliacoes()
if provas:
    p = provas[0]
    print(f"📌 Prova de {p['disciplina']} em {p['data_avaliacao']}")

# 📋 Situação das matérias
for d in suap.ensino.obter_diarios(2024, 1):
    print(f"• {d['disciplina']}: {d['numero_faltas']} faltas — {d['situacao']}")
```

---

## 🔄 Persistência de Sessão

O CLI `suapy` gerencia sua sessão automaticamente para você não precisar digitar a senha toda vez.

- **Onde fica salvo?** Em `~/.suapy/session.json`.
- **Como funciona?** Ele guarda um _refresh token_. Ao abrir o app, ele tenta renovar o acesso. Se funcionar, você entra direto!
- **Segurança:** Seus dados de login (senha) **não** são salvos, apenas o token de autorização.

---

## 🎒 O que você pode fazer com `suap.ensino`

| Função                            | O que retorna                                         |
| --------------------------------- | ----------------------------------------------------- |
| `obter_dados_aluno()`             | Matrícula, curso, cotas e contatos                    |
| `obter_diarios(ano, periodo)`     | Faltas, notas e situação por disciplina               |
| `obter_boletim(ano, periodo)`     | Médias finais e carga horária                         |
| `obter_proximas_avaliacoes()`     | Datas de provas e trabalhos cadastrados               |
| `obter_mensagens_aluno()`         | Recados do SUAP (`'lidas'`, `'nao_lidas'`, `'todas'`) |
| `obter_turmas_virtuais(ano, per)` | Links e participantes da turma virtual                |
| `obter_requisitos_conclusao()`    | Horas e matérias que faltam para formar               |

---

## 📊 Analisando suas notas com Pandas

```python
from suapy import para_dataframe

boletim = suap.ensino.obter_boletim(2024, 1)
df = para_dataframe(boletim)

media = df['media_final_disciplina'].astype(float).mean()
print(f"📈 Sua média geral: {media:.2f}")
```

---

## 🔐 Tratando erros de login

```python
from suapy import Suap, SuapAuthError

try:
    suap.login("usuario", "senha_errada")
except SuapAuthError:
    print("❌ Usuário ou senha incorretos.")
```

---

<div align="center">

Feito com 💚 para os estudantes do **IF** e de todas as instituições que usam o **SUAP**

_Não é afiliado ao IFRN nem ao projeto SUAP oficial._

</div>
