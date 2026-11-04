import http.server
import json
import socketserver
import threading
import time

HTML_CONTENT = """<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BSNL VIP WinGo 30S Terminal</title>
    <style>
        :root {
            --bg-color: #070b19;
            --card-bg: rgba(15, 23, 42, 0.9);
            --border-glow: rgba(56, 189, 248, 0.4);
            --text-main: #f8fafc;
            --accent-gold: #fbbf24;
        }
        body {
            background: var(--bg-color);
            background-image: radial-gradient(circle at 10% 20%, rgba(14, 165, 233, 0.15) 0%, transparent 40%), radial-gradient(circle at 90% 80%, rgba(244, 63, 94, 0.15) 0%, transparent 40%), radial-gradient(circle at 50% 50%, rgba(168, 85, 247, 0.1) 0%, #070b19 80%);
            color: var(--text-main); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center; margin: 0; padding: 15px; min-height: 100vh;
            display: flex; justify-content: center; align-items: center;
        }
        .vip-card {
            background: var(--card-bg); backdrop-filter: blur(20px);
            border: 2px solid var(--border-glow); border-radius: 22px; padding: 22px;
            width: 100%; max-width: 420px; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.9), 0 0 25px rgba(56, 189, 248, 0.2);
        }
        .header-title {
            font-size: 24px; font-weight: 900;
            background: linear-gradient(45deg, #38bdf8, #c084fc, #f43f5e, #fbbf24);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 15px; letter-spacing: 1.5px; text-transform: uppercase;
        }
        .top-bar {
            display: flex; justify-content: space-between; align-items: center;
            background: linear-gradient(135deg, #1e1b4b, #0f172a); padding: 10px 14px;
            border-radius: 12px; margin-bottom: 14px; border: 1px solid rgba(56, 189, 248, 0.3);
        }
        .switcher button {
            background: #1e293b; color: #94a3b8; border: 1px solid #475569;
            padding: 6px 14px; border-radius: 8px; cursor: pointer; font-weight: 700; font-size: 13px;
        }
        .switcher button.active {
            background: linear-gradient(135deg, #0284c7, #9333ea); color: white; border-color: #38bdf8;
            box-shadow: 0 0 12px rgba(147, 51, 234, 0.6);
        }
        .tg-control { font-size: 12px; display: flex; align-items: center; gap: 6px; color: #cbd5e1; }
        .switch { position: relative; display: inline-block; width: 38px; height: 20px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #334155; transition: .3s; border-radius: 20px; border: 1px solid #64748b; }
        .slider:before { position: absolute; content: ""; height: 14px; width: 14px; left: 2px; bottom: 2px; background-color: white; transition: .3s; border-radius: 50%; }
        input:checked + .slider { background-color: #10b981; border-color: #34d399; box-shadow: 0 0 8px #10b981; }
        input:checked + .slider:before { transform: translateX(18px); }
        .info-row {
            display: flex; justify-content: space-between; align-items: center;
            background: rgba(30, 41, 59, 0.8); padding: 10px 14px; border-radius: 10px;
            margin-bottom: 12px; font-size: 13px; font-weight: 600; border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .timer-badge { background: rgba(251, 191, 36, 0.2); color: var(--accent-gold); padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(251, 191, 36, 0.4); font-family: monospace; font-size: 14px; font-weight: bold; }
        .level-box {
            background: linear-gradient(135deg, #312e81, #1e1b4b); border: 1px solid rgba(168, 85, 247, 0.5);
            color: #facc15; font-weight: 800; padding: 10px; border-radius: 10px; font-size: 16px; margin-bottom: 12px;
            box-shadow: 0 0 15px rgba(168, 85, 247, 0.2);
        }
        .level-sub { font-size: 11px; color: #c084fc; font-weight: 600; margin-top: 2px; }
        .bsnl-signal-tag { font-size: 13px; font-weight: 800; color: #38bdf8; letter-spacing: 2px; margin-bottom: -5px; text-transform: uppercase; }
        .signal-box { font-size: 56px; font-weight: 900; margin: 10px 0 12px 0; padding: 16px; border-radius: 14px; background: #000000 !important; letter-spacing: 3px; }
        .BIG { color: #22c55e; border: 2px solid #22c55e; box-shadow: 0 0 25px rgba(34, 197, 94, 0.4); }
        .SMALL { color: #ef4444; border: 2px solid #ef4444; box-shadow: 0 0 25px rgba(239, 68, 68, 0.4); }
        .numbers-display { font-size: 15px; margin: 12px 0; background: linear-gradient(135deg, #1e293b, #0f172a); padding: 10px; border-radius: 10px; color: #38bdf8; font-weight: 600; }
        .stats { display: flex; justify-content: space-around; margin: 14px 0; background: rgba(30, 41, 59, 0.9); padding: 10px; border-radius: 10px; font-size: 12px; }
        .stat-item span { display: block; font-size: 16px; font-weight: 900; margin-top: 3px; }
        h3 { font-size: 14px; color: #38bdf8; margin: 15px 0 8px 0; text-transform: uppercase; }
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
            <div class="switcher"><button class="active">30S</button></div>
            <div class="tg-control">
                <span>Telegram:</span>
                <label class="switch"><input type="checkbox" id="tgToggle" autocomplete="off"><span class="slider"></span></label>
            </div>
        </div>
        <div class="info-row">
            <span id="issue-text">पीरियड: कनेक्ट हो रहा है...</span>
            <span>समय: <span class="timer-badge" id="timer-text">00:30</span></span>
        </div>
        <div class="level-box">
            <div id="level-main">LEVEL-1</div>
            <div class="level-sub" id="recover-sub">1X (Safe Recovery)</div>
        </div>
        <div class="bsnl-signal-tag">📶 BSNL LIVE SIGNAL</div>
        <div class="signal-box" id="signal-text">--</div>
        <div class="numbers-display">गोल्डन नंबर: <strong id="numbers-text" style="color: #facc15; font-size: 17px;">-- --</strong></div>
        <div class="stats">
            <div class="stat-item" style="color: #22c55e;">जीत<span id="wins-count">0</span></div>
            <div class="stat-item" style="color: #ef4444;">हार<span id="losses-count">0</span></div>
            <div class="stat-item" style="color: #facc15;">जैकपॉट<span id="jackpots-count">0</span></div>
        </div>
        <h3>हालिया इतिहास</h3>
        <div class="table-container">
            <table>
                <thead><tr><th>पीरियड</th><th>नंबर</th><th>साइज</th><th>स्टेटस</th></tr></thead>
                <tbody id="history-rows"><tr><td colspan="4" style="color: #64748b;">लाइव डेटा आ रहा है...</td></tr></tbody>
            </table>
        </div>
    </div>
    <script>
        const TG_BOT_TOKEN = "8615000301:AAGL-UQq6ZKjuaSkDm-fk15xBfz3Xw3BPD0";
        const TG_CHAT_ID = "-1003934563963";
        const API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json";

        let totalSeconds = 30;
        let lastProcessedIssue = "";
        let lastSentIssue = "";
        let wins = 0, losses = 0, jackpots = 0;
        let historyLog = [];
        let consecutiveLosses = 0;

        function sendTelegramMessage(text) {
            if (!document.getElementById('tgToggle').checked) return;
            fetch(`https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chat_id: TG_CHAT_ID, text: text, parse_mode: "Markdown" })
            }).catch(err => console.log(err));
        }

        // टाइमर चलाएं
        setInterval(() => {
            totalSeconds--;
            if (totalSeconds < 0) totalSeconds = 30;
            let m = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
            let s = String(totalSeconds % 60).padStart(2, '0');
            document.getElementById('timer-text').innerText = `${m}:${s}`;
        }, 1000);

        // सीधे ब्राउज़र से असली API फेच करें (बिना सर्वर रुकावट के)
        async function fetchRealMarketData() {
            try {
                let response = await fetch(API_URL);
                let json = await response.json();
                let listData = json.data?.list;
                if (!listData || listData.length === 0) return;

                let latest = listData[0];
                let issueId = String(latest.issueNumber);
                let num = parseInt(latest.number ?? latest.winningNumber);

                if (issueId !== lastProcessedIssue) {
                    let actualSize = num >= 5 ? "BIG" : "SMALL";
                    let matchStatus = "LOSS";

                    if (historyLog.length > 0 && lastProcessedIssue !== "") {
                        let lastPred = historyLog[0].predicted;
                        let lastNums = historyLog[0].predNums.split(' ').map(Number);
                        
                        if (lastPred === actualSize && lastNums.includes(num)) {
                            matchStatus = "JACKPOT"; jackpots++; wins++; consecutiveLosses = 0;
                            setTimeout(() => sendTelegramMessage("🟡 *JACKPOT!* 🌟"), 1000);
                        } else if (lastPred === actualSize) {
                            matchStatus = "WIN"; wins++; consecutiveLosses = 0;
                            setTimeout(() => sendTelegramMessage("🟢 *WIN* ✅"), 1000);
                        } else {
                            matchStatus = "LOSS"; losses++; consecutiveLosses++;
                            setTimeout(() => sendTelegramMessage("🔴 *LOSS* ❌"), 1000);
                        }
                        historyLog[0].status = matchStatus;
                    }

                    // नया प्रेडिक्शन कैलकुलेशन (पाइथन जैसा लॉजिक यहाँ फ्रंटएंड पर तुरंत कैलकुलेट होगा)
                    if (consecutiveLosses >= 3) consecutiveLosses = 0;
                    let level = Math.min(consecutiveLosses + 1, 3);
                    let target = (num % 2 === 0) ? "BIG" : "SMALL"; // स्मार्ट ट्रेंड लॉजिक
                    let pool = target === "BIG" ? [5, 6, 7, 8, 9] : [0, 1, 2, 3, 4];
                    let predNumbers = `${pool[0]}  ${pool[1]}`;

                    let nextIssueNum = String(BigInt(issueId) + 1n);

                    historyLog.unshift({
                        issue: issueId.slice(-4),
                        num: num,
                        size: actualSize,
                        status: "PENDING",
                        predicted: target,
                        predNums: predNumbers
                    });
                    if (historyLog.length > 15) historyLog.pop();

                    // यूआई अपडेट करें
                    document.getElementById('issue-text').innerText = `पीरियड: ${nextIssueNum.slice(-4)} (${nextIssueNum})`;
                    let sigBox = document.getElementById('signal-text');
                    sigBox.innerText = target;
                    sigBox.className = "signal-box " + target;

                    document.getElementById('level-main').innerText = `LEVEL-${level}`;
                    document.getElementById('recover-sub').innerText = `${level}X (Safe Recovery)`;
                    document.getElementById('numbers-text').innerText = predNumbers;
                    document.getElementById('wins-count').innerText = wins;
                    document.getElementById('losses-count').innerText = losses;
                    document.getElementById('jackpots-count').innerText = jackpots;

                    // टेलीग्राम पर 5 सेकंड बाद लाइव सिग्नल भेजें
                    if (nextIssueNum !== lastSentIssue) {
                        lastSentIssue = nextIssueNum;
                        setTimeout(() => {
                            let predEmoji = target === "BIG" ? "🟢" : "🔴";
                            let msg = `🚨 *WinGo 30S SIGNAL LIVE* 📶\n` +
                                      `----------------------------------\n` +
                                      `📌 *Period:* \`${nextIssueNum}\`\n` +
                                      `🎯 *Prediction:* *${target}* ${predEmoji}\n` +
                                      `🔢 *Golden Pair:* \`${predNumbers}\`\n` +
                                      `⚡ *Recovery Level:* Level-${level}\n` +
                                      `----------------------------------\n` +
                                      `🚀 *Fast & Secure Prediction! Play Smart.*`;
                            sendTelegramMessage(msg);
                        }, 5000);
                    }

                    // टेबल अपडेट करें
                    let rows = "";
                    historyLog.forEach(item => {
                        rows += `<tr><td>${item.issue}</td><td>${item.num}</td><td>${item.size}</td><td class="${item.status}">${item.status}</td></tr>`;
                    });
                    document.getElementById('history-rows').innerHTML = rows;

                    lastProcessedIssue = issueId;
                }
            } catch (e) {
                console.log("API Fetching...", e);
            }
        }

        setInterval(fetchRealMarketData, 2000);
        fetchRealMarketData();
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
    import os
    PORT = int(os.environ.get("PORT", 8000))
    with socketserver.TCPServer(("", PORT), DashboardServer) as httpd:
        print(f"🌐 30S Server Live on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
