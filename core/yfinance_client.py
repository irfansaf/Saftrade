import yfinance as yf
import pandas as pd
import logging
from typing import List, Optional
from database.db_manager import DailyCandle
from datetime import datetime

logger = logging.getLogger(__name__)

class YFinanceClient:
    def get_historical_data(self, symbol: str, from_date: str = None, to_date: str = None) -> List[DailyCandle]:
        """
        Fetch historical data from Yahoo Finance.
        Handles symbol conversion (e.g., BBCA -> BBCA.JK).
        """
        # Convert symbol to YF format (add .JK for Indonesia)
        yf_symbol = f"{symbol}.JK"
        
        logger.info(f"Fetching YFinance data for {yf_symbol}...")
        
        try:
            # Fetch data
            # YF expects YYYY-MM-DD
            df = yf.download(yf_symbol, start=from_date, end=to_date, progress=False)
            
            if df.empty:
                logger.warning(f"No YFinance data found for {yf_symbol}")
                return []
            
            # Fix: Handle MultiIndex columns (Common in new yfinance)
            # e.g. columns might be ('Close', 'SCMA.JK')
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            
            candles = []
            # YFinance returns DateTime index. Reset it to access Date column.
            df = df.reset_index()
            
            for _, row in df.iterrows():
                try:
                    # YFinance columns are MultiIndex if multiple tickers, but singular here.
                    # Standard columns: Date, Open, High, Low, Close, Adj Close, Volume
                    # We use 'Close' or 'Adj Close'? Standard is usually Adj Close for backtesting, 
                    # but GoAPI might return raw close. Let's stick to 'Close' for consistency with signal detection 
                    # unless user specifies. 'Close' is raw.
                    
                    # Handle potential header issues (sometimes lowercase)
                    date_val = row['Date'].strftime("%Y-%m-%d")
                    
                    # Extract scalar values safely
                    open_val = float(row['Open'].iloc[0]) if isinstance(row['Open'], pd.Series) else float(row['Open'])
                    high_val = float(row['High'].iloc[0]) if isinstance(row['High'], pd.Series) else float(row['High'])
                    low_val = float(row['Low'].iloc[0]) if isinstance(row['Low'], pd.Series) else float(row['Low'])
                    close_val = float(row['Close'].iloc[0]) if isinstance(row['Close'], pd.Series) else float(row['Close'])
                    vol_val = int(row['Volume'].iloc[0]) if isinstance(row['Volume'], pd.Series) else int(row['Volume'])
                    
                    candles.append(DailyCandle(
                        symbol=symbol, # Store as original symbol (BBCA) not BBCA.JK
                        date=date_val,
                        open=open_val,
                        high=high_val,
                        low=low_val,
                        close=close_val,
                        volume=vol_val
                    ))
                except Exception as row_err:
                    # logger.debug(f"Skipping row due to error: {row_err}")
                    continue
                    
            logger.info(f"Retrieved {len(candles)} candles from YFinance")
            return candles
            
        except Exception as e:
            logger.error(f"YFinance Error for {symbol}: {e}")
            return []
