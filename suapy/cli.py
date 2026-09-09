"""Interface de terminal para consultas acadêmicas."""

import argparse
import csv
import getpass
import io
import json
import os
import tempfile
import sys
from datetime import datetime
from itertools import islice
from pathlib import Path

from rich.console import Console
from rich.table import Table

from suapy import Suap, SuapAuthError, SuapError, parse_horario
from suapy.modules.ensino import validar_periodo

console = Console(markup=False, stderr=True)
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


def menu(suap, salvar_sessao=True):
    acoes = {"1": mostrar_boletim_e_faltas, "2": mostrar_horario_hoje,
             "3": detalhar_progresso, "4": mostrar_eventos}
    while True:
        sair = "Sair (manter sessão)" if salvar_sessao else "Sair"
        console.print("\n1. Boletim e faltas\n2. Horário de hoje\n3. Progresso do curso"
                      f"\n4. Eventos\n5. Encerrar sessão e sair\n0. {sair}")
        opcao = console.input("Opção: ").strip()
        if opcao == "0":
            return
        if opcao == "5":
            if salvar_sessao:
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
            if salvar_sessao and suap.refresh_token:
                save_session(suap.refresh_token)


def exportar(dados, formato):
    """Serializa registros sem dependência de Pandas."""
    if formato == "json":
        return json.dumps(dados, ensure_ascii=False, indent=2) + "\n"
    registros = dados if isinstance(dados, list) else [dados]
    if not all(isinstance(registro, dict) for registro in registros):
        raise ValueError("CSV exige registros em formato de objeto.")
    colunas = list(dict.fromkeys(chave for r in registros for chave in r))
    saida = io.StringIO(newline="")
    writer = csv.DictWriter(saida, fieldnames=colunas)
    writer.writeheader()
    for registro in registros:
        linha = {}
        for chave, valor in registro.items():
            if isinstance(valor, (dict, list)):
                valor = json.dumps(valor, ensure_ascii=False)
            # Evita interpretar textos da API como fórmulas em planilhas.
            if isinstance(valor, str) and valor.lstrip().startswith(("=", "+", "-", "@")):
                valor = "'" + valor
            linha[chave] = valor
        writer.writerow(linha)
    return saida.getvalue()


def executar_consulta(suap, args):
    ensino = suap.ensino
    consultas = {
        "boletim": lambda: ensino.obter_boletim(args.ano, args.periodo),
        "turmas": lambda: ensino.obter_turmas_virtuais(args.ano, args.periodo),
        "periodos": ensino.obter_periodos_letivos,
        "avaliacoes": ensino.obter_proximas_avaliacoes,
        "mensagens": lambda: ensino.obter_mensagens_aluno(args.status),
        "progresso": ensino.obter_requisitos_conclusao,
    }
    dados = consultas[args.comando]()
    if args.comando != "progresso":
        dados = list(suap.iterar_resultados(dados))
    if args.formato == "tabela":
        registros = dados if isinstance(dados, list) else [dados]
        if not registros:
            Console(markup=False).print("Nenhum registro disponível.")
            return
        colunas = list(dict.fromkeys(chave for r in registros for chave in r))
        tabela = Table(*colunas)
        for r in registros:
            tabela.add_row(*(str(r.get(c, "")) for c in colunas))
        Console(markup=False).print(tabela)
    else:
        texto = exportar(dados, args.formato)
        if args.saida:
            # Não sobrescreve exportações existentes; permissões restritas em POSIX.
            fd = os.open(args.saida, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as arquivo:
                arquivo.write(texto)
        else:
            sys.stdout.write(texto)


def criar_parser():
    parser = argparse.ArgumentParser(description="Consulte o SUAP pelo terminal.")
    def comuns(destino, sub=False):
        default = argparse.SUPPRESS if sub else False
        destino.add_argument("--sem-sessao", action="store_true", default=default,
                             help="não lê, grava ou remove a sessão salva")
        destino.add_argument("--url-base", default=argparse.SUPPRESS if sub else "https://suap.ifrn.edu.br",
                             help="URL da instituição; URLs alternativas não usam sessão em disco")
    comuns(parser)
    parser.add_argument("--logout", action="store_true", help="remove a sessão local e sai")
    comandos = parser.add_subparsers(dest="comando")
    for nome in ("boletim", "turmas", "periodos", "avaliacoes", "mensagens", "progresso"):
        sub = comandos.add_parser(nome)
        comuns(sub, sub=True)
        sub.add_argument("--formato", choices=("tabela", "json", "csv"), default="tabela")
        sub.add_argument("--saida", type=Path, help="novo arquivo para exportação CSV/JSON")
        if nome in ("boletim", "turmas"):
            sub.add_argument("--ano", required=True)
            sub.add_argument("--periodo", required=True)
        if nome == "mensagens":
            sub.add_argument("--status", choices=("nao_lidas", "lidas", "todas"), default="nao_lidas")
    return parser


def main():
    parser = criar_parser()
    args = parser.parse_args()
    if args.logout and (args.sem_sessao or args.comando):
        parser.error("--logout não pode ser combinado com consultas ou --sem-sessao.")
    if args.comando:
        if args.saida and args.formato == "tabela":
            parser.error("--saida exige --formato json ou csv.")
        if args.comando in ("boletim", "turmas"):
            try:
                args.ano, args.periodo = validar_periodo(args.ano, args.periodo)
            except ValueError as exc:
                parser.error(str(exc))
    salvar = not args.sem_sessao and args.url_base.rstrip('/') == "https://suap.ifrn.edu.br"
    try:
        if args.logout:
            clear_session()
            console.print("Sessão local removida.")
            return
        if not args.comando:
            console.print("Suapy · Consultas acadêmicas")
        with Suap(url_base=args.url_base) as suap:
            suap.refresh_token = load_session() if salvar else None
            if suap.refresh_token:
                try:
                    suap.renovar_token()
                    if salvar:
                        save_session(suap.refresh_token)
                except SuapAuthError:
                    if salvar:
                        clear_session()
                    suap.logout()
                    console.print("Sessão expirada. Entre novamente.")
            if not suap.token:
                usuario = console.input("Matrícula: ")
                senha = getpass.getpass("Senha: ")
                suap.login(usuario, senha)
                if salvar:
                    save_session(suap.refresh_token)
            if args.comando:
                try:
                    executar_consulta(suap, args)
                finally:
                    if salvar and suap.refresh_token:
                        save_session(suap.refresh_token)
            elif salvar:
                menu(suap)
            else:
                menu(suap, salvar_sessao=False)
    except (KeyboardInterrupt, EOFError):
        console.print("\nEncerrado.")
        raise SystemExit(130)
    except (SuapError, OSError, ValueError) as exc:
        console.print(f"Erro: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
