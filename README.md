# Saftrade 🎯

> **Automated AI-Powered Trading Bot for the Indonesian Stock Market (IDX/IHSG)**

![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen)

**Saftrade** is a sophisticated trading bot designed to hunt for high-probability setups in the Indonesian market. It combines **Technical Analysis** (Trend, Momentum, Volatility) with **AI Validation** (DeepSeek LLM) to filter out "false positives" and "pump-and-dump" traps before alerting you via Telegram.

---

## ✨ Key Features

- **Hybrid Data Engine** 🛡️
  - **Primary**: Uses [GoAPI](https://goapi.io) for fast bulk data fetching.
  - **Failover**: Automatically switches to **Yahoo Finance** (`yfinance`) if GoAPI rate limits are hit or if no API key is provided. Zero downtime.
- **Dual Strategy Engine** ⚔️
  - **Trend Swing**: Catches safe, uptrending stocks (Price > EMA200 + RSI Bounce).
  - **Gorengan Mode (Volatility Breakout)**: Hunts for high-risk, high-reward spikes (Volume > 2x Avg, Price > 3%) with "Falling Knife" protection.
- **AI Analyst Core** 🧠
  - Every technical signal is reviewed by a "Senior Hedge Fund Analyst" persona (DeepSeek AI).
  - Rejects overbought "traps" or "manipulation" patterns.
  - Accepts high-risk plays ONLY with explicit warnings and tight stop-loss plans.
- **Real-Time Notifications** 🔔
  - Sends formatted trade plans (Entry, SL, TP) directly to Telegram.

---

## 🚀 Installation

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/) (Recommended) or pip

### Quick Start

1.  **Clone the Repository**

    ```bash
    git clone https://github.com/yourusername/saftrade.git
    cd saftrade
    ```

2.  **Install Dependencies**

    ```bash
    poetry install
    # OR
    pip install -r requirements.txt
    ```

3.  **Configure Environment**
    Copy the example config and edit it:

    ```bash
    cp .env.example .env
    ```

    - `DEEPSEEK_API_KEY`: Required for AI analysis.
    - `TELEGRAM_BOT_TOKEN`: Required for alerts.
    - `GOAPI_KEY`: (Optional) Leave empty to run 100% free on Yahoo Finance.

4.  **Run the Bot**
    ```bash
    poetry run python main.py
    ```

---

## ⚙️ Configuration

Start with `config/watchlist.py` to define your target stocks:

```python
WATCHLIST = ["BBCA", "BBRI", "BMRI", "BUMI", "GOTO"]
```

Tweaking strategies in `config/settings.py`:

- `VOL_BREAKOUT_FACTOR = 2.0` (Volume multiplier for breakouts)
- `RSI_OVERSOLD = 30` (Buy zone for swing trades)

---

## 🤖 Decision Logic

The bot follows a strict **3-Step Funnel**:

1.  **Technical Filter (The Math)**
    - _Scan_: Does `Close > EMA200`? Is `Volume > 2x Avg`?
    - _Pass_: Signal detected.
2.  **AI Analyst (The Brain)**
    - _Prompt_: "Here is the chart data. Is this a pump-and-dump?"
    - _Pass_: AI says "Valid Setup".
3.  **Notification (The Alert)**
    - You receive a Telegram message with a Trade Plan.

---

## ⚠️ Disclaimer

**Educational Purpose Only.**
This software is for educational and research purposes. It is not financial advice. Trading stocks involves risk of loss. The authors and contributors are not responsible for any financial losses incurred from using this bot. Use the AI's trade plans at your own discretion.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
