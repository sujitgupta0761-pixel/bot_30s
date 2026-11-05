import http.server
import socketserver
import os

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
        const API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json";

        let lastProcessedIssue = "";
        let consecutiveLosses = 0;
        let stats = { wins: 0, losses: 0, jackpots: 0 };
        let historyLog = [];
        let records = [];

        setInterval(() => {
            let now = new Date();
            let sec = now.getSeconds();
            let remaining = 29 - (sec % 30);
            let m = String(Math.floor(remaining / 60)).padStart(2, '0');
            let s = String(remaining % 60).padStart(2, '0');
            document.getElementById('timer-text').innerText = `${m}:${s}`;
        }, 200);

        function calculatePrediction(history_list) {
            if (!history_list || history_list.length < 6) {
                return { display: "BIG", numbers: "7  8", level: 1, bet_size: "Level-1" };
            }
            if (consecutiveLosses >= 3) consecutiveLosses = 0;
            let fib_steps = [1, 1, 2, 3];
            let current_step = fib_steps[Math.min(consecutiveLosses, fib_steps.length - 1)];
            
            let recent = history_list.slice(0, 12).map(r => r.size);
            let big_count = recent.filter(s => s === "BIG").length;
            
            let target = big_count >= 6 ? "BIG" : "SMALL";
            if (consecutiveLosses >= 1) target = target === "BIG" ? "SMALL" : "BIG";

            let digits = history_list.slice(0, 20).map(r => r.number);
            let pool = target === "BIG" ? [5, 6, 7, 8, 9] : [0, 1, 2, 3, 4];
            
            return { display: target, numbers: `${pool[0]}  ${pool[1]}`, level: current_step, bet_size: `Level-${current_step}` };
        }

        // Auto-retry fetch with Timeout mechanism
        async function fetchWithRetry(url, retries = 2, timeout = 2500) {
            for (let i = 0; i < retries; i++) {
                try {
                    const controller = new AbortController();
                    const timer = setTimeout(() => controller.abort(), timeout);
                    let res = await fetch(url, { signal: controller.signal });
                    clearTimeout(timer);
                    if (res.ok) {
                        return await res.json();
                    }
                } catch (err) {
                    if (i === retries - 1) throw err;
                }
            }
        }

        async function fetchAndProcess() {
            try {
                let json_data = await fetchWithRetry(API_URL);
                if (!json_data) return;
                let list = json_data.get?.("data")?.list || json_data.data?.list;
                if (!list || list.length === 0) return;

                let latest = list[0];
                let issueId = String(latest.issueNumber);
                let num = parseInt(latest.number !== undefined ? latest.number : latest.winningNumber);

                if (issueId !== lastProcessedIssue) {
                    lastProcessedIssue = issueId;
                    let actual_size = num >= 5 ? "BIG" : "SMALL";
                    let result_header = null;

                    if (records.length > 0) {
                        let last_pred = records[0].predicted_size;
                        let last_nums = records[0].predNumbers.split(' ').map(Number);
                        if (last_pred === actual_size && last_nums.includes(num)) {
                            consecutiveLosses = 0; result_header = "👑 JACKPOT ⚡👑"; stats.jackpots++; stats.wins++;
                        } else if (last_pred === actual_size) {
                            consecutiveLosses = 0; result_header = "👑  WIN ⚡👑"; stats.wins++;
                        } else {
                            consecutiveLosses++; result_header = "LOSS 🤬💔"; stats.losses++;
                        }
                        
                        historyLog.unshift({ issue: issueId.slice(-4), num: num, size: actual_size, status: result_header });
                        if (historyLog.length > 15) historyLog.pop();

                        if (document.getElementById('tgToggle').checked && result_header) {
                            fetch(`https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ chat_id: TG_CHAT_ID, text: result_header, parse_mode: "Markdown" })
                            }).catch(err => {});
                        }
                    }

                    let pred = calculatePrediction(records);
                    let next_issue = String(BigInt(issueId) + 1n);
                    
                    records.unshift({ issueId: issueId, number: num, size: actual_size, predicted_size: pred.display, predNumbers: pred.numbers });
                    if (records.length > 50) records.pop();

                    let short_next = next_issue.slice(-4);
                    let signal_line = pred.display === "BIG" ? "🟢 Signal: BIG" : "🔴 Signal: SMALL";
                    let signal_msg = `👑 PREDICTION VIP 👑\\n🏷️ Period: ${short_next}\\n${signal_line}\\n🎯 Target: ${pred.numbers}\\n📊 Plan: Level-${pred.level}`;

                    document.getElementById('issue-text').innerText = "पीरियड नंबर: " + short_next + " (" + next_issue + ")";
                    document.getElementById('signal-text').innerText = pred.display;
                    document.getElementById('level-main').innerText = "LEVEL-" + pred.level;
                    document.getElementById('numbers-text').innerText = pred.numbers;
                    document.getElementById('wins-count').innerText = stats.wins;
                    document.getElementById('losses-count').innerText = stats.losses;
                    document.getElementById('jackpots-count').innerText = stats.jackpots;

                    let rows = "";
                    historyLog.forEach(item => {
                        rows += `<tr><td>${item.issue}</td><td>${item.num}</td><td>${item.size}</td><td>${item.status}</td></tr>`;
                    });
                    document.getElementById('history-rows').innerHTML = rows || '<tr><td colspan="4">डाटा सिंक हो रहा है...</td></tr>';

                    if (document.getElementById('tgToggle').checked) {
                        setTimeout(() => {
                            if (document.getElementById('tgToggle').checked) {
                                fetch(`https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage`, {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ chat_id: TG_CHAT_ID, text: signal_msg, parse_mode: "Markdown" })
                                }).catch(err => {});
                            }
                        }, 2000);
                    }
                }
            } catch (e) {}
        }

        // Millisecond Syncing: Poll every 300ms with Auto-retry protection
        setInterval(fetchAndProcess, 300);
        fetchAndProcess();
    </script>
</body>
</html>"""

class DashboardServer(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML_CONTENT.encode('utf-8'))

    def log_message(self, format, *args):
        pass

def run_server():
    PORT = int(os.environ.get("PORT", 8000))
    with socketserver.TCPServer(("", PORT), DashboardServer) as httpd:
        print(f"🌐 30S Server Live on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
