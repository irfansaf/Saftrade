import logging
import sys
from config.watchlist import WATCHLIST
from database.db_manager import DBManager
from core.strategy import TechnicalAnalyzer
from core.ai_engine import AIEngine
from core.notifier import TelegramNotifier
import pandas as pd

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Saftrade - Full Pipeline")
    
    # 1. Initialize Database
    try:
        db = DBManager()
        db.init_db()
        logger.info("Database initialized.")
    except Exception as e:
        logger.critical(f"Database init failed: {e}")
        return

    # 2. Select Targets
    target_stocks = WATCHLIST[:5] # Process top 5 for demo
    logger.info(f"Processing stocks: {target_stocks}")

    # 3. Initialize Components
    # Use DataProvider for Redundancy (GoAPI -> YFinance)
    from core.data_provider import DataProvider
    client = DataProvider()
    
    analyzer = TechnicalAnalyzer()
    ai = AIEngine()
    notifier = TelegramNotifier()

    # 4. Process Loop
    for ticker in target_stocks:
        logger.info(f"--- Processing {ticker} ---")
        
        # A. Fetch/Update Data
        # For MVP, we need history to calculate ema200. 
        # In a real daily run, we'd have history in DB and just append today.
        # Here we'll fetch full history to ensure we can run indicators.
        logger.info("Fetching history...")
        
        # Calculate 1 year ago for seeding
        from datetime import datetime, timedelta
        # to_date needs to be tomorrow because yfinance 'end' is exclusive
        to_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        history = client.get_historical_data(ticker, from_date=from_date, to_date=to_date)
        
        if not history:
            logger.warning(f"No history found for {ticker}. Skipping.")
            continue
            
        # Save to DB (optional, but good practice)
        db.upsert_candles(history)
        
        # Convert to DataFrame
        import pandas as pd
        data_dicts = [h.model_dump() for h in history]
        df = pd.DataFrame(data_dicts)
        if df.empty: 
            continue
            
        # Ensure Types and Sort
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # B. Technical Analysis
        logger.info("Running Technical Analysis...")
        tech_result = analyzer.analyze(df)
        
        if not tech_result['valid']:
            logger.info(f"Result: {tech_result['reason']}")
            continue
            
        logger.info(f"[SIGNAL DETECTED] {tech_result['signals']}")
        
        # C. AI Validation
        logger.info("Requesting AI Validation...")
        ai_result = ai.analyze_signal(ticker, tech_result)
        
        logger.info(f"[AI VERDICT] {ai_result.get('valid')} - {ai_result.get('analysis')}")
        
        if ai_result.get('valid'):
            trade_plan = ai_result.get('trade_plan', {})
            logger.info(f"[TRADE PLAN] {trade_plan}")
            
            # D. Send Notification
            logger.info("Sending Telegram Alert...")
            notifier.send_alert(ticker, tech_result, trade_plan, ai_result.get('analysis', 'No analysis provided.'))
            
            # E. Log to CSV (PRD Requirement)
            try:
                import csv
                import os
                
                csv_file = "signals.csv"
                file_exists = os.path.isfile(csv_file)
                
                with open(csv_file, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(["date", "ticker", "close", "signal_type", "ai_valid", "entry", "sl", "tp"])
                    
                    writer.writerow([
                        tech_result['date'],
                        ticker,
                        tech_result['close'],
                        tech_result['signals'], # Might want to clean this up string-wise
                        ai_result.get('valid'),
                        trade_plan.get('entry'),
                        trade_plan.get('stop_loss'),
                        trade_plan.get('take_profit')
                    ])
                logger.info("Signal logged to signals.csv")
            except Exception as e:
                logger.error(f"Failed to log to CSV: {e}")
        else:
            logger.info("AI Rejected the setup.")

    logger.info("Batch Process Complete.")

if __name__ == "__main__":
    main()
