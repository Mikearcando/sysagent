<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SysAgent Dashboard</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
<div class="app">

    <!-- Header -->
    <header class="header">
        <div class="header-left">
            <div class="logo">
                <span class="logo-icon">&#9889;</span>
                <span class="logo-text">SysAgent</span>
            </div>
            <div id="agent-status" class="agent-badge badge-unknown">
                <span class="dot"></span>
                <span class="badge-label">Verbinden...</span>
            </div>
        </div>
        <div class="header-right">
            <button class="btn btn-primary" onclick="openModal()">+ Nieuwe Taak</button>
        </div>
    </header>

    <div class="layout">

        <!-- Sidebar -->
        <aside class="sidebar">

            <div class="sidebar-section">
                <div class="section-title">Systeemstatus</div>

                <div class="stat-card">
                    <div class="stat-label">CPU</div>
                    <div class="gauge-row">
                        <div class="gauge"><div id="cpu-bar" class="gauge-fill"></div></div>
                        <span id="cpu-val" class="gauge-val">0%</span>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-label">RAM</div>
                    <div class="gauge-row">
                        <div class="gauge"><div id="ram-bar" class="gauge-fill"></div></div>
                        <span id="ram-val" class="gauge-val">0%</span>
                    </div>
                    <div id="ram-detail" class="stat-sub"></div>
                </div>

                <div class="stat-card">
                    <div class="stat-label">Schijf (C:)</div>
                    <div class="gauge-row">
                        <div class="gauge"><div id="disk-bar" class="gauge-fill"></div></div>
                        <span id="disk-val" class="gauge-val">0%</span>
                    </div>
                    <div id="disk-detail" class="stat-sub"></div>
                </div>
            </div>

            <div class="sidebar-section">
                <div class="section-title">Overzicht</div>
                <div class="counts-grid">
                    <div class="count-box">
                        <span id="cnt-pending" class="count-num">0</span>
                        <span class="count-lbl">Wachtend</span>
                    </div>
                    <div class="count-box">
                        <span id="cnt-running" class="count-num c-blue">0</span>
                        <span class="count-lbl">Actief</span>
                    </div>
                    <div class="count-box">
                        <span id="cnt-completed" class="count-num c-green">0</span>
                        <span class="count-lbl">Voltooid</span>
                    </div>
                    <div class="count-box">
                        <span id="cnt-failed" class="count-num c-red">0</span>
                        <span class="count-lbl">Mislukt</span>
                    </div>
                </div>
            </div>

        </aside>

        <!-- Task list -->
        <main class="content">
            <div class="content-bar">
                <h2 class="content-title">Taken</h2>
                <div class="filters">
                    <button class="filter active" data-s="">Alle</button>
                    <button class="filter" data-s="pending">Wachtend</button>
                    <button class="filter" data-s="running">Actief</button>
                    <button class="filter" data-s="completed">Voltooid</button>
                    <button class="filter" data-s="failed">Mislukt</button>
                </div>
            </div>
            <div id="task-list" class="task-list">
                <div class="empty-msg">Laden...</div>
            </div>
        </main>

        <!-- Detail panel -->
        <div id="detail" class="detail hidden">
            <div class="detail-top">
                <h3 id="d-title"></h3>
                <button class="icon-btn" onclick="closeDetail()">&#10005;</button>
            </div>
            <div class="detail-meta">
                <span id="d-status" class="task-badge"></span>
                <span id="d-time" class="meta-time"></span>
            </div>
            <div id="d-desc" class="d-desc"></div>
            <div id="d-result-wrap" class="d-result hidden">
                <div class="d-result-title">Resultaat</div>
                <pre id="d-result"></pre>
            </div>
            <div class="d-logs">
                <div class="d-logs-title">
                    Logs <span id="log-cnt" class="log-cnt"></span>
                    <button class="icon-btn small" onclick="clearLogs()" title="Wis logweergave">&#8635;</button>
                </div>
                <div id="log-box" class="log-box"></div>
            </div>
        </div>

    </div>
</div>

<!-- Modal: Nieuwe Taak -->
<div id="modal" class="modal hidden">
    <div class="modal-bg" onclick="closeModal()"></div>
    <div class="modal-box">
        <div class="modal-head">
            <h3>Nieuwe Taak</h3>
            <button class="icon-btn" onclick="closeModal()">&#10005;</button>
        </div>
        <form id="task-form" onsubmit="submitTask(event)">
            <div class="field">
                <label>Titel</label>
                <input type="text" id="f-title" placeholder="Omschrijf de taak kort" required>
            </div>
            <div class="field">
                <label>Instructies voor de agent</label>
                <textarea id="f-desc" rows="7"
                    placeholder="Beschrijf stap voor stap wat de agent moet doen...&#10;&#10;Voorbeelden:&#10;- Controleer of poort 80 en 443 open zijn op server.local&#10;- Lees de laatste 100 regels van het Windows eventlog&#10;- Haal systeeminformatie op en schrijf dit naar C:\temp\rapport.txt"
                    required></textarea>
            </div>
            <div class="field">
                <label>Prioriteit</label>
                <select id="f-prio">
                    <option value="1">Normaal</option>
                    <option value="2">Hoog</option>
                    <option value="3">Kritiek</option>
                </select>
            </div>
            <div class="modal-actions">
                <button type="button" class="btn btn-ghost" onclick="closeModal()">Annuleren</button>
                <button type="submit" class="btn btn-primary">Aanmaken</button>
            </div>
        </form>
    </div>
</div>

<!-- Toast -->
<div id="toast" class="toast"></div>

<script>
    const API_BASE = 'http://localhost:5000';
</script>
<script src="js/app.js"></script>
</body>
</html>
