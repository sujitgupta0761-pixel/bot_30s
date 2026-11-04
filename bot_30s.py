import http.server
import json
import socketserver
import threading
import time
import requests

TG_BOT_TOKEN = "8615000301:AAGL-UQq6ZKjuaSkDm-fk15xBfz3Xw3BPD0"
TG_CHAT_ID = "-1003934563963"

records = []
consecutive_losses = 0
last_processed_issue = None
stats = {"total": 0, "wins": 0, "jackpots": 0, "losses": 0}
history_log = []

def calculate_prediction(history_list):
    global consecutive_losses
    if not history_list or len(history_list) < 4:
        return {"display": "BIG", "numbers": "7  8", "level": 1, "bet_size": "1X"}
    if consecutive_losses >= 3: consecutive_losses = 0
    level = min(consecutive_losses + 1, 3)
    recent = [r["size"] for r in history_list[:8]]
    wma = sum((i+1)* (1 if s=="BIG" else 0) for i, s in enumerate(reversed(recent))) / sum(range(1, len(recent)+1))
    target = "BIG" if wma >= 0.5 else "SMALL"
    if consecutive_losses >= 1: target = "SMALL" if target == "BIG" else "BIG"
    digits = [r["number"] for r in history_list[:20]]
    counts = {i: digits.count(i) for i in range(10)}
    pool = [5, 6, 7, 8, 9] if target == "BIG" else [0, 1, 2, 3, 4]
    pool.sort(key=lambda x: counts.get(x, 0), reverse=True)
    return {"display": target, "numbers": f"{pool[0]}  {pool[1]}", "level": level, "bet_size": f"Level-{level}"}

HTML_CONTENT = """<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BSNL VIP WinGo 30S Terminal</title>
    <style>
        :root { --bg-color: #070b19; --card-bg: rgba(15, 23, 42, 0.9); --border-glow: rgba(56, 189, 248, 0.4); --text-main: #f8fafc; --accent-gold: #fbbf24; }
        body { background: var(--bg-color); color: var(--text-main); font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; padding: 15px; min-height: 100vh; display: flex; justify-content: center; align-items: center; }
        .vip-card { background: var(--card-bg); border: 2px solid var(--border-glow); border-radius: 22px; padding: 22px; width: 100%; max-width: 420px; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.9); }
        .header-title { font-size: 24px; font-weight: 900; background: linear-gradient(45deg, #38bdf8, #c084fc, #f43f5e, #fbbf24); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 15px; }
        .top-bar { display: flex; justify-content: space-between; align-items: center; background: #1e1b4b; padding: 10px 14px; border-radius: 12px; margin-bottom: 14px; }
        .tg-control { font-size: 12px; display: flex; align-items: center; gap: 6px; }
        .info-row { display: flex; justify-content: space-between; align-items: center; background: rgba(30, 41, 59, 0.8); padding: 10px 14px; border-radius: 10px; margin-bottom: 12px; font-size: 13px; }
        .timer-badge { background: rgba(251, 191, 36, 0.2); color: var(--accent-gold); padding: 4px 10px; border-radius: 6px; font-family: monospace; font-size: 14px; font-weight: bold; }
        .level-box { background: linear-gradient(135deg, #312e81, #1e1b4b); border: 1px solid rgba(168, 85, 247, 0.5); color: #facc15; font-weight: 800; padding: 10px; border-radius: 10px; font-size: 16px; margin-bottom: 12px; }
        .signal-box { font-size: 56px; font-weight: 900; margin: 10px 0; padding: 16px; border-radius: 14px; background: #000; letter-spacing: 3px; }
        .BIG { color: #22c55e; border: 2px solid #22c55e; }
        .SMALL { color: #ef4444; border: 2px solid #ef4444; }
        .numbers-display { font-size: 15px; margin: 12px 0; background: #1e293b; padding: 10px; border-radius: 10px; color: #38bdf8; }
        .stats { display: flex; justify-content: space-around; margin: 14px 0; background: #1e293b; padding: 10px; border-radius: 10px; font-size: 12px; }
        .table-container { max-height: 160px; overflow-y: auto; border-radius: 8px; border: 1px solid #475569; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        th, td { padding: 8px; border-bottom: 1px solid #1e293b; text-align: center; }
        th { background: #0f172a; color: #38bdf8; position: sticky; top: 0; }
        .WIN { color: #22c55e; font-weight: bold; }
        .LOSS { color: #ef4444; font-weight: bold; }
        .JACKPOT { color: #facc15; font-weight: bold; }
    </style>
</head>
<body>
    <div class="vip-card">
        <div class="header-title">BSNL VIP 30S Terminal</div>
        <div class="top-bar">
            <button class="active" style="background:#0284c7; color:#fff; border:0; padding:6px 14px; border-radius:8px;">30S</button>
            <div class="tg-control"><span>Telegram:</span> <input type="checkbox" id="tgToggle" checked></div>
        </div>
        <div class="info-row"><span id="issue-text">पीरियड: --</span><span>समय: <span class="timer-badge" id="timer-text">00:30</span></span></div>
        <div class="level-box"><div id="level-main">LEVEL-1</div></div>
        <div class="signal-box" id="signal-text">--</div>
        <div class="numbers-display">गोल्डन नंबर: <strong id="numbers-text" style="color: #facc15;">-- --</strong></div>
        <div class="stats">
            <div style="color: #22c55e;">जीत<span id="wins-count">0</span></div>
            <div style="color: #ef4444;">हार<span id="losses-count">0</span></div>
            <div style="color: #facc15;">जैकपॉट<span id="jackpots-count">0</span></div>
        </div>
        <h3>हालिया इतिहास</h3>
        <div class="table-container">
            <table>
                <thead><tr><th>पीरियड</th><th>नंबर</th><th>साइज</th><th>स्टेटस</th></tr></thead>
                <tbody id="history-rows"><tr><td colspan="4">डेटा सिंक हो रहा है...</td></tr></tbody>
            </table>
        </div>
    </div>
    <script>
        const API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json";
        let lastCheckedIssue = "";

        setInterval(() => {
            let now = new Date();
            let sec = now.getSeconds();
            let remaining = 29 - (sec % 30);
            let m = String(Math.floor(remaining / 60)).padStart(2, '0');
            let s = String(remaining % 60).padStart(2, '0');
            document.getElementById('timer-text').innerText = `${m}:${s}`;
        }, 500);

        async function syncWithPythonBrain() {
            try {
                let res = await fetch(API_URL);
                let json = await res.json();
                let latest = json.data?.list?.[0];
                if (!latest) return;

                let issueId = String(latest.issueNumber);
                let num = parseInt(latest.number ?? latest.winningNumber);

                if (issueId !== lastCheckedIssue) {
                    lastCheckedIssue = issueId;
                    
                    let postRes = await fetch('/post_data', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ issue: issueId, number: num })
                    });
                    let data = await postRes.json();

                    document.getElementById('issue-text').innerText = "पीरियड: " + data.issue;
                    let sig = document.getElementById('signal-text');
                    sig.innerText = data.signal;
                    sig.className = "signal-box " + data.signal;
                    document.getElementById('level-main').innerText = data.level;
                    document.getElementById('numbers-text').innerText = data.numbers;
                    document.getElementById('wins-count').innerText = data.wins;
                    document.getElementById('losses-count').innerText = data.losses;
                    document.getElementById('jackpots-count').innerText = data.jackpots;

                    let rows = "";
                    data.history.forEach(item => {
                        rows += `<tr><td>${item.issue}</td><td>${item.num}</td><td>${item.size}</td><td class="${item.status}">${item.status}</td></tr>`;
                    });
                    document.getElementById('history-rows').innerHTML = rows;

                    if (document.getElementById('tgToggle').checked && data.send_telegram) {
                        fetch(`https://api.telegram.org/bot8615000301:AAGL-UQq6ZKjuaSkDm-fk15xBfz3Xw3BPD0/sendMessage`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ chat_id: "-1003934563963", text: data.tg_message, parse_mode: "Markdown" })
                        }).catch(err => {});
                    }
                }
            } catch (e) { console.log("Sync error", e); }
        }

        setInterval(syncWithPythonBrain, 1000);
        syncWithPythonBrain();
    </script>
</body>
</html>"""

class DashboardServer(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global records, consecutive_losses, last_processed_issue, stats, history_log
        if self.path == '/post_data':
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            
            issue_id = post_data.get("issue")
            num = post_data.get("number")
            actual_size = "BIG" if num >= 5 else "SMALL"
            
            match_status = "LOSS"
            tg_msg = ""
            send_tg = False

            if records and last_processed_issue:
                last_pred = records[0].get("predicted_size")
                last_nums = [int(n) for n in records[0].get("predNumbers", "").split() if n.isdigit()]
                stats["total"] += 1
                if last_pred == actual_size and num in last_nums:
                    consecutive_losses = 0; match_status = "JACKPOT"; stats["jackpots"] += 1; stats["wins"] += 1
                elif last_pred == actual_size:
                    consecutive_losses = 0; match_status = "WIN"; stats["wins"] += 1
                else:
                    consecutive_losses += 1; match_status = "LOSS"; stats["losses"] += 1
                
                history_log.insert(0, {"issue": issue_id[-4:], "num": num, "size": actual_size, "status": match_status})
                if len(history_log) > 15: history_log.pop()

            pred = calculate_prediction(records)
            next_issue = str(int(issue_id) + 1)
            
            records.insert(0, {"issueId": issue_id, "number": num, "size": actual_size, "predicted_size": pred["display"], "predNumbers": pred["numbers"]})
            if len(records) > 50: records.pop()
            last_processed_issue = issue_id

            if next_issue != last_processed_issue:
                send_tg = True
                pred_emoji = "🟢" if pred["display"] == "BIG" else "🔴"
                tg_msg = (f"🚨 *WinGo 30S SIGNAL LIVE* 📶\n"
                          f"----------------------------------\n"
                          f"📌 *Period:* `{next_issue}`\n"
                          f"🎯 *Prediction:* *{pred['display']}* {pred_emoji}\n"
                          f"🔢 *Golden Pair:* `{pred['numbers']}`\n"
                          f"⚡ *Recovery Level:* Level-{pred['level']}\n"
                          f"----------------------------------\n"
                          f"🚀 *Fast & Secure Prediction!*")

            response_data = {
                "issue": f"{next_issue[-4:]} ({next_issue})",
                "signal": pred["display"],
                "numbers": pred["numbers"],
                "level": f"Level-{pred['level']} ({pred['bet_size']})",
                "wins": stats["wins"],
                "losses": stats["losses"],
                "jackpots": stats["jackpots"],
                "history": history_log,
                "send_telegram": send_tg,
                "tg_message": tg_msg
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        pass

def run_server():
    import os
    PORT = int(os.environ.get("PORT", 8000))
    with socketserver.TCPServer(("", PORT), DashboardServer) as httpd:
        print(f"🌐 30S Server Live on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
