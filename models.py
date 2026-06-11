# models.py
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from db_setup import Base

# ユーザーモデル (データベースの users テーブルに対応)
class UserDb(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)

class MessageDb(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    content = Column(String)
    created_at = Column(DateTime, default=datetime.now)
