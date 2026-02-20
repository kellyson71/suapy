import re

def parse_horario(horario_str):
    """
    Parses SUAP schedule strings like '2V34 / 4V56'.
    Returns a list of dicts with day, shift, and slots.
    """
    if not horario_str:
        return []
    
    # Example: '2V34 / 4V56' -> ['2V34', '4V56']
    parts = [p.strip() for p in horario_str.split('/')]
    results = []
    
    dias_map = {
        '2': 'Segunda',
        '3': 'Terça',
        '4': 'Quarta',
        '5': 'Quinta',
        '6': 'Sexta',
        '7': 'Sábado',
        '1': 'Domingo'
    }
    
    turnos_map = {
        'M': 'Manhã',
        'V': 'Tarde',
        'N': 'Noite'
    }

    for part in parts:
        # Match pattern: Day(s) Turn Slot(s)
        # Some are single days: 2V34
        # Some might be 23V12
        match = re.match(r'([1-7]+)([MVN])([1-7]+)', part)
        if match:
            dias_chars, turno_char, slots_chars = match.groups()
            for d in dias_chars:
                results.append({
                    'dia_semana': dias_map.get(d, 'Desconhecido'),
                    'dia_num': int(d),
                    'turno': turnos_map.get(turno_char, 'Desconhecido'),
                    'horarios': [int(s) for s in slots_chars]
                })
    return results
