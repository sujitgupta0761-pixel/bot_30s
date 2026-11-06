import http.server
import socketserver
import os
import time
from urllib.parse import parse_qs, urlparse

active_sessions = {}
blocked_ips = set()

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
        .header-title { font-size: 24px; font-weight: 900; color: #38bdf8; margin-bottom: 12px; }
        .top-bar { display: flex; justify-content: space-between; align-items: center; background: #1e1b4b; padding: 10px 14px; border-radius: 12px; margin-bottom: 10px; }
        .tg-control { font-size: 12px; display: flex; align-items: center; gap: 6px; color: #38bdf8; font-weight: bold; }
        .info-row { display: flex; justify-content: space-between; align-items: center; background: rgba(30, 41, 59, 0.8); padding: 8px 12px; border-radius: 10px; margin-bottom: 8px; font-size: 13px; }
        .timer-badge { background: rgba(251, 191, 36, 0.2); color: var(--accent-gold); padding: 4px 10px; border-radius: 6px; font-family: monospace; font-size: 14px; font-weight: bold; }
        .pattern-box { background: #1e1b4b; border: 1px solid #475569; color: #facc15; font-weight: 800; padding: 8px; border-radius: 10px; font-size: 13px; margin-bottom: 8px; }
        .signal-box { font-size: 42px; font-weight: 900; margin: 8px 0; padding: 12px; border-radius: 14px; background: #000; letter-spacing: 2px; color: #38bdf8; }
        .stats-row { display: flex; justify-content: space-around; background: #1e293b; padding: 8px; border-radius: 10px; margin-bottom: 10px; font-size: 13px; font-weight: bold; }
        .table-container { max-height: 150px; overflow-y: auto; border-radius: 8px; border: 1px solid #475569; margin-top: 8px; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; color: #fff; }
        th, td { padding: 6px; border-bottom: 1px solid #1e293b; text-align: center; }
        th { background: #0f172a; color: #38bdf8; position: sticky; top: 0; }
        .footer-panel { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; font-size: 12px; background: rgba(56, 189, 248, 0.1); padding: 6px 10px; border-radius: 8px; }
        .admin-btn { background: #38bdf8; color: #0f172a; border: 0; padding: 4px 10px; border-radius: 6px; font-weight: bold; cursor: pointer; }
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
        <div class="pattern-box" id="pattern-text">पैटर्न स्कैन हो रहा है...</div>
        <div class="signal-box" id="signal-text">--</div>
        <div class="stats-row">
            <span style="color: #22c55e;">जीत (Win): <span id="wins-count">0</span></span>
            <span style="color: #ef4444;">हार (Loss): <span id="losses-count">0</span></span>
        </div>
        <h3>लाइव मार्केट इतिहास</h3>
        <div class="table-container">
            <table>
                <thead><tr><th>पीरियड</th><th>नंबर</th><th>साइज</th><th>स्टेटस</th></tr></thead>
                <tbody id="history-rows"><tr><td colspan="4">डाटा सिंक हो रहा है...</td></tr></tbody>
            </table>
        </div>
        <div class="footer-panel">
            <span>🟢 एक्टिव डिवाइस: <span id="active-count">1</span></span>
            <button class="admin-btn" onclick="openAdminPanel()">⚙️ Admin Panel</button>
        </div>
    </div>
    <script>
        const TG_BOT_TOKEN = "8615000301:AAGL-UQq6ZKjuaSkDm-fk15xBfz3Xw3BPD0";
        const TG_CHAT_ID = "-1003934563963";
        const API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json";
        const TG_PASSWORD = "8709";

        let urlParams = new URLSearchParams(window.location.search);
        let userName = urlParams.get('user');
        if (!userName || userName.trim() === "") {
            userName = localStorage.getItem("bsnl_user_name");
        }
        if (!userName || userName.trim() === "" || userName === "null") {
            userName = prompt("🔒 सुरक्षा जाँच: कृपया अपना असली नाम दर्ज करें:");
            if (!userName || userName.trim() === "") {
                userName = "Guest_" + Math.floor(Math.random() * 1000);
            }
        }
        localStorage.setItem("bsnl_user_name", userName);

        let lastProcessedIssue = "";
        let historyLog = [];
        let records = [];
        let stats = { wins: 0, losses: 0 };
        
        let lockedPeriod = "";
        let lockedPrediction = null;
        let lockedPattern = "";

        setInterval(() => {
            fetch('/ping?user=' + encodeURIComponent(userName)).then(res => res.json()).then(data => {
                if(data.blocked) {
                    document.body.innerHTML = "<h1 style='color:red; margin-top:20vh;'>🚫 Access Denied: Your device has been blocked by the Administrator!</h1>";
                } else if(data.active_devices) {
                    document.getElementById('active-count').innerText = data.active_devices;
                }
            }).catch(e => {});
        }, 5000);

        function openAdminPanel() {
            let pass = prompt("🔑 एडमिन पासवर्ड दर्ज करें:");
            if (pass === TG_PASSWORD) {
                window.location.href = "/admin?pass=8709";
            } else if (pass !== null) {
                alert("❌ गलत पासवर्ड!");
            }
        }

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

        function analyzeMarketPattern(history_list) {
            if (!history_list || history_list.length < 4) {
                return { prediction: "WAITING", pattern: "डेटा सिंक हो रहा है..." };
            }
            let recent = history_list.map(r => r.size);

            if (recent[0] === recent[1] && recent[1] === recent[2]) {
                return { prediction: recent[0], pattern: "🐉 DRAGON (" + recent[0] + ")" };
            }

            let is_zigzag = (recent[0] !== recent[1] && recent[1] !== recent[2] && recent[2] !== recent[3]);
            if (is_zigzag) {
                let next_pred = recent[0] === "BIG" ? "SMALL" : "BIG";
                return { prediction: next_pred, pattern: "⚡ ZIG-ZAG PATTERN" };
            }

            let big_count = recent.slice(0, 4).filter(s => s === "BIG").length;
            let pred = big_count >= 2 ? "BIG" : "SMALL";
            return { prediction: pred, pattern: "📊 MIXED TREND" };
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
                    for (let i = Math.min(10, list.length) - 1; i >= 1; i--) {
                        let p_item = list[i];
                        let p_num = parseInt(p_item.number !== undefined ? p_item.number : p_item.winningNumber);
                        records.unshift({ size: p_num >= 5 ? "BIG" : "SMALL" });
                    }
                    lastProcessedIssue = String(list[0].issueNumber);
                }

                let latest = list[0];
                let issueId = String(latest.issueNumber);
                let num = parseInt(latest.number !== undefined ? latest.number : latest.winningNumber);

                if (issueId !== lastProcessedIssue) {
                    lastProcessedIssue = issueId;
                    let actual_size = num >= 5 ? "BIG" : "SMALL";
                    let result_status = "📌 PAST";

                    if (records.length > 0 && records[0].predicted) {
                        let last_pred = records[0].predicted;
                        if (last_pred === actual_size) {
                            stats.wins++;
                            result_status = "👑  WIN ⚡👑";
                        } else {
                            stats.losses++;
                            result_status = "LOSS 🤬💔";
                        }

                        if (document.getElementById('tgToggle').checked) {
                            fetch(`https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ chat_id: TG_CHAT_ID, text: result_status, parse_mode: "Markdown" })
                            }).catch(err => {});
                        }
                    }

                    records.unshift({ size: actual_size, predicted: lockedPrediction });
                    if (records.length > 30) records.pop();

                    historyLog.unshift({ issue: issueId.slice(-4), num: num, size: actual_size, status: result_status });
                    if (historyLog.length > 20) historyLog.pop();

                    lockedPrediction = null;
                }

                let next_issue = String(BigInt(issueId) + 1n);
                let short_next = next_issue.slice(-4);

                if (lockedPeriod !== short_next) {
                    let result = analyzeMarketPattern(records);
                    if (result.prediction !== "WAITING") {
                        lockedPeriod = short_next;
                        lockedPrediction = result.prediction;
                        lockedPattern = result.pattern;
                        records[0].predicted = lockedPrediction;

                        if (document.getElementById('tgToggle').checked) {
                            let msg = `👑 BSNV VIP SIGNAL 👑\\n🏷️ Period: ${short_next}\\n🎯 Prediction: ${lockedPrediction}\\n📈 Pattern: ${lockedPattern}`;
                            setTimeout(() => {
                                if (document.getElementById('tgToggle').checked) {
                                    fetch(`https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage`, {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({ chat_id: TG_CHAT_ID, text: msg, parse_mode: "Markdown" })
                                    }).catch(err => {});
                                }
                            }, 5000);
                        }
                    }
                }

                if (lockedPrediction) {
                    document.getElementById('signal-text').innerText = lockedPrediction;
                    document.getElementById('pattern-text').innerText = lockedPattern;
                } else {
                    document.getElementById('signal-text').innerText = "WAITING";
                    document.getElementById('pattern-text').innerText = "पैटर्न स्कैन हो रहा है...";
                }

                document.getElementById('issue-text').innerText = "पीरियड नंबर: " + short_next;
                document.getElementById('wins-count').innerText = stats.wins;
                document.getElementById('losses-count').innerText = stats.losses;

                let rows = "";
                historyLog.forEach(item => {
                    let colorStyle = item.status.includes("WIN") ? "color:#22c55e; font-weight:bold;" : (item.status.includes("LOSS") ? "color:#ef4444; font-weight:bold;" : "color:#94a3b8;");
                    rows += `<tr><td>${item.issue}</td><td>${item.num}</td><td>${item.size}</td><td style="${colorStyle}">${item.status}</td></tr>`;
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
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        client_ip = self.client_address[0]
        
        user_name = query.get('user', [''])[0]
        if not user_name:
            user_name = active_sessions.get(client_ip, {}).get("name", "Guest")
        
        if user_name != "Guest":
            active_sessions[client_ip] = {"time": time.time(), "name": user_name}

        if client_ip in blocked_ips:
            self.send_response(403)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'{"blocked": true}')
            return

        if client_ip not in active_sessions:
            active_sessions[client_ip] = {"time": time.time(), "name": user_name if user_name else "Guest"}

        current_time = time.time()
        inactive_ips = [ip for ip, data in active_sessions.items() if current_time - data["time"] > 20]
        for ip in inactive_ips:
            del active_sessions[ip]

        if path == "/ping":
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            response_data = f'{{"blocked": false, "active_devices": {len(active_sessions)}}}'
            self.wfile.write(response_data.encode('utf-8'))
            return

        elif path == "/admin":
            admin_pass = query.get('pass', [''])[0]
            if admin_pass != "8709":
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"<h1>401 Unauthorized: Invalid Admin Password!</h1>")
                return
            
            action = query.get('action', [''])[0]
            target_ip = query.get('ip', [''])[0]
            if action == 'block' and target_ip:
                blocked_ips.add(target_ip)
                if target_ip in active_sessions:
                    del active_sessions[target_ip]

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = f"""
            <html>
            <head><title>Master Admin Control</title></head>
            <body style="background:#0f172a; color:#fff; font-family:sans-serif; text-align:center; padding:20px;">
                <h1>👑 BSNV VIP Master Admin Panel 👑</h1>
                <h3>Total Active Devices: {len(active_sessions)}</h3>
                <table border="1" style="margin:20px auto; width:80%; border-collapse:collapse; text-align:center;">
                    <tr style="background:#1e293b; color:#38bdf8;"><th>User Name</th><th>Client IP</th><th>Status</th><th>Action</th></tr>
            """
            for ip, data in list(active_sessions.items()):
                html += f"<tr><td style='color:#facc15; font-weight:bold;'>{data['name']}</td><td>{ip}</td><td style='color:green;'>Active</td><td><a href='/admin?pass=8709&action=block&ip={ip}' style='color:red; font-weight:bold;'>BLOCK DEVICE</a></td></tr>"
            
            html += """
                </table>
                <br><a href="/" style="color:#38bdf8; font-size:16px; font-weight:bold;">⬅️ Back to Terminal</a>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
            return

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
