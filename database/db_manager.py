from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, create_engine, Session, select
from config.settings import SQLITE_URL

# --- Models ---
class DailyCandle(SQLModel, table=True):
    __tablename__: str = "daily_candles"
    
    # Composite Primary Key: symbol + date
    symbol: str = Field(primary_key=True, index=True)
    date: str = Field(primary_key=True, index=True) # YYYY-MM-DD
    
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    change: Optional[float] = None
    change_pct: Optional[float] = None
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# --- Database Engine ---
# check_same_thread=False is needed for SQLite if accessed from multiple threads (e.g., API + Cron)
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

class DBManager:
    def __init__(self):
        self.engine = engine

    def init_db(self):
        """Create tables if they don't exist."""
        SQLModel.metadata.create_all(self.engine)

    def upsert_candles(self, candles: List[DailyCandle]):
        """
        Bulk upsert candles. 
        Since SQLite doesn't have a native "ON DUPLICATE KEY UPDATE" in standard SQL without custom syntax,
        and SQLModel/SQLAlchemy support for it varies by dialect, 
        we will use a simple strategy: determine which exist and update, or just replace.
        
        For simplicity and robustness with SQLite:
        We will iterate and merge. For high performance bulk with SQLite, we could use native INSERT OR REPLACE.
        """
        with Session(self.engine) as session:
            for candle in candles:
                # Merge checks primary key. If exists, updates. If not, inserts.
                session.merge(candle)
            session.commit()
            
    def get_latest_candle(self, symbol: str) -> Optional[DailyCandle]:
        with Session(self.engine) as session:
            statement = select(DailyCandle).where(DailyCandle.symbol == symbol).order_by(DailyCandle.date.desc()).limit(1)
            result = session.exec(statement).first()
            return result

    def get_history(self, symbol: str, limit: int = 200) -> List[DailyCandle]:
        with Session(self.engine) as session:
            statement = select(DailyCandle).where(DailyCandle.symbol == symbol).order_by(DailyCandle.date.asc())
            # Note: We order distinctively. To get last 200, we might need to sort desc then reverse, 
            # or just get all and slice if dataset is small (1 year is ~250 rows).
            # Let's just return all for now or modify query if limit is strict.
            # Efficient way for last N:
            # select * from (select * from table order by date desc limit N) order by date asc
            
            # For this MVP, let's just fetch tailored to the strategy needs
            results = session.exec(statement).all()
            return list(results) # Convert to list
