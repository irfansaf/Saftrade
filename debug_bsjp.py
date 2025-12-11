import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta

# BSJP Constants
BSJP_CLOSE_THRESHOLD = 0.90
BSJP_MIN_VOLUME = 1.0

def debug_bsjp():
    symbol = "BUMI.JK"
    
    # Range to include today
    to_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    
    print(f"Fetching {symbol} up to {to_date}...")
    df = yf.download(symbol, start=from_date, end=to_date, progress=False)
    
    # Fix MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    
    # Calculate Vol Avg
    # YFinance uses Capitalized columns: 'Close', 'Open', 'Volume'
    df['vol_avg'] = ta.sma(df['Volume'], length=20)
    
    latest = df.iloc[-1]
    
    # Data Extraction
    high = latest['High']
    low = latest['Low']
    close = latest['Close']
    open_p = latest['Open']
    vol = latest['Volume']
    vol_avg = latest['vol_avg']
    
    print("\n--- Candle Analysis ---")
    print(f"Date: {latest.name}")
    print(f"Open: {open_p}")
    print(f"High: {high}")
    print(f"Low:  {low}")
    print(f"Close: {close}")
    print(f"Vol: {vol} (Avg: {vol_avg:.0f})")
    
    # BSJP Check
    day_range = high - low
    ratio = (close - low) / day_range if day_range > 0 else 0
    vol_ratio = vol / vol_avg if vol_avg > 0 else 0
    
    print("\n--- BSJP Logic Check ---")
    print(f"1. Green Candle? {close > open_p}")
    print(f"2. Strong Close Ratio: {ratio:.4f} (Required: >= {BSJP_CLOSE_THRESHOLD})")
    print(f"3. Volume Ratio: {vol_ratio:.2f} (Required: > {BSJP_MIN_VOLUME})")
    
    if close > open_p and ratio >= BSJP_CLOSE_THRESHOLD and vol_ratio > BSJP_MIN_VOLUME:
        print("\nRESULT: VALID BSJP")
    else:
        print("\nRESULT: NOT VALID")

if __name__ == "__main__":
    debug_bumi_bsjp()
