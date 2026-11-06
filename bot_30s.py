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
            <div class="tg-control"><span>Telegram Auto:</span> <input type="checkbox" id="tgToggle" onclick="verifyTelegram(event)"></div>
        </div>
        <div class="info-row"><span id="issue-text">पीरियड नंबर: --</span><span>समय: <span class="timer-badge" id="timer-text">00:30</span></span></div>
        <div class="level-box"><div id="level-main">DATA SYNCING...</div></div>
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
        const TG_PASSWORD = "8709";

        let lastProcessedIssue = "";
        let consecutiveLosses = 0;
        let stats = { wins: 0, losses: 0, jackpots: 0 };
        let historyLog = [];
        let records = [];

        function verifyTelegram(event) {
            let toggleBox = document.getElementById('tgToggle');
            if (toggleBox.checked) {
                toggleBox.checked = false;
                let pass = prompt("🔒 सुरक्षित क्षेत्र: टेलीग्राम ऑटोमेशन ऑन करने के लिए पासवर्ड दर्ज करें:");
                if (pass === TG_PASSWORD) {
                    toggleBox.checked = true;
                    alert("✅ टेलीग्राम ऑटोमेशन सफलतापूर्वक ऑन हो गया है!");
                } else if (pass !== null) {
                    alert("❌ गलत पासवर्ड! टेलीग्राम ऑन नहीं किया जा सकता।");
                }
            }
        }

        setInterval(() => {
            let now = new Date();
            let sec = now.getSeconds();
            let remaining = 29 - (sec % 30);
            let m = String(Math.floor(remaining / 60)).padStart(2, '0');
            let s = String(remaining % 60).padStart(2, '0');
            document.getElementById('timer-text').innerText = `${m}:${s}`;
        }, 200);

        function calculatePrediction(history_list) {
            if (!history_list || history_list.length < 3) return null;
            if (consecutiveLosses >= 3) consecutiveLosses = 0;
            let fib_steps = [1, 1, 2, 3];
            let current_step = fib_steps[Math.min(consecutiveLosses, fib_steps.length - 1)];

            let recent_sizes = history_list.map(r => r.size);
            let last_actual = recent_sizes[0];
            let target = "BIG";

            let is_zigzag = (recent_sizes.length >= 3 && recent_sizes[0] !== recent_sizes[1] && recent_sizes[1] !== recent_sizes[2]);
            let is_cluster_2_1 = (recent_sizes.length >= 3 && recent_sizes[0] === recent_sizes[1] && recent_sizes[1] !== recent_sizes[2]);

            if (consecutiveLosses > 0) {
                if (is_cluster_2_1) target = recent_sizes[2];
                else if (is_zigzag) target = last_actual === "BIG" ? "SMALL" : "BIG";
                else target = last_actual;
            } else {
                if (is_cluster_2_1) target = recent_sizes[2];
                else if (is_zigzag) target = last_actual === "BIG" ? "SMALL" : "BIG";
                else {
                    let sample_size = Math.min(10, history_list.length);
                    let big_score = 0, small_score = 0;
                    for (let i = 0; i < sample_size; i++) {
                        let weight = sample_size - i;
                        if (history_list[i].size === "BIG") big_score += weight;
                        else small_score += weight;
                    }
                    target = big_score >= small_score ? "BIG" : "SMALL";
                }
            }

            let pool = target === "BIG" ? [6, 7, 8, 9] : [0, 1, 2, 3];
            let lucky_nums = `${pool[Math.floor(Math.random()*pool.length)]}  ${pool[Math.floor(Math.random()*pool.length)]}`;
            
            return { display: target, numbers: lucky_nums, level: current_step };
        }

        async function fetchWithRetry(url, retries = 2, timeout = 2500) {
            for (let i = 0; i < retries; i++) {
                try {
                    const controller = new AbortController();
                    const timer = setTimeout(() => controller.abort(), timeout);
                    let res = await fetch(url, { signal: controller.signal });
                    clearTimeout(timer);
                    if (res.ok) return await res.json();
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

                if (lastProcessedIssue === "" && list.length >= 5) {
                    let loadCount = Math.min(10, list.length);
                    for (let i = loadCount - 1; i >= 1; i--) {
                        let past_item = list[i];
                        let p_issue = String(past_item.issueNumber);
                        let p_num = parseInt(past_item.number !== undefined ? past_item.number : past_item.winningNumber);
                        let p_size = p_num >= 5 ? "BIG" : "SMALL";
                        records.unshift({ issueId: p_issue, number: p_num, size: p_size, predicted_size: p_size, predNumbers: "--" });
                        historyLog.unshift({ issue: p_issue.slice(-4), num: p_num, size: p_size, status: "📌 PAST" });
                    }
                    lastProcessedIssue = String(list[0].issueNumber);
                }

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
                        if (last_pred && last_pred !== "--") {
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
                    }

                    records.unshift({ issueId: issueId, number: num, size: actual_size, predicted_size: "", predNumbers: "" });
                    if (records.length > 50) records.pop();
                }

                let pred = calculatePrediction(records);
                let next_issue = String(BigInt(issueId) + 1n);
                let short_next = next_issue.slice(-4);

                if (pred) {
                    records[0].predicted_size = pred.display;
                    records[0].predNumbers = pred.numbers;

                    let signal_line = pred.display === "BIG" ? "🟢 Signal: BIG" : "🔴 Signal: SMALL";
                    let signal_msg = `👑 PREDICTION VIP 👑\\n🏷️ Period: ${short_next}\\n${signal_line}\\n🎯 Target: ${pred.numbers}\\n📊 Plan: Level-${pred.level}`;

                    document.getElementById('signal-text').innerText = pred.display;
                    document.getElementById('level-main').innerText = "LEVEL-" + pred.level;
                    document.getElementById('numbers-text').innerText = pred.numbers;

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
                } else {
                    document.getElementById('signal-text').innerText = "--";
                    document.getElementById('level-main').innerText = "DATA SYNCING...";
                    document.getElementById('numbers-text').innerText = "-- --";
                }

                document.getElementById('issue-text').innerText = "पीरियड नंबर: " + short_next + " (" + next_issue + ")";
                document.getElementById('wins-count').innerText = stats.wins;
                document.getElementById('losses-count').innerText = stats.losses;
                document.getElementById('jackpots-count').innerText = stats.jackpots;

                let rows = "";
                historyLog.forEach(item => {
                    rows += `<tr><td>${item.issue}</td><td>${item.num}</td><td>${item.size}</td><td>${item.status}</td></tr>`;
                });
                document.getElementById('history-rows').innerHTML = rows || '<tr><td colspan="4">डाटा सिंक हो रहा है...</td></tr>';

            } catch (e) {}
        }

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
