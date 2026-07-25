import os
import json
import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class DBAnalysisHistory(Base):
    __tablename__ = 'analysis_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    target = Column(String, nullable=False)
    target_type = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    score_general = Column(Integer, default=100)
    success_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    info_count = Column(Integer, default=0)
    results_json = Column(Text, nullable=False)  # Armazena os checks como JSON

class DBSettings(Base):
    __tablename__ = 'settings'
    
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)

# Configurar Banco de Dados SQLite na pasta de dados do usuário
DB_DIR = os.path.expanduser("~/.mailcerto")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "mailcerto.db")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
