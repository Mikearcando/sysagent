import subprocess
import requests
import psutil
import socket
import platform
from pathlib import Path
from datetime import datetime

TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": "Lees de inhoud van een bestand",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Pad naar het bestand"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Schrijf inhoud naar een bestand (maakt het bestand aan als het niet bestaat)",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Pad naar het bestand"},
                "content": {"type": "string", "description": "Inhoud om te schrijven"},
                "append": {"type": "boolean", "description": "True om toe te voegen, False om te overschrijven"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_directory",
        "description": "Geef een lijst van bestanden en mappen in een directory",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Pad naar de directory"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "fetch_url",
        "description": "Haal de inhoud op van een website of API endpoint",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "De URL om op te halen"},
                "method": {"type": "string", "description": "HTTP methode: GET of POST"},
                "headers": {"type": "object", "description": "HTTP headers als key-value pairs"},
                "body": {"type": "string", "description": "Request body voor POST requests"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "run_shell",
        "description": "Voer een shell-commando uit op het systeem",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Het shell-commando om uit te voeren"},
                "timeout": {"type": "integer", "description": "Timeout in seconden (standaard 30)"}
            },
            "required": ["command"]
        }
    },
    {
        "name": "get_system_info",
        "description": "Haal systeeminformatie op: CPU, RAM, schijfgebruik, OS, uptime",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "list_processes",
        "description": "Geef een lijst van draaiende processen gesorteerd op CPU of RAM gebruik",
        "input_schema": {
            "type": "object",
            "properties": {
                "sort_by": {"type": "string", "description": "Sorteren op: cpu, memory of name"},
                "limit": {"type": "integer", "description": "Aantal processen om terug te geven"},
                "filter_name": {"type": "string", "description": "Filter op procesnaam (optioneel)"}
            }
        }
    },
    {
        "name": "check_port",
        "description": "Controleer of een TCP poort open is op een host",
        "input_schema": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "Hostname of IP adres"},
                "port": {"type": "integer", "description": "Poortnummer"},
                "timeout": {"type": "integer", "description": "Timeout in seconden"}
            },
            "required": ["host", "port"]
        }
    },
    {
        "name": "ping_host",
        "description": "Ping een host om bereikbaarheid te controleren",
        "input_schema": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "Hostname of IP adres om te pingen"},
                "count": {"type": "integer", "description": "Aantal ping packets (standaard 4)"}
            },
            "required": ["host"]
        }
    },
    {
        "name": "get_network_interfaces",
        "description": "Geef informatie over netwerk-interfaces, IP-adressen en statistieken",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "read_log",
        "description": "Lees de laatste N regels van een logbestand",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Pad naar het logbestand"},
                "lines": {"type": "integer", "description": "Aantal regels om te lezen (standaard 100)"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "get_services",
        "description": "Haal informatie op over systeemservices (Windows services of systemd)",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter_name": {"type": "string", "description": "Filter op servicenaam (optioneel)"}
            }
        }
    }
]


def execute_tool(name: str, input_data: dict) -> str:
    tool_map = {
        "read_file": _read_file,
        "write_file": _write_file,
        "list_directory": _list_directory,
        "fetch_url": _fetch_url,
        "run_shell": _run_shell,
        "get_system_info": _get_system_info,
        "list_processes": _list_processes,
        "check_port": _check_port,
        "ping_host": _ping_host,
        "get_network_interfaces": _get_network_interfaces,
        "read_log": _read_log,
        "get_services": _get_services,
    }

    if name not in tool_map:
        return f"Onbekende tool: {name}"

    try:
        return tool_map[name](**input_data)
    except Exception as e:
        return f"Fout bij uitvoeren van {name}: {str(e)}"


def _read_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"Bestand niet gevonden: {path}"
    if not p.is_file():
        return f"Pad is geen bestand: {path}"
    try:
        content = p.read_text(encoding='utf-8', errors='replace')
        if len(content) > 10000:
            return content[:10000] + f"\n... (afgekapt, totaal {len(content)} tekens)"
        return content
    except Exception as e:
        return f"Fout bij lezen: {str(e)}"


def _write_file(path: str, content: str, append: bool = False) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    mode = 'a' if append else 'w'
    with open(path, mode, encoding='utf-8') as f:
        f.write(content)
    action = 'aangevuld' if append else 'geschreven'
    return f"Bestand {action}: {path} ({len(content)} tekens)"


def _list_directory(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"Map niet gevonden: {path}"
    items = []
    for item in sorted(p.iterdir()):
        kind = "map" if item.is_dir() else "bestand"
        size = ""
        if item.is_file():
            try:
                size = f" ({item.stat().st_size} bytes)"
            except Exception:
                pass
        items.append(f"[{kind}] {item.name}{size}")
    return "\n".join(items) if items else "(lege map)"


def _fetch_url(url: str, method: str = "GET", headers: dict = None, body: str = None) -> str:
    try:
        h = headers or {}
        if method.upper() == "POST":
            resp = requests.post(url, headers=h, data=body, timeout=15)
        else:
            resp = requests.get(url, headers=h, timeout=15)

        content = resp.text
        if len(content) > 5000:
            content = content[:5000] + f"\n... (afgekapt, totaal {len(resp.text)} tekens)"
        return f"Status: {resp.status_code}\nContent-Type: {resp.headers.get('Content-Type', 'onbekend')}\n\n{content}"
    except requests.exceptions.Timeout:
        return "Fout: Verzoek verlopen (timeout)"
    except Exception as e:
        return f"Fout bij ophalen URL: {str(e)}"


def _run_shell(command: str, timeout: int = 30) -> str:
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, timeout=timeout, encoding='utf-8', errors='replace'
            )
        else:
            result = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, timeout=timeout, executable='/bin/bash',
                encoding='utf-8', errors='replace'
            )

        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]: {result.stderr}"
        if len(output) > 5000:
            output = output[:5000] + "\n... (uitvoer afgekapt)"
        return output.strip() if output.strip() else f"(Geen uitvoer, exitcode: {result.returncode})"
    except subprocess.TimeoutExpired:
        return f"Commando verlopen na {timeout} seconden"
    except Exception as e:
        return f"Fout: {str(e)}"


def _get_system_info() -> str:
    lines = []

    lines.append(f"OS:           {platform.system()} {platform.release()} ({platform.version()})")
    lines.append(f"Hostname:     {platform.node()}")
    lines.append(f"Architectuur: {platform.machine()}")

    cpu_count = psutil.cpu_count()
    cpu_pct = psutil.cpu_percent(interval=1)
    cpu_freq = psutil.cpu_freq()
    freq_str = f"{cpu_freq.current:.0f} MHz" if cpu_freq else "onbekend"
    lines.append(f"CPU:          {cpu_count} kernen @ {freq_str}, gebruik: {cpu_pct}%")

    ram = psutil.virtual_memory()
    lines.append(f"RAM totaal:   {ram.total / (1024**3):.1f} GB")
    lines.append(f"RAM gebruikt: {ram.used / (1024**3):.1f} GB ({ram.percent}%)")
    lines.append(f"RAM vrij:     {ram.available / (1024**3):.1f} GB")

    lines.append("\nSchijven:")
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            lines.append(
                f"  {part.device} ({part.mountpoint}): "
                f"{usage.used/(1024**3):.1f} GB / {usage.total/(1024**3):.1f} GB ({usage.percent}%)"
            )
        except Exception:
            pass

    boot = datetime.fromtimestamp(psutil.boot_time())
    lines.append(f"\nOpgestart:    {boot.strftime('%Y-%m-%d %H:%M:%S')}")

    return "\n".join(lines)


def _list_processes(sort_by: str = "cpu", limit: int = 20, filter_name: str = None) -> str:
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
        try:
            info = p.info
            if filter_name and filter_name.lower() not in (info['name'] or '').lower():
                continue
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    sort_key = 'cpu_percent' if sort_by == 'cpu' else 'memory_percent' if sort_by == 'memory' else 'name'
    reverse = sort_by in ('cpu', 'memory')
    procs.sort(key=lambda x: x.get(sort_key) or 0 if reverse else x.get(sort_key) or '', reverse=reverse)
    procs = procs[:limit]

    lines = [f"{'PID':<8} {'Naam':<30} {'CPU%':<8} {'MEM%':<8} Status"]
    lines.append("-" * 68)
    for p in procs:
        lines.append(
            f"{p['pid']:<8} {(p['name'] or '')[:29]:<30} "
            f"{p['cpu_percent'] or 0:<8.1f} {p['memory_percent'] or 0:<8.2f} {p['status'] or ''}"
        )
    return "\n".join(lines)


def _check_port(host: str, port: int, timeout: int = 3) -> str:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return f"Poort {port} op {host} is OPEN"
    except socket.timeout:
        return f"Poort {port} op {host} is GESLOTEN (timeout)"
    except ConnectionRefusedError:
        return f"Poort {port} op {host} is GESLOTEN (verbinding geweigerd)"
    except Exception as e:
        return f"Fout bij controleren poort: {str(e)}"


def _ping_host(host: str, count: int = 4) -> str:
    if platform.system() == 'Windows':
        cmd = f"ping -n {count} {host}"
    else:
        cmd = f"ping -c {count} {host}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    output = result.stdout + result.stderr
    return output[:3000] if output else "Geen uitvoer van ping"


def _get_network_interfaces() -> str:
    lines = []
    stats = psutil.net_if_stats()
    for iface, addrs in psutil.net_if_addrs().items():
        iface_stats = stats.get(iface)
        status = "UP" if iface_stats and iface_stats.isup else "DOWN"
        lines.append(f"\nInterface: {iface} [{status}]")
        for addr in addrs:
            if addr.family == socket.AF_INET:
                lines.append(f"  IPv4: {addr.address} / {addr.netmask}")
            elif addr.family == socket.AF_INET6:
                lines.append(f"  IPv6: {addr.address}")
            elif addr.family == psutil.AF_LINK:
                lines.append(f"  MAC:  {addr.address}")

    net_io = psutil.net_io_counters()
    lines.append(f"\nNetwerk I/O totaal:")
    lines.append(f"  Verzonden:  {net_io.bytes_sent / (1024**2):.1f} MB")
    lines.append(f"  Ontvangen:  {net_io.bytes_recv / (1024**2):.1f} MB")
    return "\n".join(lines)


def _read_log(path: str, lines: int = 100) -> str:
    p = Path(path)
    if not p.exists():
        return f"Logbestand niet gevonden: {path}"
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            all_lines = f.readlines()
        last = all_lines[-lines:]
        return f"Laatste {len(last)} regels van {path}:\n" + "".join(last)
    except Exception as e:
        return f"Fout bij lezen logbestand: {str(e)}"


def _get_services(filter_name: str = None) -> str:
    if platform.system() == 'Windows':
        try:
            lines = [f"{'Naam':<45} {'Status':<12} Start type"]
            lines.append("-" * 75)
            for svc in psutil.win_service_iter():
                try:
                    info = svc.as_dict()
                    name = info['name']
                    if filter_name and filter_name.lower() not in name.lower():
                        continue
                    lines.append(f"{name[:44]:<45} {info['status']:<12} {info['start_type']}")
                except Exception:
                    pass
            return "\n".join(lines)
        except Exception:
            result = subprocess.run(
                'wmic service get Name,State,StartMode /format:csv',
                shell=True, capture_output=True, text=True, timeout=15
            )
            return result.stdout[:5000]
    else:
        result = subprocess.run(
            'systemctl list-units --type=service --no-pager',
            shell=True, capture_output=True, text=True, timeout=15
        )
        return result.stdout[:5000]
