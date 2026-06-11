from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/async")
async def root():
    # 非同期エンドポイント
    await asyncio.sleep(1)  # 何らかの処理を待つシミュレーション
    return {"message": "こんにちは、非同期の世界！"}

@app.get("/sync")
def sync_root():
    # 同期エンドポイント
    import time
    time.sleep(1)  # 何らかの処理を待つシミュレーション
    return {"message": "こんにちは、同期の世界！"}