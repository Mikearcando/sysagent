const API = (typeof API_Base !== 'undefined' ? API_Base : null) || 'http://localhost:5000';

let currentTaskId = null;
let lastLogId = 0;
let currentFilter = '';
let logPollTimer = null;

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    fetchTasks();
    fetchStats();
    fetchAgentStatus();

    setInterval(fetchTasks,       3000);
    setInterval(fetchStats,       5000);
    setInterval(fetchAgentStatus, 4000);

    document.querySelectorAll('.filter').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.s;
            fetchTasks();
        });
    });

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') { closeModal(); closeDetail(); }
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') { e.preventDefault(); openModal(); }
    });
});

// ── API helpers ───────────────────────────────────────────────────────────────

async function api(path, opts = {}) {
    const r = await fetch(API + path, {
        headers: { 'Content-Type': 'application/json' },
        ...opts
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
}

// ── Data fetching ─────────────────────────────────────────────────────────────

async function fetchTasks() {
    try {
        const url = currentFilter ? `/api/tasks?status=${currentFilter}` : '/api/tasks';
        const tasks = await api(url);
        renderTasks(tasks);
        updateCounts(tasks);
    } catch (e) { /* network not ready */ }
}

async function fetchStats() {
    try {
        const s = await api('/api/system');
        setGauge('cpu',  s.cpu_percent);
        setGauge('ram',  s.ram_percent);
        setGauge('disk', s.disk_percent);
        document.getElementById('ram-detail').textContent  = `${s.ram_used_gb} GB / ${s.ram_total_gb} GB`;
        document.getElementById('disk-detail').textContent = `${s.disk_used_gb} GB / ${s.disk_total_gb} GB`;
    } catch (e) { /* ignore */ }
}

async function fetchAgentStatus() {
    const badge = document.getElementById('agent-status');
    const lbl   = badge.querySelector('.badge-label');
    try {
        const s = await api('/api/agent/status');
        badge.className = 'agent-badge ' + (s.running ? 'badge-running' : 'badge-stopped');
        lbl.textContent  = s.running ? 'Agent actief' : 'Agent gestopt';
    } catch (e) {
        badge.className = 'agent-badge badge-stopped';
        lbl.textContent  = 'Geen verbinding';
    }
}

// ── Gauges & counts ───────────────────────────────────────────────────────────

function setGauge(name, pct) {
    const bar = document.getElementById(`${name}-bar`);
    const val = document.getElementById(`${name}-val`);
    bar.style.width = pct + '%';
    bar.className   = 'gauge-fill' + (pct > 90 ? ' danger' : pct > 70 ? ' warn' : '');
    val.textContent = Math.round(pct) + '%';
}

function updateCounts(visibleTasks) {
    api('/api/tasks').then(all => {
        const c = { pending: 0, running: 0, completed: 0, failed: 0 };
        all.forEach(t => { if (c[t.status] !== undefined) c[t.status]++; });
        document.getElementById('cnt-pending').textContent   = c.pending;
        document.getElementById('cnt-running').textContent   = c.running;
        document.getElementById('cnt-completed').textContent = c.completed;
        document.getElementById('cnt-failed').textContent    = c.failed;
    }).catch(() => {});
}

// ── Task list rendering ───────────────────────────────────────────────────────

function renderTasks(tasks) {
    const box = document.getElementById('task-list');
    if (!tasks.length) {
        box.innerHTML = '<div class="empty-msg">Geen taken gevonden</div>';
        return;
    }

    box.innerHTML = tasks.map(t => `
        <div class="task-card${t.id === currentTaskId ? ' active' : ''}"
             onclick="selectTask(${t.id})">
            <div class="tc-body">
                <div class="tc-title">${esc(t.title)}</div>
                <div class="tc-desc">${esc(t.description)}</div>
                <div class="tc-foot">
                    <span class="task-badge s-${t.status}">${statusLabel(t.status)}</span>
                    ${t.status === 'running' ? '<span class="pulse"><span class="pulse-dot"></span>Bezig</span>' : ''}
                    ${t.priority === 2 ? '<span class="prio p2">HOOG</span>' : ''}
                    ${t.priority === 3 ? '<span class="prio p3">KRITIEK</span>' : ''}
                </div>
            </div>
            <div class="tc-side">
                <span class="tc-time">${fmtTime(t.created_at)}</span>
                <button class="del-btn" onclick="deleteTask(event,${t.id})">Verwijder</button>
            </div>
        </div>
    `).join('');
}

// ── Task detail ───────────────────────────────────────────────────────────────

async function selectTask(id) {
    currentTaskId = id;
    lastLogId = 0;

    document.querySelectorAll('.task-card').forEach(c => c.classList.remove('active'));
    document.querySelector(`.task-card[onclick="selectTask(${id})"]`)?.classList.add('active');

    const panel = document.getElementById('detail');
    panel.classList.remove('hidden');
    document.getElementById('log-box').innerHTML = '';
    document.getElementById('log-cnt').textContent = '';

    try {
        const t = await api(`/api/tasks/${id}`);
        renderDetail(t);
        await pollLogs(id);

        if (logPollTimer) clearInterval(logPollTimer);
        if (t.status === 'running' || t.status === 'pending') {
            logPollTimer = setInterval(() => pollLogs(id), 2000);
        }
    } catch (e) { console.error(e); }
}

function renderDetail(t) {
    document.getElementById('d-title').textContent = t.title;
    document.getElementById('d-desc').textContent  = t.description;
    document.getElementById('d-time').textContent  = fmtTime(t.created_at);

    const badge = document.getElementById('d-status');
    badge.className   = `task-badge s-${t.status}`;
    badge.textContent = statusLabel(t.status);

    const rw = document.getElementById('d-result-wrap');
    if (t.result || t.error) {
        rw.classList.remove('hidden');
        document.getElementById('d-result').textContent = t.result || t.error;
    } else {
        rw.classList.add('hidden');
    }
}

async function pollLogs(taskId) {
    if (taskId !== currentTaskId) return;
    try {
        const logs = await api(`/api/tasks/${taskId}/logs?since_id=${lastLogId}`);
        if (logs.length) {
            const box = document.getElementById('log-box');
            const atBottom = box.scrollHeight - box.clientHeight <= box.scrollTop + 20;

            logs.forEach(l => {
                const row = document.createElement('div');
                row.className = 'log-row';
                row.innerHTML = `
                    <span class="l-time">${fmtLogTime(l.timestamp)}</span>
                    <span class="l-lvl ${l.level}">${l.level.toUpperCase()}</span>
                    <span class="l-msg">${esc(l.message)}</span>
                `;
                box.appendChild(row);
                lastLogId = Math.max(lastLogId, l.id);
            });

            if (atBottom) box.scrollTop = box.scrollHeight;
            document.getElementById('log-cnt').textContent =
                `(${box.querySelectorAll('.log-row').length})`;
        }

        // Refresh detail panel when task finishes
        const t = await api(`/api/tasks/${taskId}`);
        if (t.status !== 'running' && t.status !== 'pending') {
            if (logPollTimer) { clearInterval(logPollTimer); logPollTimer = null; }
            renderDetail(t);
            fetchTasks();
        }
    } catch (e) { /* ignore transient errors */ }
}

function closeDetail() {
    currentTaskId = null;
    if (logPollTimer) { clearInterval(logPollTimer); logPollTimer = null; }
    document.getElementById('detail').classList.add('hidden');
    document.getElementById('log-box').innerHTML = '';
    document.querySelectorAll('.task-card').forEach(c => c.classList.remove('active'));
}

function clearLogs() {
    lastLogId = 0;
    document.getElementById('log-box').innerHTML = '';
    document.getElementById('log-cnt').textContent = '';
    if (currentTaskId) pollLogs(currentTaskId);
}

// ── Create task ───────────────────────────────────────────────────────────────

function openModal() {
    document.getElementById('modal').classList.remove('hidden');
    document.getElementById('f-title').focus();
}

function closeModal() {
    document.getElementById('modal').classList.add('hidden');
    document.getElementById('task-form').reset();
}

async function submitTask(e) {
    e.preventDefault();
    const title    = document.getElementById('f-title').value.trim();
    const desc     = document.getElementById('f-desc').value.trim();
    const priority = parseInt(document.getElementById('f-prio').value);
    try {
        const res = await api('/api/tasks', {
            method: 'POST',
            body: JSON.stringify({ title, description: desc, priority })
        });
        closeModal();
        toast('Taak aangemaakt', 'ok');
        await fetchTasks();
        setTimeout(() => selectTask(res.id), 300);
    } catch (e) {
        toast('Aanmaken mislukt', 'err');
    }
}

// ── Delete ────────────────────────────────────────────────────────────────────

async function deleteTask(e, id) {
    e.stopPropagation();
    if (!confirm('Taak verwijderen?')) return;
    try {
        await api(`/api/tasks/${id}`, { method: 'DELETE' });
        if (currentTaskId === id) closeDetail();
        fetchTasks();
        toast('Taak verwijderd', 'ok');
    } catch (e) {
        toast('Verwijderen mislukt', 'err');
    }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function esc(s) {
    if (!s) return '';
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function statusLabel(s) {
    return { pending:'Wachtend', running:'Actief', completed:'Voltooid', failed:'Mislukt' }[s] || s;
}

function fmtTime(ts) {
    if (!ts) return '';
    return new Date(ts).toLocaleString('nl-NL', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' });
}

function fmtLogTime(ts) {
    if (!ts) return '';
    return new Date(ts).toLocaleTimeString('nl-NL', { hour:'2-digit', minute:'2-digit', second:'2-digit' });
}

function toast(msg, type) {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = `toast ${type} show`;
    setTimeout(() => el.classList.remove('show'), 2800);
}
