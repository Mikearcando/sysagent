import threading
import time
import signal
import sys
from agent import database
from agent import core
from api.routes import app, set_agent_running
from config import API_HOST, API_PORT, AGENT_POLL_INTERVAL

_running = True


def agent_loop():
    set_agent_running(True)
    print("[Agent] Gestart, wachten op taken...")

    while _running:
        try:
            tasks = database.get_tasks(status='pending')
            for task in tasks:
                if not _running:
                    break
                print(f"[Agent] Uitvoeren: {task['title']} (ID: {task['id']})")
                core.run_task(task['id'])
                print(f"[Agent] Voltooid:  {task['title']} (ID: {task['id']})")
        except Exception as e:
            print(f"[Agent] Fout in hoofdlus: {e}")

        time.sleep(AGENT_POLL_INTERVAL)

    set_agent_running(False)
    print("[Agent] Gestopt")


def signal_handler(sig, frame):
    global _running
    print("\n[Systeem] Afsluiten...")
    _running = False
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    database.init_db()
    print("[DB] Database geinitialiseerd")

    agent_thread = threading.Thread(target=agent_loop, daemon=True)
    agent_thread.start()

    print(f"[API] Server gestart op http://{API_HOST}:{API_PORT}")
    print(f"[Dashboard] Open http://localhost:8080 na: cd dashboard && php -S localhost:8080")
    app.run(host=API_HOST, port=API_PORT, debug=False, use_reloader=False)
