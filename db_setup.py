# db_setup.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# データベースURL
DATABASE_URL = "sqlite+aiosqlite:///./chat_app.db"

# エンジン作成
engine = create_async_engine(DATABASE_URL, echo=True)

# セッションの作成
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# モデル定義の基底クラス
Base = declarative_base()

# データベースセッションを取得する関数
async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()