# Alterações

## 1.4.1 — em preparação

- Prefixos de instalação preservados nos endpoints; paginação relativa à URL consultada.
- Validação de ano, período e status de mensagens antes das chamadas HTTP.
- Consultas diretas no CLI, exportação CSV/JSON e modo sem persistência de sessão.
- URLs alternativas no CLI sem reutilizar a sessão do IFRN.
- Teste opt-in com conta real e diagnóstico OIDC sem upload via execução manual.
- Página de documentação responsiva e workflow para GitHub Pages.

## 1.4.0 — 2026-09-09

- Python mínimo passa de 3.6 para 3.10; metadados migrados para pyproject.toml.
- Timeout de conexão/leitura, validação dos tokens e suporte a refresh token rotativo.
- Erros de autenticação preservados; HTTP 403 agora usa SuapAuthError.
- Fechamento explícito da sessão e suporte ao bloco with.
- Iteração explícita sobre páginas, sem alterar os retornos dos métodos existentes.
- Importação de Pandas sob demanda.
- Sessão do CLI gravada atomicamente, com permissões restritas em POSIX, e logout local.
- CLI unificado; períodos ordenados, turnos em ordem cronológica e remoção do alerta fixo de faltas.
- README revisado, logo do projeto, testes e workflows de CI/publicação.
- Redirecionamentos HTTP deixam de ser seguidos; configure diretamente a URL final do SUAP.
