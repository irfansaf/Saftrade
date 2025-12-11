import logging
from typing import List
from core.goapi_client import GoApiClient
from core.yfinance_client import YFinanceClient
from database.db_manager import DailyCandle

logger = logging.getLogger(__name__)

class DataProvider:
    def __init__(self):
        from config.settings import GOAPI_KEY # Import here to check
        self.goapi = GoApiClient()
        self.yfinance = YFinanceClient()
        
        # Circuit Breaker State
        # If no key, trip immediately
        self.use_fallback_mode = False if GOAPI_KEY else True
        
        if self.use_fallback_mode:
            logger.warning("GOAPI_KEY missing. Initializing DataProvider in FALLBACK MODE (YFinance Only).")
    
    def get_historical_data(self, symbol: str, from_date: str = None, to_date: str = None) -> List[DailyCandle]:
        """
        Try GoAPI first. If it fails (returns empty or error logs inside client), switch to YFinance.
        If Circuit Breaker is tripped (use_fallback_mode = True), skip GoAPI entirely.
        """
        # 1. Check Circuit Breaker
        if self.use_fallback_mode:
            logger.info(f"Circuit Breaker Active: Skipping GoAPI for {symbol}, using YFinance.")
            return self.yfinance.get_historical_data(symbol, from_date, to_date)

        # 2. Try GoAPI
        try:
            logger.info(f"Attempting fetch from GoAPI for {symbol}...")
            data = self.goapi.get_historical_data(symbol, from_date, to_date)
            
            if data:
                return data
            else:
                logger.warning(f"GoAPI returned no data for {symbol}. Switching to Fallback.")
                # Optional: Decide if empty data triggers circuit breaker? 
                # Let's say NO for specific stock missing, YES for API error.
                # But here we are in the 'data is None' block which might vary.
                # safely just fall through for now. 
        except Exception as e:
            logger.error(f"GoAPI Exception: {e}. TRIPPING CIRCUIT BREAKER.")
            self.use_fallback_mode = True # Trip the break
            
        # 3. Fallback to YFinance
        logger.info(f"FALLBACK: Fetching from YFinance for {symbol}...")
        return self.yfinance.get_historical_data(symbol, from_date, to_date)
