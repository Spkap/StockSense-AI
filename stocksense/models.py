from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class AnalysisCache(Base):
    __tablename__ = 'analysis_cache'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False)
    analysis_summary = Column(Text)
    sentiment_report = Column(Text)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_ticker_timestamp', 'ticker', 'timestamp'),
    )