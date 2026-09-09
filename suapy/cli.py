"""Interface de terminal para consultas acadêmicas."""

import argparse
import getpass
import json
import os
import tempfile
from datetime import datetime
from itertools import islice
from pathlib import Path

from rich.console import Console
from rich.table import Table

from suapy import Suap, SuapAuthError, SuapError, parse_horario

console = Console(markup=False)
SESSION_FILE = Path.home() / ".suapy" / "session.json"


def save_session(refresh_token):
    """Grava atomicamente; em POSIX, pasta 700 e arquivo 600."""
    SESSION_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name == "posix":
        SESSION_FILE.parent.chmod(0o700)
    fd, nome = tempfile.mkstemp(dir=SESSION_FILE.parent, prefix=".session-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
            json.dump({"refresh": refresh_token}, arquivo)
        os.replace(nome, SESSION_FILE)
    finally:
        if os.path.exists(nome):
            os.unlink(nome)


def load_session():
    try:
        with SESSION_FILE.open(encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        token = dados.get("refresh") if isinstance(dados, dict) else None
        return token if isinstance(token, str) and token.strip() else None
    except (OSError, ValueError):
        return None


def clear_session():
    try:
        SESSION_FILE.unlink()
    except FileNotFoundError:
        pass


def escolher_periodo(suap):
    periodos = list(suap.iterar_resultados(suap.ensino.obter_periodos_letivos()))
    periodos.sort(key=lambda p: (int(p["ano_letivo"]), int(p["periodo_letivo"])), reverse=True)
    if not periodos:
        console.print("Nenhum período letivo encontrado.")
        return None, None
    for i, p in enumerate(periodos, 1):
        console.print(f"{i}. {p['ano_letivo']}.{p['periodo_letivo']}")
    while True:
        escolha = console.input("Período [1]: ").strip() or "1"
        if escolha.isdigit() and 1 <= int(escolha) <= len(periodos):
            p = periodos[int(escolha) - 1]
            return p["ano_letivo"], p["periodo_letivo"]
        console.print("Escolha um dos períodos da lista.")


def mostrar_boletim_e_faltas(suap):
    ano, periodo = escolher_periodo(suap)
    if ano is None:
        return
    tabela = Table("Disciplina", "Média", "Faltas", "Situação")
    for d in suap.iterar_resultados(suap.ensino.obter_boletim(ano, periodo)):
        tabela.add_row(*(str(d.get(chave, "—")) for chave in
                          ("disciplina", "media_final_disciplina", "numero_faltas", "situacao")))
    console.print(tabela if tabela.row_count else "Nenhum boletim para este período.")


def ordenar_horarios(horarios):
    ordem = {"Manhã": 0, "Tarde": 1, "Noite": 2}
    return sorted(horarios, key=lambda h: (ordem.get(h["turno"], 3), h["horarios"][0]))


def mostrar_horario_hoje(suap):
    ano, periodo = escolher_periodo(suap)
    if ano is None:
        return
    dia = (datetime.now().weekday() + 1) % 7 + 1
    horarios = []
    for turma in suap.iterar_resultados(suap.ensino.obter_turmas_virtuais(ano, periodo)):
        for h in parse_horario(turma.get("horarios_de_aula", "")):
            if h["dia_num"] == dia:
                horarios.append(dict(h, disciplina=turma.get("descricao", "—"),
                                     local=", ".join(turma.get("locais_de_aula") or [])))
    tabela = Table("Turno", "Tempos de aula", "Disciplina", "Local")
    for h in ordenar_horarios(horarios):
        tabela.add_row(h["turno"], "-".join(map(str, h["horarios"])), h["disciplina"], h["local"])
    console.print(tabela if tabela.row_count else "Nenhuma aula hoje.")


def mostrar_eventos(suap):
    eventos = list(islice(suap.iterar_resultados(suap.ensino.obter_eventos()), 5))
    for evento in eventos:
        console.print(evento.get("nome") or evento.get("titulo") or "Evento")
        console.print(str(evento.get("data_inicio", "")))
        console.print(evento.get("apresentacao") or evento.get("descricao") or "")
    if not eventos:
        console.print("Nenhum evento disponível.")


def detalhar_progresso(suap):
    requisitos = suap.ensino.obter_requisitos_conclusao()
    if not requisitos:
        console.print("Progresso indisponível.")
        return
    console.print(f"Progresso do curso: {requisitos.get('percentual_cumprida', '—')}%")
    tabela = Table("Tipo", "Exigido", "Cumprido", "Pendente")
    for nome, dados in requisitos.items():
        if isinstance(dados, dict) and "ch_esperada" in dados:
            tabela.add_row(nome.replace("_", " "), *(str(dados.get(c, "—")) for c in
                            ("ch_esperada", "ch_cumprida", "ch_pendente")))
    console.print(tabela)


def menu(suap):
    acoes = {"1": mostrar_boletim_e_faltas, "2": mostrar_horario_hoje,
             "3": detalhar_progresso, "4": mostrar_eventos}
    while True:
        console.print("\n1. Boletim e faltas\n2. Horário de hoje\n3. Progresso do curso"
                      "\n4. Eventos\n5. Encerrar sessão e sair\n0. Sair (manter sessão)")
        opcao = console.input("Opção: ").strip()
        if opcao == "0":
            return
        if opcao == "5":
            clear_session()
            suap.logout()
            console.print("Sessão removida deste computador.")
            return
        if opcao not in acoes:
            console.print("Opção inválida.")
            continue
        try:
            acoes[opcao](suap)
        except SuapError as exc:
            console.print(f"Erro: {exc}")
        finally:
            if suap.refresh_token:
                save_session(suap.refresh_token)


def main():
    parser = argparse.ArgumentParser(description="Consulte o SUAP do IFRN pelo terminal.")
    parser.add_argument("--logout", action="store_true", help="remove a sessão local e sai")
    args = parser.parse_args()
    try:
        if args.logout:
            clear_session()
            console.print("Sessão local removida.")
            return
        console.print("Suapy · SUAP do IFRN")
        with Suap() as suap:
            suap.refresh_token = load_session()
            if suap.refresh_token:
                try:
                    suap.renovar_token()
                    save_session(suap.refresh_token)
                except SuapAuthError:
                    clear_session()
                    suap.logout()
                    console.print("Sessão expirada. Entre novamente.")
            if not suap.token:
                usuario = console.input("Matrícula: ")
                senha = getpass.getpass("Senha: ")
                suap.login(usuario, senha)
                save_session(suap.refresh_token)
            menu(suap)
    except (KeyboardInterrupt, EOFError):
        console.print("\nEncerrado.")
    except (SuapError, OSError) as exc:
        console.print(f"Erro: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
