# SysAgent — Project geheugen voor Claude

## Wat is dit project?

Een autonome systeembeheer agent voor Windows. De agent krijgt taken via een web dashboard,
voert ze zelfstandig uit met tools (bestanden, shell, web, netwerk), en rapporteert de resultaten.
Taal van communicatie met de gebruiker: **Nederlands**.

---

## Technische stack

| Laag       | Technologie                          |
|------------|--------------------------------------|
| Agent lus  | Python 3.10+, `anthropic` SDK        |
| REST API   | Flask + flask-cors                   |
| Database   | SQLite (WAL mode), bestand: agent.db |
| Dashboard  | PHP 8 + vanilla JS + CSS             |
| Systeem    | psutil, subprocess, requests         |

---

## Bestandsstructuur

```
main.py               →  Entry point (start agent thread + Flask)
config.py             →  Laadt .env variabelen
agent/
  core.py             →  run_task(): Claude API loop met tool use
  tools.py            →  12 tool-implementaties + TOOL_DEFINITIONS
  database.py         →  SQLite CRUD voor tasks en task_logs
api/
  routes.py           →  Flask endpoints, set_agent_running()
dashboard/
  index.php           →  Hoofd-dashboard pagina
  css/style.css       →  Dark theme (GitHub-stijl kleuren)
  js/app.js           →  Polling, taakbeheer, log-streaming
.env                  →  ANTHROPIC_API_KEY (niet committen!)
agent.db              →  SQLite database (automatisch aangemaakt)
```

---

## Datamodel

```sql
tasks (id, title, description, status, priority, created_at,
       started_at, completed_at, result, error)

task_logs (id, task_id, timestamp, level, message)
-- levels: info | agent | tool | result | error
```

Status-flow: `pending` → `running` → `completed` | `failed`

---

## Agent-lus (core.py)

- Model: `claude-sonnet-4-6`
- Max iteraties per taak: 25
- System prompt: Nederlands, methodisch werken
- Tool use: Claude roept tools aan, Python voert ze uit, resultaat terug naar Claude
- Elke stap wordt gelogd naar SQLite

---

## Beschikbare tools

`read_file`, `write_file`, `list_directory`, `fetch_url`, `run_shell`,
`get_system_info`, `list_processes`, `check_port`, `ping_host`,
`get_network_interfaces`, `read_log`, `get_services`

---

## REST API (Flask, poort 5000)

- `GET/POST /api/tasks` — taken ophalen of aanmaken
- `GET/DELETE /api/tasks/{id}` — detail of verwijderen
- `GET /api/tasks/{id}/logs?since_id=N` — live log polling
- `GET /api/system` — CPU/RAM/schijf stats
- `GET /api/agent/status` — is de agent-thread actief?

Dashboard draait op poort **8080** (`php -S localhost:8080` in `/dashboard`).

---

## Belangrijke aandachtspunten

- `.env` bevat de API key — nooit committen, staat niet in git
- `agent.db` wordt automatisch aangemaakt bij eerste start
- De agent-lus draait als daemon thread naast Flask
- SQLite WAL mode zorgt voor thread-safe reads/writes
- `run_shell` voert commando's uit met `shell=True` — bewust, dit is een sysadmin tool
- Op Windows: schijfstats via `C:/`, shell via `subprocess` zonder `/bin/bash`
- Dashboard JS pollt elke 3 sec taken, 5 sec stats, 2 sec logs (alleen bij actieve taak)

---

## Uitbreidingsideen (nog niet gebouwd)

- Geplande taken (cron-stijl)
- E-mail notificaties bij voltooide taken
- Meerdere taken tegelijk uitvoeren (worker pool)
- Authenticatie op het dashboard
- Taak-templates opslaan
