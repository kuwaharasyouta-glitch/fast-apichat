from fastapi import FastAPI
import asyncio
import time

app = FastAPI()

# メッセージを保存するための簡易的なリスト
messages = []

# メッセージ保存処理（データベース操作をシミュレート）
async def save_message(text, username):
    print(f"{username}からのメッセージを保存中...")
    # データベース操作の待ち時間をシミュレート
    await asyncio.sleep(1)
    
    # メッセージを保存
    message = {
        "id": len(messages) + 1,
        "text": text,
        "username": username,
        "time": time.strftime("%H:%M:%S")
    }
    messages.append(message)
    print("メッセージを保存しました！")
    return message

@app.post("/send")
async def send_message(text: str, username: str):
    """メッセージを送信する"""
    start_time = time.time()
    
    # メッセージを保存
    message = await save_message(text, username)
    
    end_time = time.time()
    
    return {
        "message": message,
        "processing_time": f"{end_time - start_time:.2f}秒"
    }

@app.get("/messages")
async def get_messages():
    """すべてのメッセージを取得する"""
    await asyncio.sleep(0.5)  # データベース読み込みをシミュレート
    return {"messages": messages}