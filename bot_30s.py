import http.server
import json
import socketserver
import threading
import time
import requests

TG_BOT_TOKEN = "8615000301:AAGL-UQq6ZKjuaSkDm-fk15xBfz3Xw3BPD0"
TG_CHAT_ID = "-1003934563963"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

records = []
consecutive_losses = 0
last_processed_issue = None
stats = {"total": 0, "wins": 0, "jackpots": 0, "losses": 0}
history_log = []
latest_dashboard_data = {}
data_lock = threading.Lock()

def calculate_prediction(history_list):
    global consecutive_losses
    if not history_list or len(history_list) < 6:
        return {"display": "BIG", "numbers": "7  8", "level": 1, "bet_size": "Level-1"}
    
    if consecutive_losses >= 3: 
        consecutive_losses = 0
    
    fib_steps = [1, 1, 2, 3]
    current_step = fib_steps[min(consecutive_losses, len(fib_steps)-1)]
    
    recent = [r["size"] for r in history_list[:12]]
    big_count = recent.count("BIG")
    
    target = "BIG" if big_count >= 6 else "SMALL"
    if consecutive_losses >= 1: 
        target = "SMALL" if target == "BIG" else "BIG"

    digits = [r["number"] for r in history_list[:20]]
    counts = {i: digits.count(i) for i in range(10)}
    pool = [5, 6, 7, 8, 9] if target == "BIG" else [0, 1, 2, 3, 4]
    pool.sort(key=lambda x: counts.get(x, 0), reverse=True)
    
    return {"display": target, "numbers": f"{pool[0]}  {pool[1]}", "level": current_step, "bet_size": f"Level-{current_step}"}

def background_worker():
    global records, consecutive_losses, last_processed_issue, stats, history_log, latest_dashboard_data
    while True:
        try:
            res = requests.get(API_URL, timeout=3)
            json_data = res.json()
            latest = json_data.get("data", {}).get("list", [])[0]
            if latest:
                issueId = str(latest["issueNumber"])
                num = int(latest.get("number", latest.get("winningNumber", 0)))
                
                if issueId != last_processed_issue:
                    last_processed_issue = issueId
                    actual_size = "BIG" if num >= 5 else "SMALL"
                    result_header = None

                    with data_lock:
                        if records:
                            last_pred = records[0].get("predicted_size")
                            last_nums = [int(n) for n in records[0].get("predNumbers", "").split() if n.isdigit()]
                            stats["total"] += 1
                            if last_pred == actual_size and num in last_nums:
                                consecutive_losses = 0; result_header = "👑 JACKPOT ⚡👑"; stats["jackpots"] += 1; stats["wins"] += 1
                            elif last_pred == actual_size:
                                consecutive_losses = 0; result_header = "👑  WIN ⚡👑"; stats["wins"] += 1
                            else:
                                consecutive_losses += 1; result_header = "LOSS 🤬💔"; stats["losses"] += 1
                            
                            history_log.insert(0, {"issue": issueId[-4:], "num": num, "size": actual_size, "status": result_header})
                            if len(history_log) > 15: history_log.pop()

                        pred = calculate_prediction(records)
                        next_issue = str(int(issueId) + 1)
                        
                        records.insert(0, {"issueId": issueId, "number": num, "size": actual_size, "predicted_size": pred["display"], "predNumbers": pred["numbers"]})
                        if len(records) > 50: records.pop()

                        short_next = next_issue[-4:]
                        signal_line = "🟢 Signal: BIG" if pred["display"] == "BIG" else "🔴 Signal: SMALL"
                        signal_msg = (f"👑 PREDICTION VIP 👑\n"
                                      f"🏷️ Period: {short_next}\n"
                                      f"{signal_line}\n"
                                      f"🎯 Target: {pred['numbers']}\n"
                                      f"📊 Plan: {pred['bet_size']}")

                        latest_dashboard_data = {
                            "issue": f"{short_next} ({next_issue})",
                            "signal": pred["display"],
                            "numbers": pred["numbers"],
                            "level": f"Level-{pred['level']}",
                            "wins": stats["wins"],
                            "losses": stats["losses"],
                            "jackpots": stats["jackpots"],
                            "history": history_log,
                            "result_message": result_header,
                            "signal_message": signal_msg
                        }
        except Exception as e:
            pass
        time.sleep(1)

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
        .header-title { font-size: 24px; font-weight: 900; color: #38bdf8; margin-bottom: 15px; }
        .top-bar { display: flex; justify-content: space-between; align-items: center; background: #1e1b4b; padding: 10px 14px; border-radius: 12px; margin-bottom: 14px; }
        .tg-control { font-size: 12px; display: flex; align-items: center; gap: 6px; color: #38bdf8; font-weight: bold; }
        .info-row { display: flex; justify-content: space-between; align-items: center; background: rgba(30, 41, 59, 0.8); padding: 10px 14px; border-radius: 10px; margin-bottom: 12px; font-size: 13px; }
        .timer-badge { background: rgba(251, 191, 36, 0.2); color: var(--accent-gold); padding: 4px 10px; border-radius: 6px; font-family: monospace; font-size: 14px; font-weight: bold; }
        .level-box { background: #1e1b4b; border: 1px solid #475569; color: #facc15; font-weight: 800; padding: 10px; border-radius: 10px; font-size: 16px; margin-bottom: 12px; }
        .signal-box { font-size: 56px; font-weight: 900; margin: 10px 0; padding: 16px; border-radius: 14px; background: #000; letter-spacing: 3px; color: #fff; }
        .numbers-display { font-size: 15px; margin: 12px 0; background: #1e293b; padding: 10px; border-radius: 10px; color: #38bdf8; }
        .stats { display: flex; justify-content: space-around; margin: 14px 0; background: #1e293b; padding: 10px; border-radius: 10px; font-size: 12px; color: #fff; }
        .table-container { max-height: 160px; overflow-y: auto; border-radius: 8px; border: 1px solid #475569; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; color: #fff; }
        th, td { padding: 8px; border-bottom: 1px solid #1e293b; text-align: center; }
        th { background: #0f172a; color: #38bdf8; position: sticky; top: 0; }
    </style>
</head>
<body>
    <div class="vip-card">
        <div class="header-title">BSNL VIP 30S Terminal</div>
        <div class="top-bar">
            <button style="background:#0284c7; color:#fff; border:0; padding:6px 14px; border-radius:8px;">30S</button>
            <div class="tg-control"><span>Telegram Auto:</span> <input type="checkbox" id="tgToggle"></div>
        </div>
        <div class="info-row"><span id="issue-text">पीरियड नंबर: --</span><span>समय: <span class="timer-badge" id="timer-text">00:30</span></span></div>
        <div class="level-box"><div id="level-main">LEVEL-1</div></div>
        <div class="signal-box" id="signal-text">--</div>
        <div class="numbers-display">गोल्डन नंबर: <strong id="numbers-text" style="color: #facc15;">-- --</strong></div>
        <div class="stats">
            <div>जीत <span id="wins-count">0</span></div>
            <div>हार <span id="losses-count">0</span></div>
            <div>जैकपॉट <span id="jackpots-count">0</span></div>
        </div>
        <h3>हालिया इतिहास</h3>
        <div class="table-container">
            <table>
                <thead><tr><th>पीरियड</th><th>नंबर</th><th>साइज</th><th>स्टेटस</th></tr></thead>
                <tbody id="history-rows"><tr><td colspan="4">डाटा सिंक हो रहा है...</td></tr></tbody>
            </table>
        </div>
    </div>
    <script>
        const TG_BOT_TOKEN = "8615000301:AAGL-UQq6ZKjuaSkDm-fk15xBfz3Xw3BPD0";
        const TG_CHAT_ID = "-1003934563963";
        let lastProcessedIssueUI = "";

        setInterval(() => {
            let now = new Date();
            let sec = now.getSeconds();
            let remaining = 29 - (sec % 30);
            let m = String(Math.floor(remaining / 60)).padStart(2, '0');
            let s = String(remaining % 60).padStart(2, '0');
            document.getElementById('timer-text').innerText = `${m}:${s}`;
        }, 500);

        async function fetchDashboardData() {
            try {
                let res = await fetch('/get_data');
                let data = await res.json();
                if (!data.issue) return;

                document.getElementById('issue-text').innerText = "पीरियड नंबर: " + data.issue;
                document.getElementById('signal-text').innerText = data.signal;
                document.getElementById('level-main').innerText = data.level || "LEVEL-1";
                document.getElementById('numbers-text').innerText = data.numbers;
                document.getElementById('wins-count').innerText = data.wins;
                document.getElementById('losses-count').innerText = data.losses;
                document.getElementById('jackpots-count').innerText = data.jackpots;

                let rows = "";
                data.history.forEach(item => {
                    rows += `<tr><td>${item.issue}</td><td>${item.num}</td><td>${item.size}</td><td>${item.status}</td></tr>`;
                });
                document.getElementById('history-rows').innerHTML = rows;

                // अगर नया पीरियड आया है और Telegram स्विच ON है
                let currentIssueNum = data.issue.split(' ')[1];
                if (currentIssueNum !== lastProcessedIssueUI && document.getElementById('tgToggle').checked) {
                    lastProcessedIssueUI = currentIssueNum;

                    if (data.result_message) {
                        fetch(`https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ chat_id: TG_CHAT_ID, text: data.result_message, parse_mode: "Markdown" })
                        }).catch(err => {});
                    }

                    // 5 सेकंड का डिले सिर्फ सिग्नल से पहले
                    setTimeout(() => {
                        if (document.getElementById('tgToggle').checked) {
                            fetch(`https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ chat_id: TG_CHAT_ID, text: data.signal_message, parse_mode: "Markdown" })
                            }).catch(err => {});
                        }
                    }, 5000);
                }
            } catch (e) {}
        }

        setInterval(fetchDashboardData, 1000);
        fetchDashboardData();
    </script>
</body>
</html>"""

class DashboardServer(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global latest_dashboard_data
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode('utf-8'))
        elif self.path == '/get_data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            with data_lock:
                self.wfile.write(json.dumps(latest_dashboard_data, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def run_server():
    import os
    PORT = int(os.environ.get("PORT", 8000))
    threading.Thread(target=background_worker, daemon=True).start()
    with socketserver.TCPServer(("", PORT), DashboardServer) as httpd:
        print(f"🌐 30S Server Live on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
