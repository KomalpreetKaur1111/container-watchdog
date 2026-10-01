from flask import Flask, render_template_string, redirect, url_for
import json
import subprocess

app = Flask(__name__)
STATUS_FILE = "status.json"

PAGE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Container Watchdog Dashboard</title>
    <meta http-equiv="refresh" content="3">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Inter', Arial, sans-serif;
            background: #0f1117;
            color: #e6e6e6;
            margin: 0;
            padding: 40px 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .header h1 {
            font-size: 32px;
            font-weight: 800;
            margin: 0;
            letter-spacing: -0.5px;
        }
        .header p {
            color: #8a8f98;
            margin-top: 6px;
            font-size: 14px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
            gap: 24px;
            max-width: 1100px;
            margin: 0 auto;
        }
        .card {
            background: #171a23;
            border: 1px solid #262b38;
            border-radius: 16px;
            padding: 24px;
            transition: border-color 0.3s ease;
        }
        .card.is-down { border-color: #b3261e; }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
        }
        .card-title {
            font-size: 17px;
            font-weight: 700;
        }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 700;
        }
        .badge.healthy { background: rgba(46, 160, 67, 0.15); color: #3fb950; }
        .badge.down { background: rgba(248, 81, 73, 0.15); color: #f85149; }
        .dot {
            width: 8px; height: 8px; border-radius: 50%;
            display: inline-block;
        }
        .badge.healthy .dot { background: #3fb950; box-shadow: 0 0 8px #3fb950; }
        .badge.down .dot { background: #f85149; animation: pulse 1s infinite; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 18px;
        }
        .metric {
            background: #0f1117;
            border-radius: 10px;
            padding: 12px 10px;
            text-align: center;
        }
        .metric-label {
            font-size: 11px;
            color: #8a8f98;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metric-value {
            font-size: 16px;
            font-weight: 700;
            margin-top: 4px;
        }
        .crash-btn {
            width: 100%;
            background: #262b38;
            color: #e6e6e6;
            border: 1px solid #363c4a;
            padding: 10px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 12px;
            transition: background 0.2s ease;
        }
        .crash-btn:hover { background: #b3261e; border-color: #b3261e; }
        .log-toggle summary {
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            color: #8a8f98;
            padding: 8px 0;
            list-style: none;
            user-select: none;
        }
        .log-toggle summary::-webkit-details-marker {
            display: none;
        }
        .log-toggle summary::before {
            content: "\\25B8  ";
        }
        .log-toggle[open] summary::before {
            content: "\\25BE  ";
        }
        .log-list {
            font-size: 12.5px;
            max-height: 180px;
            overflow-y: auto;
            margin-top: 8px;
        }
        .log-row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid #1f232e;
            color: #b0b5bd;
        }
        .log-row:last-child { border-bottom: none; }
        .log-time { color: #5c6270; font-variant-numeric: tabular-nums; }
        .empty-msg {
            text-align: center;
            color: #8a8f98;
            margin-top: 60px;
            font-size: 15px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Container Watchdog</h1>
        <p>Auto-healing infrastructure monitor - refreshes every 3s</p>
    </div>

    {% if not containers %}
        <div class="empty-msg">No containers labeled "watch=true" found.</div>
    {% endif %}

    <div class="grid">
        {% for name, c in containers.items() %}
        <div class="card {{ '' if c.healthy else 'is-down' }}">
            <div class="card-header">
                <span class="card-title">{{ name }}</span>
                <span class="badge {{ 'healthy' if c.healthy else 'down' }}">
                    <span class="dot"></span>
                    {{ "HEALTHY" if c.healthy else "DOWN" }}
                </span>
            </div>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">CPU</div>
                    <div class="metric-value">{{ c.cpu }}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Memory</div>
                    <div class="metric-value">{{ c.mem }}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Restarts</div>
                    <div class="metric-value">{{ c.restart_count }}</div>
                </div>
            </div>
            <form action="/chaos/{{ name }}" method="post">
                <button class="crash-btn" type="submit">Simulate Crash</button>
            </form>
            <details class="log-toggle">
                <summary>View activity log</summary>
                <div class="log-list">
                    {% for entry in c.logs|reverse %}
                    <div class="log-row">
                        <span>{{ entry.message }}</span>
                        <span class="log-time">{{ entry.time.split(" ")[1] }}</span>
                    </div>
                    {% endfor %}
                </div>
            </details>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    try:
        with open(STATUS_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    return render_template_string(PAGE_TEMPLATE, containers=data)

@app.route('/chaos/<name>', methods=['POST'])
def chaos(name):
    try:
        with open(STATUS_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    if name in data:
        subprocess.run(["docker", "stop", name])
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6060)