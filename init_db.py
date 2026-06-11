# init_db.py
import asyncio
from db_setup import engine, Base
from models import UserDb

async def init_db():
    async with engine.begin() as conn:
        # テーブルをすべて削除（開発時のリセット用）
        # await conn.run_sync(Base.metadata.drop_all)
        
        # テーブルを作成
        await conn.run_sync(Base.metadata.create_all)
    
    print("データベースの初期化が完了しました！")

if __name__ == "__main__":
    asyncio.run(init_db())