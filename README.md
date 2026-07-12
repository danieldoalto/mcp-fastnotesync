# fast-note-sync-mcp

Servidor MCP em Python para expor a REST API do Fast Note Sync como ferramentas MCP via `FastMCP`.

O projeto funciona como um wrapper entre clientes MCP e o backend `fast-note-sync-service`, permitindo consultar e editar o vault `_Obsidian` por `stdio` ou via transporte HTTP do `fastmcp`.

## Visao Geral

Fluxo principal:

```text
Cliente MCP
  -> server.py (FastMCP + httpx)
  -> REST API Fast Note Sync
  -> vault _Obsidian
```

O arquivo principal do projeto e `server.py`, que:

- carrega configuracao de `.env`
- monta headers obrigatorios da API
- encapsula chamadas HTTP com `httpx`
- publica as tools MCP com `@mcp.tool`

## Requisitos

- Python 3.11 ou superior
- acesso ao backend Fast Note Sync
- token valido em `API_TOKEN`

Dependencias Python usadas pelo projeto:

- `fastmcp`
- `httpx`

## Instalacao

Exemplo com `venv`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastmcp httpx
```

## Configuracao

O projeto le automaticamente o arquivo `.env` no mesmo diretorio do `server.py`.

Comece copiando o arquivo de exemplo:

```bash
cp .env.example .env
```

Exemplo:

```env
API_BASE_URL=http://seu-servidor:9009/api
API_TOKEN=seu_token_aqui
API_TIMEOUT_SECONDS=20
```

Variaveis suportadas:

- `API_BASE_URL`: URL base da REST API
- `API_TOKEN`: token Bearer obrigatorio
- `API_TIMEOUT_SECONDS`: timeout das requisicoes HTTP

Observacoes:

- se `API_TOKEN` nao estiver definido, o `server.py` falha no startup
- o arquivo `.env` esta ignorado no `.gitignore`

## Execucao

Rodar diretamente com Python:

```bash
.venv/bin/python server.py
```

Esse modo e o mais comum para clientes MCP locais via `stdio`.

## Transporte HTTP

Para expor o MCP via HTTP:

```bash
fastmcp run server.py:mcp --transport http --host 0.0.0.0 --port 8001
```

## Exemplo De Configuracao MCP

Exemplo generico para clientes que aceitam processo Python:

```json
{
  "mcpServers": {
    "fast-note-sync": {
      "type": "python",
      "command": "/caminho/para/.venv/bin/python",
      "args": [
        "/caminho/para/fast-note-sync-mcp/server.py"
      ]
    }
  }
}
```

Exemplo de configuracao no Hermes:

```yaml
mcp_servers:
  fast-note-sync:
    command: /caminho/para/.venv/bin/python
    args:
      - /caminho/para/fast-note-sync-mcp/server.py
    enabled: true
```

## Tools Expostas

O `server.py` atualmente expoe 36 tools MCP, agrupadas nestas categorias:

- Sistema: `health_check`, `get_version`, `get_webgui_config`, `get_user_info`
- Vaults: `list_vaults`, `get_vault_detail`
- Pastas: `get_folder_info`, `create_folder`, `delete_folder`, `get_folder_tree`, `list_folders`, `list_folder_notes`
- Notas leitura: `get_note`, `search_notes`, `get_note_outlinks`, `get_note_backlinks`
- Notas escrita: `create_or_update_note`, `append_to_note`, `prepend_to_note`, `replace_in_note`, `delete_note`, `restore_note`
- Frontmatter: `set_note_frontmatter`, `delete_note_frontmatter`
- Organizacao: `move_note`, `rename_note`
- Historico: `get_note_history`, `get_note_history_detail`
- Arquivos: `get_file_list`, `get_file_info`
- Outras: `list_shares`, `get_storage_configs`, `get_enabled_storage_types`, `get_git_sync_configs`, `get_system_info`, `get_backup_configs`

## Comportamento Importante

- `set_note_frontmatter` esta funcional e envia o valor como lista de um item no payload de update
- `replace_in_note` suporta busca literal e regex
- `move_note` e `rename_note` usam o mesmo endpoint backend
- algumas tools podem depender das permissoes do token usado no backend

## Teste Rapido

Validar import e carregamento do `.env`:

```bash
.venv/bin/python -c "import server; print(server.API_BASE_URL); print(bool(server.API_TOKEN))"
```

Testar health check:

```bash
.venv/bin/python - <<'PY'
import json
import server
print(json.dumps(server.health_check(), ensure_ascii=False, indent=2))
PY
```

## Estrutura Atual

```text
fast-note-sync-mcp/
  .env
  .env.example
  .gitignore
  server.py
  README.md
```

## Seguranca

- nao comite o `.env`
- trate `API_TOKEN` como credencial sensivel
- se o token ja tiver sido exposto anteriormente, faca rotacao

## Desenvolvimento

Como o projeto esta concentrado em um unico arquivo, a manutencao tipica envolve:

- adicionar ou ajustar uma tool em `server.py`
- validar a chamada contra a API real
- atualizar este `README.md` se o contrato mudar
