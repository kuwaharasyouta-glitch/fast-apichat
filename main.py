from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import Dict
from datetime import datetime, timedelta, timezone
from jose import jwt
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db_setup import get_db
from models import UserDb, MessageDb

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

# ユーザー情報 (パソコンのメモリで管理。実際はデータベースに保存)
users_db = {}  # {username: {"password": "hashed_password", "email": "...", ...}}

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
        for username, connection in self.active_connections:
            await connection.send_text(json_str)

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

            async for db in get_db():
                message_db = MessageDb(
                    username=username,
                    content=data
                )
                db.add(message_db)
                await db.commit()
                break

            await manager.broadcast_json({
                "type": "message",
                "username": username,
                "content": data,
                "timestamp": datetime.now().isoformat()
            })

    except WebSocketDisconnect:
        if 'username' in locals():
            manager.disconnect(websocket)
            await manager.broadcast_json({
                "type": "system",
                "content": f"User {username} left the chat",
                "timestamp": datetime.now().isoformat()
            })