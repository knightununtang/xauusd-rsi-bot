# XAU/USD (Gold) RSI Telegram Alert Bot 📈🔔

A lightweight, robust Python system that monitors 5-minute interval Gold (XAU/USD) price data, calculates the 14-period Relative Strength Index (RSI), and dispatches real-time alerts to a Telegram chat whenever RSI drops strictly below a defined threshold (default: 35).

---

## 🌟 Key Features

- **Real-Time Data**: Fetches 5m timeframe data for Gold (`GC=F` symbol) using Yahoo Finance (`yfinance`).
- **Standard Wilder RSI**: Computes standard 14-period RSI using Wilder's Exponential Smoothing algorithm.
- **Telegram Notifications**: Sends Markdown-formatted alerts containing price, RSI value, timestamp, and alert status.
- **Alert Cooldown Mechanism**: Prevents continuous notification spamming when RSI remains under the threshold over consecutive candles. Resets automatically when RSI recovers above the threshold.
- **Resilient & Reliable**: Comprehensive logging and exception handling to survive temporary network or API failures.
- **Configurable Environment**: Clean configuration separation using `python-dotenv`.

---

## 📁 Project Structure

```
xauusd_rsi_bot/
├── config.py          # Environment & settings loader
├── main.py            # Main application loop, RSI logic, Telegram integration
├── requirements.txt   # Python dependency declarations
├── .env.example       # Sample environment configuration file
├── .gitignore         # Excluded files for git repository
└── README.md          # Project documentation
```

---

## 🚀 Quick Start & Installation

### 1. Clone or Download Project
Navigate into the project directory:
```bash
cd xauusd_rsi_bot
```

### 2. Create Virtual Environment
Create and activate a isolated Python virtual environment:

**On Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
Install all required libraries:
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration Setup

### 1. Obtain Telegram Credentials

1. **Bot Token**:
   - Message `@BotFather` on Telegram.
   - Run `/newbot` and follow the prompts to create your bot.
   - Copy the HTTP API token provided (e.g., `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).

2. **Chat ID**:
   - Send a message to your new bot.
   - Search for `@userinfobot` or `@GetMyChatID_Bot` on Telegram to get your user or group **Chat ID** (e.g., `987654321`).

### 2. Create `.env` File

Copy `.env.example` to create `.env`:

**Linux/macOS:**
```bash
cp .env.example .env
```

**Windows:**
```powershell
copy .env.example .env
```

Edit `.env` with your preferred settings and credentials:
```env
# Telegram Credentials
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=987654321

# Monitoring Settings
CHECK_INTERVAL=300
RSI_THRESHOLD=35
SYMBOL=GC=F
TIMEFRAME=5m
RSI_PERIOD=14
```

---

## 🏃 Running the Bot

Run the script directly:
```bash
python main.py
```

### Example Terminal Output
```
2026-10-02 11:15:00 [INFO] ==================================================
2026-10-02 11:15:00 [INFO]   XAU/USD (Gold) RSI Telegram Alert System Active  
2026-10-02 11:15:00 [INFO] ==================================================
2026-10-02 11:15:00 [INFO] Target Symbol : GC=F
2026-10-02 11:15:00 [INFO] Timeframe     : 5m
2026-10-02 11:15:00 [INFO] RSI Period    : 14
2026-10-02 11:15:00 [INFO] RSI Threshold : < 35.0
2026-10-02 11:15:00 [INFO] Check Interval: 300 seconds
2026-10-02 11:15:00 [INFO] --------------------------------------------------
2026-10-02 11:15:01 [INFO] Fetching 5m timeframe market data for GC=F...
2026-10-02 11:15:02 [INFO] [2026-10-02 04:10:00 UTC] Price: $2,654.30 | RSI (5m): 32.14
2026-10-02 11:15:02 [WARNING] 🚨 ALERT TRIGGERED: RSI (32.14) < Threshold (35.0)
2026-10-02 11:15:03 [INFO] Telegram alert delivered successfully.
2026-10-02 11:15:03 [INFO] Cooldown activated: Further alerts will be suppressed while RSI remains < threshold.
```

---

## 🖥️ Server / Production Deployment

### Option A: Background Execution using `nohup` (Linux)
```bash
nohup python main.py > bot.log 2>&1 &
```

### Option B: Linux `systemd` Service
Create a service file at `/etc/systemd/system/xauusd-rsi-bot.service`:
```ini
[Unit]
Description=XAU/USD RSI Telegram Alert Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/xauusd_rsi_bot
ExecStart=/path/to/xauusd_rsi_bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable xauusd-rsi-bot
sudo systemctl start xauusd-rsi-bot
sudo systemctl status xauusd-rsi-bot
```

---

## 🛠️ Verification & Testing

To test the project code locally:
1. Ensure dependencies (`yfinance`, `pandas`, `requests`, `python-dotenv`) are installed.
2. Run `python main.py`. The bot will output current live price and RSI values to the console.
