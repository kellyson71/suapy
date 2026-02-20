from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from suapy import Suap, parse_horario
import getpass
import sys
from datetime import datetime

console = Console()

def print_header():
    console.print(Panel.fit("[bold green]Suapy CLI[/bold green] - Central do Estudante IFRN", border_style="green"))

def do_login():
    suap = Suap()
    # Para testes, podemos usar os dados fornecidos ou pedir ao usuário
    # Mas como o usuário quer testar a lib, vamos pedir.
    usuario = console.input("[bold cyan]Matrícula SUAP:[/bold cyan] ")
    senha = getpass.getpass("Senha: ")
    
    with console.status("Autenticando...", spinner="dots"):
        try:
            suap.login(usuario, senha)
            aluno = suap.ensino.obter_dados_aluno()
            console.print(f"\n✅ [bold green]Login bem-sucedido![/bold green] Olá, [bold]{aluno.get('nome_usual')}[/bold]")
            console.print(f"Curso: {aluno.get('curso')}")
            return suap, aluno
        except Exception as e:
            console.print(f"\n❌ [bold red]Erro ao logar:[/bold red] {e}")
            sys.exit(1)

def escolher_periodo(suap):
    periodos = suap.ensino.obter_periodos_letivos()
    if not periodos or 'results' not in periodos:
        console.print("[yellow]Nenhum período letivo encontrado.[/yellow]")
        return None, None
        
    lista_periodos = periodos['results'][:4] # Pega os 4 mais recentes
    
    console.print("\n[bold cyan]Selecione o período letivo:[/bold cyan]")
    for i, p in enumerate(lista_periodos):
        console.print(f"{i + 1}. [blue]{p['ano_letivo']}.{p['periodo_letivo']}[/blue]")
        
    escolha = console.input("\nPeríodo (padrão 1): ")
    idx = 0
    if escolha.isdigit() and 1 <= int(escolha) <= len(lista_periodos):
        idx = int(escolha) - 1
        
    p = lista_periodos[idx]
    return p['ano_letivo'], p['periodo_letivo']

def mostrar_boletim_e_faltas(suap):
    ano, periodo = escolher_periodo(suap)
    if not ano: return
    
    console.print(f"\n[bold blue]📚 Boletim e Faltas - Semestre {ano}.{periodo}[/bold blue]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Disciplina", ratio=3)
    table.add_column("Média", justify="center")
    table.add_column("Faltas", justify="center")
    table.add_column("Situação")

    with console.status("Buscando boletim...", spinner="dots"):
        response = suap.ensino.obter_boletim(ano, periodo)
        boletim = response.get('results', []) if isinstance(response, dict) else response
        
    if not boletim:
        console.print("[yellow]Nenhum dado de boletim para este semestre.[/yellow]")
        return
        
    for d in boletim:
        faltas = d.get('numero_faltas', 0)
        situacao = d.get('situacao', 'Cursando')
        media = d.get('media_final_disciplina', '-')
        
        falta_color = "red" if faltas > 15 else "green"
        table.add_row(
            d.get('disciplina', 'N/A'),
            str(media),
            f"[{falta_color}]{faltas}[/{falta_color}]",
            situacao
        )
        
    console.print(table)

def mostrar_horario_hoje(suap):
    ano, periodo = escolher_periodo(suap)
    if not ano: return
    
    # Dia da semana (1-7, 1=Segunda?) -> datetime weekday is 0-6 (0=Segunda)
    hoje_fds = datetime.now().weekday() + 2 # 2=Segunda, 3=Terça... 8=Domingo?
    if hoje_fds > 7: hoje_fds = 1 # Domingo
    
    dias_semana = {2: "Segunda", 3: "Terça", 4: "Quarta", 5: "Quinta", 6: "Sexta", 7: "Sábado", 1: "Domingo"}
    nome_dia = dias_semana.get(hoje_fds)

    console.print(f"\n[bold blue]📅 Horário de Hoje ({nome_dia})[/bold blue]")

    with console.status("Buscando turmas...", spinner="dots"):
        turmas = suap.ensino.obter_turmas_virtuais(ano, periodo)
        if 'results' not in turmas: return

    horario_hoje = []
    for t in turmas['results']:
        h_str = t.get('horarios_de_aula', '')
        Parsed = parse_horario(h_str)
        for h in Parsed:
            if h['dia_num'] == hoje_fds:
                horario_hoje.append({
                    'disciplina': t.get('descricao'),
                    'turno': h['turno'],
                    'horarios': h['horarios'],
                    'local': ", ".join(t.get('locais_de_aula', []))
                })

    if not horario_hoje:
        console.print("[green]Nenhuma aula hoje! Aproveite.[/green]")
        return

    # Sort by shift and slots
    horario_hoje.sort(key=lambda x: (x['turno'], x['horarios'][0]))

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Turno")
    table.add_column("Horário")
    table.add_column("Disciplina")
    table.add_column("Local")

    for h in horario_hoje:
        slots = "-".join(map(str, h['horarios']))
        table.add_row(h['turno'], slots, h['disciplina'], h['local'])
    
    console.print(table)

def mostrar_eventos(suap):
    console.print(f"\n[bold blue]📣 Eventos e Avisos Institucionais[/bold blue]")
    with console.status("Buscando eventos...", spinner="dots"):
        eventos = suap.ensino.obter_eventos()
    
    if not eventos or 'results' not in eventos or not eventos['results']:
        console.print("[yellow]Nenhum evento recente.[/yellow]")
        return
        
    for ev in eventos['results'][:5]: # Mostra os 5 primeiros
        title = ev.get('titulo')
        data = ev.get('data_inicio')
        console.print(Panel(f"{ev.get('descricao')}\n\n[bold]Data:[/bold] {data}", title=f"[bold]{title}[/bold]"))

def detalhar_progresso(suap):
    console.print(f"\n[bold blue]🎓 Progresso do Curso[/bold blue]")
    with console.status("Buscando progresso...", spinner="dots"):
        reqs = suap.ensino.obter_requisitos_conclusao()
    
    if not reqs:
        console.print("Dados indisponíveis.")
        return

    # No SUAP, os campos variam. Vamos tentar extrair os mais comuns.
    perc = reqs.get('percentual_cumprida', '0')
    console.print(f"Progresso Geral: [bold green]{perc}%[/bold green]")
    
    table = Table(title="Carga Horária")
    table.add_column("Tipo")
    table.add_column("Exigido")
    table.add_column("Cumprido")
    table.add_column("Pendente")

    for key, val in reqs.items():
        if isinstance(val, dict) and 'ch_esperada' in val:
            name = key.replace('_', ' ').title()
            table.add_row(name, f"{val['ch_esperada']}h", f"{val['ch_cumprida']}h", f"{val['ch_pendente']}h")
            
    console.print(table)

def menu(suap):
    while True:
        console.print("\n[bold cyan]O que deseja fazer?[/bold cyan]")
        console.print("1. [blue]Resumo Completo (Faltas e Notas)[/blue]")
        console.print("2. [magenta]Ver Horário de Hoje[/magenta]")
        console.print("3. [yellow]Progresso do Curso (Horas)[/yellow]")
        console.print("4. [green]Eventos e Avisos[/green]")
        console.print("0. [red]Sair[/red]")
        
        op = console.input("\nEscolha uma opção: ")
        
        try:
            if op == "1":
                mostrar_boletim_e_faltas(suap)
            elif op == "2":
                mostrar_horario_hoje(suap)
            elif op == "3":
                detalhar_progresso(suap)
            elif op == "4":
                mostrar_eventos(suap)
            elif op == "0":
                console.print("Saindo... Bons estudos! 🤓")
                break
            else:
                console.print("[red]Opção inválida.[/red]")
        except Exception as e:
            console.print(f"[red]Erro na operação:[/red] {e}")

if __name__ == "__main__":
    print_header()
    suap, aluno = do_login()
    menu(suap)
