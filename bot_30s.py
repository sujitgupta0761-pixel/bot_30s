import http.server
import socketserver
import os
import time
import json
import math
import urllib.request
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

active_sessions = {}
blocked_ips = set()

# Firebase Database URL for Permanent Storage
FIREBASE_URL = "https://vipp-b3a35-default-rtdb.firebaseio.com/passwords.json"

def load_passwords():
    try:
        req = urllib.request.Request(FIREBASE_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            if data and isinstance(data, dict):
                return data
    except Exception as e:
        print("Firebase Load Error:", e)
    return {
        "vip123": {"status": "Active", "session_token": "", "expires_at": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")},
        "jivan99": {"status": "Active", "session_token": "", "expires_at": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")}
    }

def save_passwords(db):
    try:
        data = json.dumps(db).encode("utf-8")
        req = urllib.request.Request(FIREBASE_URL, data=data, method='PUT', headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=3) as response:
            pass
    except Exception as e:
        print("Firebase Save Error:", e)

user_passwords_db = load_passwords()

for p in list(user_passwords_db.keys()):
    if isinstance(user_passwords_db[p], str):
        user_passwords_db[p] = {
            "status": user_passwords_db[p], 
            "session_token": "", 
            "expires_at": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        }

security_config = {
    "password_enabled": True,
    "dashboard_password": "8709"
}

HTML_LOGIN = """<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jivan VIP Master - Secure Access</title>
    <style>
        body { background: #040814; color: #f8fafc; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: linear-gradient(145deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.9)); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 24px; padding: 40px 30px; width: 100%; max-width: 380px; text-align: center; box-shadow: 0 25px 50px rgba(0,0,0,0.9); }
        .logo-icon { font-size: 50px; margin-bottom: 15px; background: rgba(56, 189, 248, 0.1); width: 80px; height: 80px; line-height: 80px; border-radius: 50%; margin-left: auto; margin-right: auto; border: 1px solid rgba(56, 189, 248, 0.2); }
        h2 { color: #38bdf8; margin-bottom: 10px; font-size: 26px; font-weight: 900; letter-spacing: 0.5px; }
        p { font-size: 13px; color: #94a3b8; margin-bottom: 25px; line-height: 1.4; }
        input { width: 100%; padding: 15px; border-radius: 14px; border: 1px solid #475569; background: #0b1329; color: #fff; font-size: 16px; text-align: center; margin-bottom: 18px; outline: none; box-sizing: border-box; transition: 0.3s; }
        input:focus { border-color: #38bdf8; box-shadow: 0 0 15px rgba(56,189,248,0.3); }
        button { width: 100%; padding: 15px; background: linear-gradient(135deg, #0284c7, #38bdf8); color: #040814; border: 0; border-radius: 14px; font-weight: 900; font-size: 16px; cursor: pointer; transition: 0.3s; box-shadow: 0 5px 20px rgba(56,189,248,0.4); }
        button:hover { opacity: 0.95; transform: translateY(-1px); }
        .error-box { background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); padding: 12px; border-radius: 12px; margin-top: 18px; color: #f87171; font-size: 13px; line-height: 1.5; }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo-icon">👑</div>
        <h2>Jivan Master VIP</h2>
        <p>डैशबोर्ड एक्सेस करने के लिए अपना लॉगिन पासवर्ड दर्ज करें। (हर बार लॉगिन आवश्यक है)</p>
        <form method="POST">
            <input type="password" name="password" placeholder="••••••••" required autofocus>
            <button type="submit">अनलॉक करें ➔</button>
        </form>
        %ERROR_MSG%
    </div>
</body>
</html>"""

HTML_BLOCKED_HINDI = """<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Access Blocked / Expired</title>
    <style>
        body { background: #040814; color: #f8fafc; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; text-align: center; }
        .block-card { background: linear-gradient(145deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.9)); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 24px; padding: 35px 25px; width: 100%; max-width: 400px; box-shadow: 0 25px 50px rgba(0,0,0,0.9); }
        .icon { font-size: 50px; margin-bottom: 15px; }
        h1 { color: #ef4444; font-size: 20px; margin-bottom: 10px; font-weight: bold; }
        p { font-size: 13px; color: #94a3b8; line-height: 1.5; margin-bottom: 20px; }
        .copy-box { background: #0b1329; border: 1px dashed #38bdf8; padding: 12px; border-radius: 12px; font-size: 18px; color: #38bdf8; font-weight: bold; margin-bottom: 15px; user-select: all; }
        .copy-box a { color: #38bdf8; text-decoration: none; display: block; }
        .btn { display: inline-block; width: 100%; box-sizing: border-box; padding: 12px 20px; background: linear-gradient(135deg, #0284c7, #38bdf8); color: #040814; font-weight: bold; text-decoration: none; border-radius: 12px; transition: 0.3s; box-shadow: 0 5px 20px rgba(56,189,248,0.4); }
        .btn:hover { opacity: 0.9; }
    </style>
</head>
<body>
    <div class="block-card">
        <div class="icon">⌛</div>
        <h1>आपका पासवर्ड ब्लॉक या अन्य डिवाइस पर लॉगिन हो गया है!</h1>
        <p>यह पासवर्ड या तो एक्सपायर हो गया है, ब्लॉक है, या किसी अन्य मोबाइल पर उपयोग किया जा रहा है। नया पासवर्ड बनवाने के लिए संपर्क करें:</p>
        <div class="copy-box" onclick="copyId(this)" title="Click to copy">
            <a href="https://t.me/VIPGUPTAA" target="_blank">@VIPGUPTAA</a>
        </div>
        <a href="https://t.me/VIPGUPTAA" target="_blank" class="btn">टेलीग्राम पर चैट खोलें ➔</a>
    </div>
    <script>
        function copyId(el) {
            let text = "@VIPGUPTAA";
            navigator.clipboard.writeText(text).then(() => {
                alert("टेलीग्राम आईडी कॉपी हो गई है: " + text);
            });
        }
    </script>
</body>
</html>"""

HTML_MASTER_CONTENT = """<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jivan Master Dashboard VIP - Advanced Intelligence</title>
    <style>
        :root { --bg-color: #070b19; --card-bg: rgba(15, 23, 42, 0.95); --border-glow: rgba(56, 189, 248, 0.4); --text-main: #f8fafc; --accent-gold: #fbbf24; }
        body { background: var(--bg-color); color: var(--text-main); font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; padding: 10px; min-height: 100vh; display: flex; justify-content: center; align-items: center; }
        .vip-card { background: var(--card-bg); border: 2px solid var(--border-glow); border-radius: 20px; padding: 18px; width: 100%; max-width: 440px; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.9); position: relative; }
        .admin-icon-btn { position: absolute; top: 12px; right: 12px; background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; color: #f87171; padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: bold; text-decoration: none; transition: 0.3s; }
        .admin-icon-btn:hover { background: #ef4444; color: #fff; }
        .header-title { font-size: 19px; font-weight: 900; color: #38bdf8; margin-bottom: 6px; }
        .mode-selector { display: flex; gap: 6px; margin-bottom: 8px; }
        .mode-btn { flex: 1; padding: 6px; border: 0; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 12px; background: #1e1b4b; color: #94a3b8; transition: 0.3s; }
        .mode-btn.active { background: #0284c7; color: #fff; box-shadow: 0 0 10px rgba(56,189,248,0.5); }
        .top-bar { display: flex; justify-content: space-between; align-items: center; background: #1e1b4b; padding: 6px 10px; border-radius: 10px; margin-bottom: 6px; }
        .tg-control { font-size: 11px; display: flex; align-items: center; gap: 4px; color: #38bdf8; font-weight: bold; }
        .info-row { display: flex; justify-content: space-between; align-items: center; background: rgba(30, 41, 59, 0.8); padding: 5px 8px; border-radius: 8px; margin-bottom: 5px; font-size: 12px; }
        .timer-badge { background: rgba(251, 191, 36, 0.2); color: var(--accent-gold); padding: 2px 6px; border-radius: 6px; font-family: monospace; font-size: 12px; font-weight: bold; }
        .pattern-box { background: #1e1b4b; border: 1px solid #475569; color: #facc15; font-weight: 800; padding: 6px; border-radius: 8px; font-size: 11px; margin-bottom: 5px; }
        .signal-box { font-size: 32px; font-weight: 900; margin: 5px 0; padding: 8px; border-radius: 12px; background: #000; letter-spacing: 2px; color: #38bdf8; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 5px; margin-bottom: 6px; font-size: 11px; }
        .stat-card { background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; padding: 5px; border-radius: 8px; text-align: left; }
        .stat-card b { color: #38bdf8; }

        .level-mini-box { background: rgba(251, 191, 36, 0.15); border: 1px dashed var(--accent-gold); padding: 4px 8px; border-radius: 8px; margin-bottom: 5px; font-size: 11px; font-weight: bold; color: var(--accent-gold); display: flex; justify-content: space-between; align-items: center; }
        .stats-row { display: flex; justify-content: space-around; background: #1e293b; padding: 5px; border-radius: 8px; margin-bottom: 6px; font-size: 11px; font-weight: bold; }
        .table-container { max-height: 95px; overflow-y: auto; border-radius: 8px; border: 1px solid #475569; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; font-size: 10px; color: #fff; }
        th, td { padding: 4px; border-bottom: 1px solid #1e293b; text-align: center; }
        th { background: #0f172a; color: #38bdf8; position: sticky; top: 0; }
        .footer-panel { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; font-size: 10px; background: rgba(56, 189, 248, 0.1); padding: 5px 6px; border-radius: 8px; gap: 3px; }
        .action-btn { background: #38bdf8; color: #0f172a; border: 0; padding: 4px 6px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 10px; }
        .copy-btn { background: #22c55e; color: #fff; }
    </style>
</head>
<body>
    <div class="vip-card">
        <a href="/admin_master_jivan" class="admin-icon-btn">👑 Admin</a>
        <div class="header-title" id="dashboard-title">Jivan dashboard VIP 30S</div>
        <div class="mode-selector">
            <button class="mode-btn active" id="btn-30s" onclick="switchMode('30S')">⚡ 30 सेकंड</button>
            <button class="mode-btn" id="btn-1m" onclick="switchMode('1M')">🚀 1 मिनट</button>
        </div>
        <div class="top-bar">
            <button style="background:#0284c7; color:#fff; border:0; padding:4px 10px; border-radius:6px;" id="mode-badge">30S</button>
            <div class="tg-control"><span>Telegram Auto:</span> <input type="checkbox" id="tgToggle" onclick="verifyTelegram(event)"></div>
        </div>
        <div class="info-row"><span id="issue-text">पीरियड नंबर: --</span><span>समय: <span class="timer-badge" id="timer-text">00:30</span></span></div>
        <div class="pattern-box" id="pattern-text">Advanced Intelligence Initializing...</div>
        <div class="signal-box" id="signal-text">--</div>
        
        <div class="stats-grid">
            <div class="stat-card">📊 Freq: <span id="freq-stat">Big: 0% | Small: 0%</span></div>
            <div class="stat-card">🔥 Streak: <span id="streak-stat">None</span></div>
            <div class="stat-card">⛓️ Markov: <span id="markov-stat">--</span></div>
            <div class="stat-card">📐 Entropy: <span id="entropy-stat">0.00</span></div>
        </div>

        <div class="level-mini-box">
            <span>📊 वर्तमान लेवल: <span id="current-level-text" style="color:#fff;">Level 1</span></span>
            <span>💰 अमाउंट: <span id="current-amount-text" style="color:#38bdf8; font-size:12px;">₹10</span></span>
        </div>

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
            <span>🟢 एक्टिव: <span id="active-count">1</span></span>
            <button class="action-btn" onclick="openLevelMenu()">📋 Level</button>
            <button class="action-btn" onclick="editLevelAmounts()">⚙️ Edit</button>
            <button class="action-btn copy-btn" onclick="copyResultsList()">📋 Copy</button>
        </div>
    </div>
    <script>
        const API_URL_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json";
        const API_URL_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json";

        let currentMode = "30S";
        let levelAmounts = { 1: 10, 2: 25, 3: 60, 4: 150, 5: 350, 6: 800, 7: 1800, 8: 4000 };
        let currentLevel = 1;

        let lastProcessedIssue = "";
        let historyLog = [];
        let records = [];
        let stats = { wins: 0, losses: 0 };
        let shiftToCurrent = false;
        let lockedPeriod = "";
        let lockedPrediction = null;
        let lockedPattern = "";

        function switchMode(mode) {
            currentMode = mode;
            lastProcessedIssue = "";
            historyLog = [];
            records = [];
            stats = { wins: 0, losses: 0 };
            shiftToCurrent = false;
            lockedPeriod = "";
            lockedPrediction = null;
            
            if(mode === "30S") {
                document.getElementById('btn-30s').classList.add('active');
                document.getElementById('btn-1m').classList.remove('active');
                document.getElementById('dashboard-title').innerText = "Jivan dashboard VIP 30S";
                document.getElementById('mode-badge').innerText = "30S";
            } else {
                document.getElementById('btn-1m').classList.add('active');
                document.getElementById('btn-30s').classList.remove('active');
                document.getElementById('dashboard-title').innerText = "Jivan dashboard VIP 1M";
                document.getElementById('mode-badge').innerText = "1M";
            }
            fetchAndProcess();
        }

        function copyResultsList() {
            if (historyLog.length === 0 && !lockedPrediction) {
                alert("❌ अभी कोई डेटा उपलब्ध नहीं है!");
                return;
            }
            let textToCopy = "";
            let reversedLog = [...historyLog].reverse();
            reversedLog.forEach((item, index) => {
                textToCopy += `${index + 1}. Period: ${item.issue} | ${item.size} | Status: ${item.status}\\n`;
            });
            if (lockedPrediction && lockedPeriod) {
                textToCopy += `👉 LIVE Target: Period ${lockedPeriod} - ${lockedPrediction}\\n`;
            }
            navigator.clipboard.writeText(textToCopy).then(() => {
                alert("✅ लिस्ट कॉपी हो गई है!");
            }).catch(err => {
                prompt("कॉपी करें:", textToCopy);
            });
        }

        setInterval(() => {
            fetch('/ping').then(res => res.json()).then(data => {
                if(data.blocked) {
                    window.location.reload();
                } else if(data.active_devices) {
                    document.getElementById('active-count').innerText = data.active_devices;
                }
            }).catch(e => {});
        }, 3000);

        function openLevelMenu() {
            let menuText = `👑 Jivan VIP (${currentMode}) - Level Amounts 👑\\n\\n`;
            for (let lvl = 1; lvl <= 8; lvl++) {
                let marker = (lvl === currentLevel) ? " ➔ [Current]" : "";
                menuText += `Level ${lvl} : ₹${levelAmounts[lvl]}${marker}\\n`;
            }
            alert(menuText);
        }

        function editLevelAmounts() {
            let lvlChoice = prompt("किस लेवल का अमाउंट बदलना चाहते हैं? (1 से 8):");
            if (!lvlChoice) return;
            let lvlNum = parseInt(lvlChoice);
            if (isNaN(lvlNum) || lvlNum < 1 || lvlNum > 8) return;
            let newAmt = prompt(`Level ${lvlNum} के लिए नया अमाउंट दर्ज करें:`);
            if (newAmt && !isNaN(parseInt(newAmt))) {
                levelAmounts[lvlNum] = parseInt(newAmt);
                alert(`✅ Updated! Level ${lvlNum} = ₹${newAmt}`);
            }
        }

        function verifyTelegram(event) {
            let toggleBox = document.getElementById('tgToggle');
            if (toggleBox.checked) {
                toggleBox.checked = false;
                let pass = prompt("🔒 टेलीग्राम ऑटोमेशन पासवर्ड दर्ज करें:");
                if (pass === "8709") { toggleBox.checked = true; alert("✅ Telegram Enabled!"); }
                else if (pass !== null) { alert("❌ गलत पासवर्ड!"); }
            }
        }

        setInterval(() => {
            let now = new Date();
            let sec = now.getSeconds();
            let remaining = (currentMode === "30S") ? (29 - (sec % 30)) : (59 - (((now.getMinutes() * 60) + sec) % 60));
            let m = String(Math.floor(remaining / 60)).padStart(2, '0');
            let s = String(remaining % 60).padStart(2, '0');
            document.getElementById('timer-text').innerText = `${m}:${s}`;
        }, 200);

        function runAdvancedAnalysis(history_list) {
            if (!history_list || history_list.length < 5) {
                return { prediction: "WAITING", pattern: "डाटा कलेक्ट हो रहा है...", freq: "Big: 0% | Small: 0%", streak: "None", markov: "Analyzing", entropy: "0.00" };
            }

            let sizes = history_list.map(r => r.size);
            let total = sizes.length;
            let bigCount = sizes.filter(s => s === "BIG").length;
            let smallCount = total - bigCount;
            let bigPct = ((bigCount / total) * 100).toFixed(1);
            let smallPct = ((smallCount / total) * 100).toFixed(1);

            let streakCount = 1;
            let streakVal = sizes[0];
            for (let i = 0; i < sizes.length - 1; i++) {
                if (sizes[i] === sizes[i+1]) streakCount++;
                else break;
            }

            let transitions = { "BIG": { "BIG": 0, "SMALL": 0 }, "SMALL": { "BIG": 0, "SMALL": 0 } };
            for (let i = 0; i < sizes.length - 1; i++) {
                let curr = sizes[i+1];
                let next = sizes[i];
                if (transitions[curr] && transitions[curr][next] !== undefined) {
                    transitions[curr][next]++;
                }
            }
            let lastState = sizes[0];
            let tBig = transitions[lastState]["BIG"];
            let tSmall = transitions[lastState]["SMALL"];
            let markovPred = (tBig >= tSmall) ? "BIG" : "SMALL";

            let priorBig = bigCount / total;
            let bayesScoreBig = priorBig * (tBig + 1) / (tBig + tSmall + 2);
            let bayesPred = bayesScoreBig >= 0.5 ? "BIG" : "SMALL";

            let pB = bigCount / total;
            let pS = smallCount / total;
            let entropy = 0;
            if (pB > 0) entropy -= pB * Math.log2(pB);
            if (pS > 0) entropy -= pS * Math.log2(pS);

            let recent = sizes.slice(0, 4);
            let patternName = "";
            let finalPred = bayesPred;

            if (recent[0] !== recent[1] && recent[1] !== recent[2] && recent[2] !== recent[3]) {
                finalPred = (recent[0] === "BIG") ? "SMALL" : "BIG";
                patternName = `⚡ ZIG-ZAG PATTERN (${finalPred})`;
            } else if (streakCount >= 3) {
                finalPred = streakVal;
                patternName = `🐉 DRAGON STREAK (${streakCount}X ${streakVal})`;
            } else if (recent[0] === recent[1] && recent[1] !== recent[2]) {
                finalPred = (recent[0] === "BIG") ? "SMALL" : "BIG";
                patternName = `🔄 2/1 MIXED FLIP (${finalPred})`;
            } else {
                patternName = `📈 MARKOV/BAYES TREND (${finalPred})`;
            }

            return {
                prediction: finalPred,
                pattern: patternName,
                freq: `Big: ${bigPct}% | Small: ${smallPct}%`,
                streak: `${streakCount}X ${streakVal}`,
                markov: markovPred,
                entropy: entropy.toFixed(2)
            };
        }

        async function fetchWithRetry(url, retries = 2, timeout = 2500) {
            for (let i = 0; i < retries; i++) {
                try {
                    let controller = new AbortController();
                    let timer = setTimeout(() => controller.abort(), timeout);
                    let res = await fetch(url, { signal: controller.signal });
                    clearTimeout(timer);
                    if (res.ok) return await res.json();
                } catch (err) { if (i === retries - 1) throw err; }
            }
        }

        async function fetchAndProcess() {
            try {
                let activeApi = (currentMode === "30S") ? API_URL_30S : API_URL_1M;
                let json_data = await fetchWithRetry(activeApi);
                if (!json_data) return;
                let list = json_data.get?.("data")?.list || json_data.data?.list;
                if (!list || list.length === 0) return;

                if (lastProcessedIssue === "" && list.length >= 5) {
                    for (let i = Math.min(15, list.length) - 1; i >= 1; i--) {
                        let p_num = parseInt(list[i].number !== undefined ? list[i].number : list[i].winningNumber);
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
                        if (records[0].predicted === actual_size) {
                            stats.wins++; result_status = "👑 WIN ⚡"; currentLevel = 1;
                        } else {
                            stats.losses++; result_status = "LOSS 🤬";
                            if (currentLevel < 8) currentLevel++;
                        }
                    }

                    records.unshift({ size: actual_size, predicted: lockedPrediction });
                    if (records.length > 40) records.pop();
                    historyLog.unshift({ issue: issueId.slice(-4), num: num, size: actual_size, status: result_status });
                    if (historyLog.length > 25) historyLog.pop();
                    lockedPrediction = null;
                }

                let next_issue = String(BigInt(issueId) + 1n);
                let short_next = next_issue.slice(-4);

                if (lockedPeriod !== short_next) {
                    let analysis = runAdvancedAnalysis(records);
                    if (analysis.prediction !== "WAITING") {
                        lockedPeriod = short_next;
                        lockedPrediction = analysis.prediction;
                        lockedPattern = analysis.pattern;
                        if(records.length > 0) records[0].predicted = lockedPrediction;
                        
                        document.getElementById('freq-stat').innerText = analysis.freq;
                        document.getElementById('streak-stat').innerText = analysis.streak;
                        document.getElementById('markov-stat').innerText = analysis.markov;
                        document.getElementById('entropy-stat').innerText = analysis.entropy;
                    }
                }

                document.getElementById('signal-text').innerText = lockedPrediction || "WAITING";
                document.getElementById('pattern-text').innerText = lockedPattern || "विश्लेषण जारी है...";
                document.getElementById('issue-text').innerText = "पीरियड नंबर: " + short_next;
                document.getElementById('wins-count').innerText = stats.wins;
                document.getElementById('losses-count').innerText = stats.losses;
                document.getElementById('current-level-text').innerText = `Level ${currentLevel}`;
                document.getElementById('current-amount-text').innerText = `₹${levelAmounts[currentLevel]}`;

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
        client_ip = self.headers.get('X-Forwarded-For', self.client_address[0]).split(',')[0].strip()
        
        if client_ip in blocked_ips:
            if path == "/ping":
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write('{"blocked": true}'.encode('utf-8'))
                return
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_BLOCKED_HINDI.encode('utf-8'))
            return

        if path == "/admin_master_jivan":
            cookie_header = self.headers.get('Cookie', '')
            if "admin_auth=master_verified" not in cookie_header:
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                admin_login_html = HTML_LOGIN.replace('डैशबोर्ड एक्सेस करने के लिए अपना लॉगिन पासवर्ड दर्ज करें।', 'मास्टर एडमिन पैनल खोलने के लिए मास्टर पासवर्ड दर्ज करें।')
                self.wfile.write(admin_login_html.replace('%ERROR_MSG%', '').encode('utf-8'))
                return
            
            action = query.get('action', [''])[0]
            target_ip = query.get('ip', [''])[0]
            target_upass = query.get('upass', [''])[0]
            new_upass = query.get('new_upass', [''])[0]
            duration_type = query.get('duration', ['30'])[0]

            if action == 'block' and target_ip: blocked_ips.add(target_ip)
            elif action == 'unblock' and target_ip: blocked_ips.discard(target_ip)
            elif action == 'toggle_sec': security_config["password_enabled"] = not security_config["password_enabled"]
            elif action == 'set_pass':
                new_p = query.get('new_p', [''])[0]
                if new_p: security_config["dashboard_password"] = new_p
            elif action == 'add_user' and new_upass:
                days = int(duration_type)
                exp_date = datetime.now() + timedelta(days=days)
                user_passwords_db[new_upass.strip()] = {
                    "status": "Active", 
                    "session_token": "", 
                    "expires_at": exp_date.strftime("%Y-%m-%d %H:%M:%S")
                }
                save_passwords(user_passwords_db)
            elif action == 'block_user' and target_upass:
                if target_upass in user_passwords_db: 
                    user_passwords_db[target_upass]["status"] = "Blocked"
                    save_passwords(user_passwords_db)
            elif action == 'unblock_user' and target_upass:
                if target_upass in user_passwords_db: 
                    user_passwords_db[target_upass]["status"] = "Active"
                    user_passwords_db[target_upass]["session_token"] = ""
                    save_passwords(user_passwords_db)
            elif action == 'extend_user' and target_upass:
                days = int(duration_type)
                if target_upass in user_passwords_db:
                    try:
                        current_exp = datetime.strptime(user_passwords_db[target_upass].get("expires_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")
                        if current_exp < datetime.now():
                            current_exp = datetime.now()
                        new_exp = current_exp + timedelta(days=days)
                        user_passwords_db[target_upass]["expires_at"] = new_exp.strftime("%Y-%m-%d %H:%M:%S")
                        user_passwords_db[target_upass]["status"] = "Active"
                        save_passwords(user_passwords_db)
                    except Exception as e:
                        print("Extend Error:", e)
            elif action == 'delete_user' and target_upass:
                if target_upass in user_passwords_db: 
                    del user_passwords_db[target_upass]
                    save_passwords(user_passwords_db)

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = f"""
            <html>
            <head><title>Jivan Master Admin Panel</title></head>
            <body style="background:#0f172a; color:#fff; font-family:sans-serif; text-align:center; padding:20px;">
                <h1>👑 Advanced Jivan Master Admin Panel 👑</h1>
                <div style="background:#1e293b; padding:15px; border-radius:10px; margin:15px auto; width:80%; max-width:650px; border:1px solid #38bdf8;">
                    <h3 style="color:#fbbf24;">Master Password: {security_config["dashboard_password"]}</h3>
                    <a href="/admin_master_jivan?action=toggle_sec" style="background:#38bdf8; color:#0f172a; padding:6px 12px; text-decoration:none; border-radius:6px; font-weight:bold;">Security Toggle</a>
                </div>

                <div style="background:#1e293b; padding:15px; border-radius:10px; margin:15px auto; width:80%; max-width:650px; border:1px solid #22c55e;">
                    <h3 style="color:#22c55e; margin-top:0;">👥 Add Time-Based User Password (Hafte/Mahine)</h3>
                    <form action="/admin_master_jivan" method="GET">
                        <input type="hidden" name="action" value="add_user">
                        <input type="text" name="new_upass" placeholder="नया यूजर पासवर्ड" style="padding:8px; border-radius:6px; width:45%;" required>
                        <select name="duration" style="padding:8px; border-radius:6px; background:#0b1329; color:#fff;">
                            <option value="7">📅 7 दिन (Weekly)</option>
                            <option value="30" selected>📅 30 दिन (Monthly)</option>
                            <option value="1">⏱️ 1 दिन (Demo)</option>
                        </select>
                        <button type="submit" style="background:#22c55e; color:#fff; border:0; padding:8px 12px; border-radius:6px; font-weight:bold; cursor:pointer;">पासवर्ड जोड़ें</button>
                    </form>
                </div>

                <h3>Registered User Passwords & Validity (Single Device Locked)</h3>
                <table border="1" style="margin:10px auto; width:95%; max-width:850px; border-collapse:collapse; text-align:center;">
                    <tr style="background:#1e293b; color:#38bdf8;"><th>Password</th><th>Status</th><th>Validity Expiry</th><th>Session Active</th><th>Actions</th></tr>
            """
            for upass, udata in user_passwords_db.items():
                ustat = udata.get("status", "Active")
                session_tok = udata.get("session_token", "")
                has_session = "Yes (Locked)" if session_tok else "No"
                exp_str = udata.get("expires_at", "N/A")
                
                try:
                    exp_dt = datetime.strptime(exp_str, "%Y-%m-%d %H:%M:%S")
                    if datetime.now() > exp_dt and ustat == "Active":
                        ustat = "Expired"
                except Exception:
                    pass

                stat_html = "<span style='color:green;'>Active</span>" if ustat == "Active" else ("<span style='color:orange;'>Expired</span>" if ustat == "Expired" else "<span style='color:red;'>Blocked</span>")
                
                act = f"<a href='/admin_master_jivan?action=block_user&upass={upass}' style='color:red; font-weight:bold;'>BLOCK</a>" if ustat != "Blocked" else f"<a href='/admin_master_jivan?action=unblock_user&upass={upass}' style='color:green; font-weight:bold;'>UNBLOCK</a>"
                ext = f"<a href='/admin_master_jivan?action=extend_user&upass={upass}&duration=30' style='color:#38bdf8; font-weight:bold;'>+30D</a>"
                del_btn = f"<a href='/admin_master_jivan?action=delete_user&upass={upass}' style='color:#fbbf24; font-weight:bold;'>DEL</a>"
                
                html += f"<tr><td><b>{upass}</b></td><td>{stat_html}</td><td style='font-size:11px; color:#facc15;'>{exp_str}</td><td style='font-size:11px; color:#38bdf8;'>{has_session}</td><td>{act} | {ext} | {del_btn}</td></tr>"
            
            html += """
                </table>
                <br><a href="/" style="color:#38bdf8; font-weight:bold; font-size:16px;">⬅️ Back to Dashboard</a>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
            return

        # Check Auth Cookie for Main Dashboard (Session-Based: No Max-Age, asks every time browser restarts)
        if security_config["password_enabled"]:
            cookie_header = self.headers.get('Cookie', '')
            auth_cookie = ""
            for cookie in cookie_header.split(';'):
                if 'auth_token=' in cookie:
                    auth_cookie = cookie.split('auth_token=')[1].strip()
            
            if not auth_cookie or not auth_cookie.startswith("jivan_vip_"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(HTML_LOGIN.replace('%ERROR_MSG%', '').encode('utf-8'))
                return
            
            pass_key = auth_cookie.replace("jivan_vip_", "")
            if pass_key not in user_passwords_db:
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(HTML_LOGIN.replace('%ERROR_MSG%', '').encode('utf-8'))
                return
            
            user_data = user_passwords_db[pass_key]
            
            exp_str = user_data.get("expires_at", "")
            is_expired = False
            if exp_str:
                try:
                    if datetime.now() > datetime.strptime(exp_str, "%Y-%m-%d %H:%M:%S"):
                        is_expired = True
                except:
                    pass

            current_token_in_cookie = ""
            for c in cookie_header.split(';'):
                if 'device_session=' in c:
                    current_token_in_cookie = c.split('device_session=')[1].strip()

            if user_data.get("status") != "Active" or is_expired or (user_data.get("session_token") != current_token_in_cookie):
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(HTML_BLOCKED_HINDI.encode('utf-8'))
                return

        active_sessions[client_ip] = time.time()
        if path == "/ping":
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write('{"blocked": false}'.encode('utf-8'))
            return

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML_MASTER_CONTENT.encode('utf-8'))

    def do_POST(self):
        client_ip = self.headers.get('X-Forwarded-For', self.client_address[0]).split(',')[0].strip()
        if client_ip in blocked_ips:
            self.send_response(403)
            self.end_headers()
            return

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = parse_qs(post_data)
        entered_pass = params.get('password', [''])[0].strip()

        if self.path.startswith("/admin_master_jivan") and entered_pass == security_config["dashboard_password"]:
            self.send_response(303)
            # Admin session cookie without Max-Age so it prompts or stays secure for current session
            self.send_header('Set-Cookie', 'admin_auth=master_verified; Path=/')
            self.send_header('Location', '/admin_master_jivan')
            self.end_headers()
            return

        if entered_pass in user_passwords_db:
            user_data = user_passwords_db[entered_pass]
            
            exp_str = user_data.get("expires_at", "")
            if exp_str:
                try:
                    exp_dt = datetime.strptime(exp_str, "%Y-%m-%d %H:%M:%S")
                    if datetime.now() > exp_dt:
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(HTML_BLOCKED_HINDI.encode('utf-8'))
                        return
                except Exception:
                    pass

            if user_data.get("status") == "Blocked":
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(HTML_BLOCKED_HINDI.encode('utf-8'))
                return

            import uuid
            new_device_token = str(uuid.uuid4())
            user_data["session_token"] = new_device_token
            save_passwords(user_passwords_db)

            self.send_response(303)
            # Session-only Cookies (No Max-Age), meaning when browser closes, login expires and requires password again!
            self.send_header('Set-Cookie', f'auth_token=jivan_vip_{entered_pass}; Path=/')
            self.send_header('Set-Cookie', f'device_session={new_device_token}; Path=/')
            self.send_header('Location', '/')
            self.end_headers()
            return

        if entered_pass == security_config["dashboard_password"]:
            self.send_response(303)
            self.send_header('Set-Cookie', 'auth_token=jivan_master_auth; Path=/')
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            err_html = HTML_LOGIN.replace('%ERROR_MSG%', '<div class="error-box">❌ गलत पासवर्ड! कृपया सही पासवर्ड दर्ज करें।</div>')
            self.wfile.write(err_html.encode('utf-8'))

    def log_message(self, format, *args): pass

def run_server():
    PORT = int(os.environ.get("PORT", 8000))
    with socketserver.TCPServer(("", PORT), DashboardServer) as httpd:
        print(f"🌐 Advanced Jivan Master Bot Server Live on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
