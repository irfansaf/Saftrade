import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from typing import List, Dict, Any, Optional
from config.settings import GOAPI_KEY, API_BASE_URL
from database.db_manager import DailyCandle

# Configure Logging
logger = logging.getLogger(__name__)

class GoApiClient:
    def __init__(self):
        self.api_key = GOAPI_KEY
        self.base_url = API_BASE_URL
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with exponential backoff retry."""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1, # 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def get_bulk_prices(self, symbols: List[str]) -> List[DailyCandle]:
        """
        Fetch latest prices for up to 50 symbols in one request.
        """
        if not symbols:
            return []
            
        # Limit to 50 per batch as per GoAPI Spec
        if len(symbols) > 50:
            logger.warning("Symbol list > 50. Splitting is not implemented in MVP. Truncating to 50.")
            symbols = symbols[:50]
            
        endpoint = f"{self.base_url}/stock/idx/prices"
        symbols_str = ",".join(symbols)
        
        params = {
            "api_key": self.api_key,
            "symbols": symbols_str
        }
        
        try:
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data_json = response.json()
            
            if data_json.get("status") != "success":
                logger.error(f"GoAPI Error: {data_json.get('message')}")
                return []
                
            results = data_json.get("data", [])
            
            candles = []
            for item in results:
                # Map API response to DB Model
                # API format: {'date': '2025-01-01', 'symbol': 'BBCA', 'close': 1000, ...}
                try:
                    candle = DailyCandle(
                        symbol=item['symbol'],
                        date=item['date'],
                        open=float(item['open']),
                        high=float(item['high']),
                        low=float(item['low']),
                        close=float(item['close']),
                        volume=int(item['volume']),
                        change=float(item.get('change', 0)),
                        change_pct=float(item.get('change_pct', 0))
                    )
                    candles.append(candle)
                except KeyError as e:
                    logger.error(f"Missing field in API response for {item.get('symbol', 'UNKNOWN')}: {e}")
                    continue
                    
            return candles

        except requests.exceptions.RequestException as e:
            logger.error(f"API Request Failed: {e}")
            return []

    def get_historical_data(self, symbol: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[DailyCandle]:
        """
        Fetch historical data for a single symbol.
        Used for initial seeding.
        """
        endpoint = f"{self.base_url}/stock/idx/{symbol}/historical"
        params = {"api_key": self.api_key}
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
            
        try:
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data_json = response.json()
             
            if data_json.get("status") != "success":
                logger.error(f"GoAPI History Error for {symbol}: {data_json.get('message')}")
                return []
                
            raw_data = data_json.get("data", [])
            logger.debug(f"Historical Data Type: {type(raw_data)}")
            
            # Defensive handling: API might return list OR dict with 'results'
            if isinstance(raw_data, dict):
                results = raw_data.get("results", [])
            elif isinstance(raw_data, list):
                results = raw_data
            else:
                results = []
            
            candles = []
            for item in results:
                if not isinstance(item, dict):
                    logger.warning(f"Unexpected item type in history: {type(item)} - {item}")
                    continue
                    
                candle = DailyCandle(
                    symbol=symbol, 
                    date=item['date'],
                    open=float(item['open']),
                    high=float(item['high']),
                    low=float(item['low']),
                    close=float(item['close']),
                    volume=int(item['volume'])
                )
                candles.append(candle)
            return candles

        except requests.exceptions.RequestException as e:
            logger.error(f"API History Request Failed for {symbol}: {e}")
            raise # Re-raise for DataProvider to handle (Circuit Breaker)
