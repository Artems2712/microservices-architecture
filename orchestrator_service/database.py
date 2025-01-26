# orchestrator_service/database.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine("sqlite:///orchestrator_db.sqlite", echo=False)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)
    payload = Column(String, nullable=False)
    published = Column(Boolean, default=False)

# Создадим таблицы
def init_db():
    Base.metadata.create_all(engine)
