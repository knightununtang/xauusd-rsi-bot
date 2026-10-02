import time
import logging
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import config

# Configure logging format and level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("XAUUSD_RSI_Bot")


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate the Relative Strength Index (RSI) using Wilder's Smoothing method.
    
    :param series: Pandas Series of close prices.
    :param period: RSI calculation period (default 14).
    :return: Pandas Series containing RSI values.
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's Exponential Moving Average
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def send_telegram_alert(token: str, chat_id: str, message: str) -> bool:
    """
    Send a Markdown-formatted alert message to Telegram.
    
    :param token: Telegram Bot Token.
    :param chat_id: Telegram Chat ID.
    :param message: Formatted string message to send.
    :return: Boolean indicating success or failure.
    """
    if not token or not chat_id:
        logger.error("Telegram BOT Token or Chat ID is missing! Skipping alert delivery.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        res_data = response.json()
        if res_data.get("ok"):
            logger.info("Telegram alert delivered successfully.")
            return True
        else:
            logger.error(f"Telegram API error response: {res_data.get('description')}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while reaching Telegram API: {e}")
        return False


def fetch_market_data(symbol: str, interval: str = "5m", period: str = "5d") -> pd.DataFrame:
    """
    Fetch market OHLCV data using yfinance.
    
    :param symbol: Financial instrument ticker (e.g., 'GC=F' for Gold Futures).
    :param interval: Data timeframe interval (e.g., '5m').
    :param period: Lookback timeframe (e.g., '5d').
    :return: DataFrame with historical market prices.
    """
    logger.info(f"Fetching {interval} timeframe market data for {symbol}...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    if df.empty:
        raise ValueError(f"No price data received for symbol '{symbol}' on timeframe '{interval}'.")
    return df


def get_rsi_state(rsi: float) -> str:
    """
    Determine current RSI zone state.
    """
    if rsi > config.RSI_HIGH_75:
        return "OVERBOUGHT_75"
    elif rsi > config.RSI_HIGH_65:
        return "OVERBOUGHT_65"
    elif rsi < config.RSI_LOW_25:
        return "OVERSOLD_25"
    elif rsi < config.RSI_LOW_35:
        return "OVERSOLD_35"
    return "NORMAL"


def run_monitor():
    """
    Main execution loop monitoring RSI and sending alerts with cooldown state handling.
    """
    logger.info("==================================================")
    logger.info("  XAU/USD (Gold) RSI Telegram Alert System Active  ")
    logger.info("==================================================")
    logger.info(f"Target Symbol  : {config.SYMBOL}")
    logger.info(f"Timeframe      : {config.TIMEFRAME}")
    logger.info(f"RSI Period     : {config.RSI_PERIOD}")
    logger.info(f"Overbought     : > {config.RSI_HIGH_65} (Extreme: > {config.RSI_HIGH_75})")
    logger.info(f"Oversold       : < {config.RSI_LOW_35} (Extreme: < {config.RSI_LOW_25})")
    logger.info(f"Check Interval : {config.CHECK_INTERVAL} seconds")
    logger.info("--------------------------------------------------")

    current_state = "NORMAL"  # State tracker: NORMAL, OVERBOUGHT_65, OVERBOUGHT_75, OVERSOLD_35, OVERSOLD_25

    while True:
        try:
            # Fetch 5 days of 5m candles (guarantees >= 14 candles across weekends/sessions)
            df = fetch_market_data(config.SYMBOL, interval=config.TIMEFRAME, period="5d")
            
            if len(df) < config.RSI_PERIOD + 1:
                logger.warning(f"Insufficient candle data (found {len(df)} rows, required >= {config.RSI_PERIOD + 1}). Retrying next interval...")
                time.sleep(config.CHECK_INTERVAL)
                continue

            # Calculate RSI
            df['RSI'] = calculate_rsi(df['Close'], period=config.RSI_PERIOD)
            
            # Extract latest completed candle
            latest_candle = df.iloc[-1]
            current_price = float(latest_candle['Close'])
            current_rsi = float(latest_candle['RSI'])
            
            # Parse timestamp safely
            raw_timestamp = df.index[-1]
            candle_time = raw_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if hasattr(raw_timestamp, 'strftime') else str(raw_timestamp)

            if pd.isna(current_rsi):
                logger.warning("Computed RSI value is NaN. Retrying next cycle...")
                time.sleep(config.CHECK_INTERVAL)
                continue

            logger.info(f"[{candle_time}] Price: ${current_price:,.2f} | RSI ({config.TIMEFRAME}): {current_rsi:.2f}")

            new_state = get_rsi_state(current_rsi)

            # Trigger alert if entering a new threshold state (e.g. NORMAL -> OVERBOUGHT_65 or OVERBOUGHT_65 -> OVERBOUGHT_75)
            if new_state != "NORMAL" and new_state != current_state:
                if new_state == "OVERBOUGHT_75":
                    header = "🚨 *XAU/USD EXTREME OVERBOUGHT ALERT (> 75)* 🔴🔴"
                    status = f"🔥 *Status:* Gold RSI is critically overbought (> {config.RSI_HIGH_75})! High risk of pullback."
                    threshold_label = f"> {config.RSI_HIGH_75}"
                elif new_state == "OVERBOUGHT_65":
                    header = "⚠️ *XAU/USD OVERBOUGHT ALERT (> 65)* 🔴"
                    status = f"📈 *Status:* Gold RSI entered overbought zone (> {config.RSI_HIGH_65})."
                    threshold_label = f"> {config.RSI_HIGH_65}"
                elif new_state == "OVERSOLD_25":
                    header = "🚨 *XAU/USD EXTREME OVERSOLD ALERT (< 25)* 🟢🟢"
                    status = f"💎 *Status:* Gold RSI is critically oversold (< {config.RSI_LOW_25})! High potential for price bounce."
                    threshold_label = f"< {config.RSI_LOW_25}"
                else:  # OVERSOLD_35
                    header = "⚠️ *XAU/USD OVERSOLD ALERT (< 35)* 🟢"
                    status = f"📉 *Status:* Gold RSI entered oversold zone (< {config.RSI_LOW_35})."
                    threshold_label = f"< {config.RSI_LOW_35}"

                logger.warning(f"🚨 ALERT TRIGGERED: State [{new_state}] | RSI: {current_rsi:.2f}")

                alert_message = (
                    f"{header}\n\n"
                    f"• *Symbol:* `{config.SYMBOL}` (Gold)\n"
                    f"• *Current Price:* `${current_price:,.2f}`\n"
                    f"• *RSI ({config.TIMEFRAME}):* `{current_rsi:.2f}` _(Threshold: {threshold_label})_\n"
                    f"• *Timestamp:* `{candle_time}`\n\n"
                    f"{status}"
                )

                if send_telegram_alert(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, alert_message):
                    current_state = new_state
                    logger.info(f"Alert state updated to [{current_state}]. Cooldown active for this zone.")
            elif new_state == "NORMAL" and current_state != "NORMAL":
                logger.info(f"RSI returned to normal range ({current_rsi:.2f}). State reset from [{current_state}] to [NORMAL].")
                current_state = "NORMAL"
            elif new_state == current_state and new_state != "NORMAL":
                logger.info(f"RSI remains in alert zone [{current_state}] ({current_rsi:.2f}). Alert suppressed by cooldown.")

        except Exception as e:
            logger.error(f"Unhandled error in monitoring loop: {e}")

        time.sleep(config.CHECK_INTERVAL)



def check_once():
    """
    Perform a single check cycle (ideal for GitHub Actions / Cron jobs).
    """
    try:
        df = fetch_market_data(config.SYMBOL, interval=config.TIMEFRAME, period="5d")
        if len(df) < config.RSI_PERIOD + 1:
            logger.warning(f"Insufficient candle data (found {len(df)} rows). Exiting.")
            return

        df['RSI'] = calculate_rsi(df['Close'], period=config.RSI_PERIOD)
        latest_candle = df.iloc[-1]
        current_price = float(latest_candle['Close'])
        current_rsi = float(latest_candle['RSI'])

        raw_timestamp = df.index[-1]
        candle_time = raw_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if hasattr(raw_timestamp, 'strftime') else str(raw_timestamp)

        if pd.isna(current_rsi):
            logger.warning("Computed RSI is NaN. Exiting.")
            return

        logger.info(f"[{candle_time}] Price: ${current_price:,.2f} | RSI ({config.TIMEFRAME}): {current_rsi:.2f}")

        rsi_state = get_rsi_state(current_rsi)
        if rsi_state != "NORMAL":
            if rsi_state == "OVERBOUGHT_75":
                header = "🚨 *XAU/USD EXTREME OVERBOUGHT ALERT (> 75)* 🔴🔴"
                status = f"🔥 *Status:* Gold RSI is critically overbought (> {config.RSI_HIGH_75})! High risk of pullback."
                threshold_label = f"> {config.RSI_HIGH_75}"
            elif rsi_state == "OVERBOUGHT_65":
                header = "⚠️ *XAU/USD OVERBOUGHT ALERT (> 65)* 🔴"
                status = f"📈 *Status:* Gold RSI entered overbought zone (> {config.RSI_HIGH_65})."
                threshold_label = f"> {config.RSI_HIGH_65}"
            elif rsi_state == "OVERSOLD_25":
                header = "🚨 *XAU/USD EXTREME OVERSOLD ALERT (< 25)* 🟢🟢"
                status = f"💎 *Status:* Gold RSI is critically oversold (< {config.RSI_LOW_25})! High potential for price bounce."
                threshold_label = f"< {config.RSI_LOW_25}"
            else:  # OVERSOLD_35
                header = "⚠️ *XAU/USD OVERSOLD ALERT (< 35)* 🟢"
                status = f"📉 *Status:* Gold RSI entered oversold zone (< {config.RSI_LOW_35})."
                threshold_label = f"< {config.RSI_LOW_35}"

            logger.warning(f"🚨 ALERT TRIGGERED: State [{rsi_state}] | RSI: {current_rsi:.2f}")

            alert_message = (
                f"{header}\n\n"
                f"• *Symbol:* `{config.SYMBOL}` (Gold)\n"
                f"• *Current Price:* `${current_price:,.2f}`\n"
                f"• *RSI ({config.TIMEFRAME}):* `{current_rsi:.2f}` _(Threshold: {threshold_label})_\n"
                f"• *Timestamp:* `{candle_time}`\n\n"
                f"{status}"
            )
            send_telegram_alert(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, alert_message)
        else:
            logger.info("RSI is in normal range. No alert sent.")
    except Exception as e:
        logger.error(f"Error during single execution check: {e}")


if __name__ == "__main__":
    import sys
    if "--once" in sys.argv:
        check_once()
    else:
        run_monitor()

