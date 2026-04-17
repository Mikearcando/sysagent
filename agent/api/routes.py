import platform
import psutil
from flask import Flask, jsonify, request
from flask_cors import CORS
from agent import database

app = Flask(__name__)
CORS(app)

_agent_running = False


def set_agent_running(running: bool):
    global _agent_running
    _agent_running = running


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    status = request.args.get('status')
    return jsonify(database.get_tasks(status))


@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.json or {}
    title = (data.get('title') or '').strip()
    description = (data.get('description') or '').strip()
    priority = int(data.get('priority', 1))

    if not title or not description:
        return jsonify({'error': 'Titel en beschrijving zijn verplicht'}), 400

    task_id = database.create_task(title, description, priority)
    return jsonify({'id': task_id, 'message': 'Taak aangemaakt'}), 201


@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = database.get_task(task_id)
    if not task:
        return jsonify({'error': 'Taak niet gevonden'}), 404
    return jsonify(task)


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    database.delete_task(task_id)
    return jsonify({'message': 'Taak verwijderd'})


@app.route('/api/tasks/<int:task_id>/logs', methods=['GET'])
def get_logs(task_id):
    since_id = request.args.get('since_id', 0, type=int)
    return jsonify(database.get_logs(task_id, since_id))


@app.route('/api/system', methods=['GET'])
def get_system():
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()

    disk_path = 'C:/' if platform.system() == 'Windows' else '/'
    try:
        disk = psutil.disk_usage(disk_path)
        disk_pct = disk.percent
        disk_used = round(disk.used / (1024**3), 1)
        disk_total = round(disk.total / (1024**3), 1)
    except Exception:
        disk_pct = disk_used = disk_total = 0

    return jsonify({
        'cpu_percent': cpu,
        'ram_percent': ram.percent,
        'ram_used_gb': round(ram.used / (1024**3), 1),
        'ram_total_gb': round(ram.total / (1024**3), 1),
        'disk_percent': disk_pct,
        'disk_used_gb': disk_used,
        'disk_total_gb': disk_total,
    })


@app.route('/api/agent/status', methods=['GET'])
def agent_status():
    return jsonify({'running': _agent_running})
