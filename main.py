from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
from jose import jwt
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db_setup import get_db
from models import UserDb, MessageDb
import os
import asyncio
import requests
import time

app = FastAPI()

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # すべてのオリジンを許可（本番環境ではより制限的にすべき）
    allow_credentials=True,
    allow_methods=["*"],  # すべてのメソッドを許可
    allow_headers=["*"],  # すべてのヘッダーを許可
)

# 静的ファイル（HTML, JavaScript, CSS）を提供するための設定
app.mount("/static", StaticFiles(directory="static"), name="static")

# ルートパスへのアクセスで index.html を返す
@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

# データモデル
class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr

class User(BaseModel):
    username: str
    email: EmailStr

# JWT 設定
SECRET_KEY = "YOUR_SECRET_KEY"  # 秘密のカギ (実際はもっと安全な場所に保管)
ALGORITHM = "HS256"  # 署名アルゴリズム
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # トークンの有効期限 (分)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
AI_USERNAME = "AI Assistant"

async def generate_ai_response(message_text: str) -> str:
    if not GEMINI_API_KEY:
        return "APIキーが設定されていません。"

    def call_gemini():
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": GEMINI_API_KEY
        }

        payload = {
            "contents": [{
                "parts": [{
                    "text": message_text
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.9,
                "maxOutputTokens": 1000,
            }
        }

        for attempt in range(3):
 
            r = requests.post(
                GEMINI_API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )

            if r.status_code == 200:
                result = r.json()
                return result["candidates"][0]["content"]["parts"][0]["text"]

            if r.status_code == 503:
                print("503内容:", r.text)
                time.sleep(2)
                continue

            return f"AI応答の生成に失敗しました。\nステータスコード: {r.status_code}\n内容: {r.text}"

        return "AIサーバーが混雑しています。少し待ってからもう一度送信してください。"

    try:
        result = await asyncio.to_thread(call_gemini)
        return result
    except requests.exceptions.Timeout:
        return "AIの応答が時間内に返ってきませんでした。少し待ってから再送信してください。"
    except requests.exceptions.RequestException as e:
        return f"AI通信エラーが発生しました: {repr(e)}"
    except Exception as e:
        return f"AI処理中にエラーが発生しました: {repr(e)}"

# パスワードをハッシュ化 (簡易版。実際はbcryptなどを使う)
def fake_hash_password(password: str):
    return "hashed_" + password

# パスワードをチェック (簡易版)
def fake_verify_password(plain_password: str, hashed_password: str):
    return hashed_password == "hashed_" + plain_password

# JWT トークンを作成する関数
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})  # 有効期限をセット
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # JWT作成
    return encoded_jwt

# WebSocket接続を管理するクラス
class WebSocketManager:
    def __init__(self):
        self.active_connections: list[tuple[str, WebSocket]] = []

    async def connect(self, websocket: WebSocket, username: str):
        self.active_connections.append((username, websocket))
        await self.broadcast_json({
            "type": "system",
            "content": f"User {username} joined the chat",
            "timestamp": datetime.now().isoformat()
        })

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [
            (username, ws)
            for username, ws in self.active_connections
            if ws != websocket
        ]

    async def broadcast_json(self, data: dict):
        json_str = json.dumps(data)
        disconnected = []

        for username, connection in self.active_connections:
            try:
                await connection.send_text(json_str)
            except RuntimeError:
                disconnected.append(connection)
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)

manager = WebSocketManager()

# ユーザー登録 API
@app.post("/user", response_model=User)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # 同じユーザー名が既に登録されていないか確認
    result = await db.execute(
        select(UserDb).filter(UserDb.username == user.username)
    )
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # パスワードをハッシュ化
    hashed_password = fake_hash_password(user.password)
    
    # ユーザー情報をデータベースに保存
    user_db = UserDb(
        username=user.username,
        hashed_password=hashed_password,
        email=user.email
    )
    db.add(user_db)
    await db.commit()
    
    return {"username": user_db.username, "email": user_db.email}

# WebSocketエンドポイント (認証あり)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        # 最初のメッセージは認証情報
        auth_data = await websocket.receive_json()
        username = auth_data.get("username")
        password = auth_data.get("password")

        # 認証チェック - データベースから確認
        async for db in get_db():
            result = await db.execute(
                select(UserDb).filter(UserDb.username == username)
            )
            user = result.scalars().first()
            break  # 最初の結果だけ使用

        if not user:
            await websocket.send_json({"error": "Authentication failed: User not found"})
            await websocket.close()
            return

        if not fake_verify_password(password, user.hashed_password):
            await websocket.send_json({"error": "Authentication failed: Invalid password"})
            await websocket.close()
            return

        # 認証成功
        token = create_access_token(data={"sub": username})
        await websocket.send_json({"token": token, "message": "Authentication successful"})

        # WebSocket接続を管理クラスに登録
        await manager.connect(websocket, username)

        # メッセージの受信ループ
        while True:
            data = await websocket.receive_text()

            is_ai_request = data.lower().startswith("@ai")
       
            if is_ai_request:
                prompt = data[3:].strip()
                display_data = data
            else:
                display_data = data

            # ユーザーメッセージをDB保存
            async for db in get_db():
                message_db = MessageDb(
                    username=username,
                    content=data
                )
                db.add(message_db)
                await db.commit()
                break

            # @AIなら自分だけ、普通なら全員に表示
            user_message = {
                "type": "message",
                "username": username,
                "content": display_data,
                "timestamp": datetime.now().isoformat()
            }

            if is_ai_request:
                await websocket.send_json(user_message)
            else:
                await manager.broadcast_json(user_message)

            # @AI のときだけAIを呼ぶ
            if is_ai_request:

                print("AI呼び出し前:", prompt)
                ai_response = await generate_ai_response(prompt)
                print("AI呼び出し後:", ai_response)

                async for db in get_db():
                    ai_message_db = MessageDb(
                        username=AI_USERNAME,
                        content=ai_response
                    )
                    db.add(ai_message_db)
                    await db.commit()
                    break

                # AI返答も自分だけに表示
                await websocket.send_json({
                    "type": "message",
                    "username": AI_USERNAME,
                    "content": ai_response,
                    "timestamp": datetime.now().isoformat(),
                    "is_ai": True
                })
    except WebSocketDisconnect:
        if 'username' in locals():
            manager.disconnect(websocket)
            await manager.broadcast_json({
                "type": "system",
                "content": f"User {username} left the chat",
                "timestamp": datetime.now().isoformat()
            })