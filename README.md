# SysAgent — Autonome Systeembeheer Agent

Een zelfstandig werkende agent die taken analyseert, plant en uitvoert op je computer.
Aangedreven door Claude Sonnet via de Anthropic API, met een PHP/CSS/JS web dashboard.

---

## Installatie op Ubuntu Desktop LTS

### Vereisten controleren

```bash
python3 --version    # moet 3.10 of hoger zijn
php --version        # moet 8.x zijn
git --version
```

### 1. Systeempakketten installeren

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv php git curl
```

### 2. Project klonen of kopiëren

```bash
# Via git (als het project op een repo staat):
git clone <jouw-repo-url> ~/sysagent
cd ~/sysagent

# Of als je de bestanden al hebt, navigeer naar de map:
cd /pad/naar/agent
```

### 3. Python virtuele omgeving aanmaken

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> De omgeving activeren doe je elke nieuwe terminal-sessie met:
> `source venv/bin/activate`

### 4. Configuratie instellen

```bash
cp .env.example .env
nano .env
```

Vul je Anthropic API key in:

```
ANTHROPIC_API_KEY=sk-ant-jouw-key-hier
DATABASE_PATH=agent.db
API_HOST=0.0.0.0
API_PORT=5000
AGENT_POLL_INTERVAL=3
```

Sla op met `Ctrl+O`, sluit af met `Ctrl+X`.

API key ophalen via: https://console.anthropic.com/

### 5. Agent starten

```bash
source venv/bin/activate   # als de venv nog niet actief is
python3 main.py
```

Je ziet dan:

```
[DB] Database geinitialiseerd
[Agent] Gestart, wachten op taken...
[API] Server gestart op http://0.0.0.0:5000
```

### 6. Dashboard starten (tweede terminal)

```bash
cd /pad/naar/agent/dashboard
php -S localhost:8080
```

Open je browser en ga naar `http://localhost:8080`

---

## Autostart bij opstarten (optioneel)

### Agent als systemd service

Maak een service-bestand aan:

```bash
sudo nano /etc/systemd/system/sysagent.service
```

Inhoud (pas paden aan naar jouw situatie):

```ini
[Unit]
Description=SysAgent autonome agent
After=network.target

[Service]
Type=simple
User=JOUW_GEBRUIKERSNAAM
WorkingDirectory=/pad/naar/agent
ExecStart=/pad/naar/agent/venv/bin/python3 main.py
EnvironmentFile=/pad/naar/agent/.env
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Activeer de service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable sysagent
sudo systemctl start sysagent
sudo systemctl status sysagent
```

Logs bekijken:

```bash
journalctl -u sysagent -f
```

### Dashboard als systemd service

```bash
sudo nano /etc/systemd/system/sysagent-dashboard.service
```

```ini
[Unit]
Description=SysAgent PHP Dashboard
After=network.target

[Service]
Type=simple
User=JOUW_GEBRUIKERSNAAM
WorkingDirectory=/pad/naar/agent/dashboard
ExecStart=/usr/bin/php -S 0.0.0.0:8080
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable sysagent-dashboard
sudo systemctl start sysagent-dashboard
```

---

## Beschikbare tools

| Tool                     | Omschrijving                                      |
|--------------------------|---------------------------------------------------|
| `read_file`              | Bestand lezen                                     |
| `write_file`             | Bestand schrijven of aanvullen                    |
| `list_directory`         | Map-inhoud bekijken                               |
| `fetch_url`              | Website of API endpoint ophalen (GET/POST)        |
| `run_shell`              | Shell-commando uitvoeren (bash)                   |
| `get_system_info`        | CPU, RAM, schijf, OS, uptime                      |
| `list_processes`         | Draaiende processen (sorteren op CPU/RAM)         |
| `check_port`             | TCP poort controleren op een host                 |
| `ping_host`              | Host bereikbaarheid testen                        |
| `get_network_interfaces` | Netwerk interfaces, IP-adressen en statistieken   |
| `read_log`               | Laatste N regels van een logbestand               |
| `get_services`           | systemd services bekijken                         |

---

## Voorbeeldtaken voor Ubuntu/Linux

**Netwerk diagnostiek:**
```
Controleer of poort 22 (SSH), 80 (HTTP) en 443 (HTTPS)
open zijn op localhost. Ping ook 8.8.8.8 en rapporteer.
```

**Systeemrapport naar bestand:**
```
Maak een volledig systeemrapport en sla dit op als /tmp/sysrapport.txt.
Zet hierin: OS info, CPU gebruik, RAM gebruik, schijfruimte
en de top 10 processen op CPU gebruik.
```

**Log analyse:**
```
Lees de laatste 100 regels van /var/log/syslog
en geef een samenvatting van eventuele fouten of waarschuwingen.
```

**Service controle:**
```
Geef een overzicht van alle systemd services die gefaald zijn
en probeer te achterhalen wat de oorzaak is.
```

**Schijfruimte analyse:**
```
Zoek de 10 grootste bestanden en mappen in /var/log
en geef aan welke opgeruimd kunnen worden.
```

---

## Problemen oplossen

**`ModuleNotFoundError`** — venv niet actief:
```bash
source venv/bin/activate
```

**`Permission denied` bij shell-commando's** — gebruik `sudo` in de taakinstructie,
of voeg de gebruiker toe aan de juiste groepen (bijv. `adm` voor logbestanden):
```bash
sudo usermod -aG adm $USER
# daarna opnieuw inloggen
```

**Poort 5000 al in gebruik:**
```bash
sudo lsof -i :5000
# pas API_PORT in .env aan naar bijv. 5001
```

**PHP niet gevonden:**
```bash
sudo apt install php-cli
```

---

## REST API endpoints

| Methode  | Pad                               | Omschrijving              |
|----------|-----------------------------------|---------------------------|
| GET      | `/api/tasks`                      | Alle taken ophalen        |
| GET      | `/api/tasks?status=pending`       | Gefilterd op status       |
| POST     | `/api/tasks`                      | Nieuwe taak aanmaken      |
| GET      | `/api/tasks/{id}`                 | Taak details              |
| DELETE   | `/api/tasks/{id}`                 | Taak verwijderen          |
| GET      | `/api/tasks/{id}/logs`            | Logs ophalen              |
| GET      | `/api/tasks/{id}/logs?since_id=N` | Alleen nieuwe logs        |
| GET      | `/api/system`                     | CPU/RAM/schijf stats      |
| GET      | `/api/agent/status`               | Agent actief of gestopt   |

---

## Dashboard sneltoetsen

| Toets   | Actie                  |
|---------|------------------------|
| Ctrl+N  | Nieuwe taak aanmaken   |
| Escape  | Modal / detail sluiten |

---

## Vereisten

- Ubuntu 22.04 LTS of 24.04 LTS
- Python 3.10+
- PHP 8.x (`php-cli`)
- Anthropic API key — https://console.anthropic.com/
