import pandas as pd
import pandas_ta as ta
from typing import Dict, Any
from config.settings import (
    RSI_OVERSOLD, VOLUME_SPIKE_FACTOR, EMA_LONG, EMA_MEDIUM, EMA_SHORT,
    VOL_BREAKOUT_FACTOR, MIN_PRICE_CHANGE,
    BSJP_CLOSE_THRESHOLD, BSJP_MIN_VOLUME
)

class TechnicalAnalyzer:
    def __init__(self):
        pass

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze a single stock's dataframe for swing trading setup.
        Expected DF columns: 'open', 'high', 'low', 'close', 'volume'
        """
        if len(df) < EMA_LONG:
            # Fallback for young stocks or short history -> Check Breakout only? 
            # For now, let's just return limitation, but normally we'd allow breakout check.
            pass

        # Calculate Indicators
        # EMA
        if len(df) >= EMA_LONG:
            df['ema_200'] = ta.ema(df['close'], length=EMA_LONG)
        else:
            df['ema_200'] = 0 # Placeholder
            
        df['ema_50'] = ta.ema(df['close'], length=EMA_MEDIUM)
        df['ema_20'] = ta.ema(df['close'], length=EMA_SHORT)
        
        # RSI
        df['rsi'] = ta.rsi(df['close'], length=14)
        
        # ATR (for Volatility/SL)
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        
        # Volume SMA
        df['vol_avg'] = ta.sma(df['volume'], length=20)

        # Get latest candle (assuming DF is sorted ascending, last row is today)
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # --- Criteria Checks ---
        
        # 1. Trend: Price > EMA 200
        is_uptrend = (latest['close'] > latest['ema_200']) if latest['ema_200'] > 0 else False
        
        # 2. Momentum:
        # A) RSI crosses above 30 (Oversold Bounce)
        rsi_bounce = (prev['rsi'] < RSI_OVERSOLD) and (latest['rsi'] >= RSI_OVERSOLD)
        
        # B) Golden Cross (EMA20 > EMA50)
        golden_cross = (prev['ema_20'] < prev['ema_50']) and (latest['ema_20'] > latest['ema_50'])
        
        # Combined Momentum signal (OR condition per PRD)
        momentum_signal = rsi_bounce or golden_cross
        
        # 3. Volume Spike
        is_volume_spike = latest['volume'] > (latest['vol_avg'] * VOLUME_SPIKE_FACTOR)
        
        # --- NEW: Volatility Breakout (Gorengan Mode) ---
        # Logic: 
        # 1. Volume > 2x Avg
        # 2. Price Change > 3% (approx)
        # 3. Close > Open (Green Candle)
        
        price_change_pct = (latest['close'] - prev['close']) / prev['close']
        is_breakout_vol = latest['volume'] > (latest['vol_avg'] * VOL_BREAKOUT_FACTOR)
        is_strong_move = price_change_pct > MIN_PRICE_CHANGE
        is_green = latest['close'] > latest['open']
        
        is_volatility_breakout = is_breakout_vol and is_strong_move and is_green

        # --- NEW: BSJP (Beli Sore Jual Pagi) ---
        # Logic:
        # 1. Close > Open (Green Candle)
        # 2. Strong Close: Close is in the top 10% of the day's range
        # 3. Volume > Average
        
        day_range = latest['high'] - latest['low']
        if day_range > 0:
            strong_close_ratio = (latest['close'] - latest['low']) / day_range
            is_strong_close = strong_close_ratio >= BSJP_CLOSE_THRESHOLD
        else:
            is_strong_close = False # Doji or Flat
            
        is_uptrend_short = latest['close'] > latest['ema_20'] if latest['ema_20'] > 0 else False
        is_volume_ok = latest['volume'] > (latest['vol_avg'] * BSJP_MIN_VOLUME)
        
        is_bsjp = is_green and is_strong_close and is_volume_ok and is_uptrend_short

        # --- Final Decision ---
        # Swing Setup OR Breakout Setup OR BSJP
        is_swing_setup = is_uptrend and momentum_signal and is_volume_spike
        
        is_valid_setup = is_swing_setup or is_volatility_breakout or is_bsjp
        
        reason = []
        if not is_swing_setup: 
            reason.append("Not Swing Setup")
        if not is_volatility_breakout:
            reason.append("Not Volatility Breakout")
        if not is_bsjp:
            reason.append("Not BSJP")

        # Determine Signal Type
        signal_type = "None"
        if is_bsjp:
            signal_type = "BSJP (Overnight Gap)"
            if is_volatility_breakout: signal_type += " + Breakout"
        elif is_volatility_breakout:
            signal_type = "Volatility Breakout"
            if is_swing_setup: signal_type += " + Swing"
        elif is_swing_setup:
            signal_type = "Trend Swing"

        return {
            "valid": is_valid_setup,
            "signal_type": signal_type,
            "symbol": "UNKNOWN", 
            "date": str(latest.name) if isinstance(latest.name, (str, pd.Timestamp)) else "today",
            "close": latest['close'],
            "indicators": {
                "ema_200": latest['ema_200'],
                "rsi": latest['rsi'],
                "atr": latest['atr'],
                "volume_ratio": latest['volume'] / latest['vol_avg'] if latest['vol_avg'] else 0,
                "price_change": price_change_pct
            },
            "signals": {
                "uptrend": bool(is_uptrend),
                "rsi_bounce": bool(rsi_bounce),
                "golden_cross": bool(golden_cross),
                "volume_spike": bool(is_volume_spike),
                "vol_breakout": bool(is_volatility_breakout),
                "bsjp": bool(is_bsjp)
            },
            "reason": "; ".join(reason) if not is_valid_setup else f"Valid: {signal_type}"
        }
