# tests/test_main.py
from fastapi.testclient import TestClient
from main import app
import time
import json
import pytest

# TestClientを使ってアプリをテスト用に準備する
client = TestClient(app)

# 1. ユーザー登録のテスト
def test_register_user():
    # テスト用ユーザーデータ - タイムスタンプで一意にする
    user_data = {
        "username": f"testuser_{int(time.time())}",
        "password": "password123",
        "email": f"test_{int(time.time())}@example.com"
    }

    # ユーザー登録APIを呼び出す
    response = client.post("/user", json=user_data)

    # 登録成功を確認
    assert response.status_code == 200
    # レスポンスのJSONデータを取得
    data = response.json()
    # ユーザー名とメールアドレスが正しいことを確認
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    # パスワードはレスポンスに含まれないことを確認
    assert "password" not in data

# 2. 存在するユーザー名での再登録が失敗するテスト
def test_register_duplicate_user():
    # テスト用ユーザーデータ
    username = f"duplicate_user_{int(time.time())}"
    user_data = {
        "username": username,
        "password": "password123",
        "email": f"duplicate_{int(time.time())}@example.com"
    }

    # 最初の登録（成功するはず）
    response1 = client.post("/user", json=user_data)
    assert response1.status_code == 200

    # 同じユーザー名で2回目の登録（失敗するはず）
    response2 = client.post("/user", json=user_data)
    assert response2.status_code == 400
    assert "already registered" in response2.json()["detail"]

# 3. WebSocketのシンプルな接続テスト
def test_websocket_connection():
    # まずユーザーを登録
    username = f"ws_user_{int(time.time())}"
    password = "password123"
    email = f"ws_{int(time.time())}@example.com"

    client.post("/user", json={
        "username": username,
        "password": password,
        "email": email
    })

    # WebSocketクライアントを使用して接続
    with client.websocket_connect("/ws") as websocket:
        # 認証情報を送信
        websocket.send_json({"username": username, "password": password})

        # 認証レスポンスを受信
        auth_response = websocket.receive_json()
        assert "token" in auth_response
        assert auth_response["message"] == "Authentication successful"

        # システムメッセージを受信（接続時に自動送信される）
        system_msg = websocket.receive_text()
        sys_data = json.loads(system_msg)
        assert sys_data["type"] == "system"
        assert username in sys_data["content"]
        assert "joined the chat" in sys_data["content"]

        # テストメッセージを送信
        test_message = "Hello, WebSocket!"
        websocket.send_text(test_message)

        # ブロードキャストされたメッセージを受信
        received_data = websocket.receive_text()
        data = json.loads(received_data)

        # メッセージの内容を確認
        assert data["type"] == "message"  # 'system'ではなく'message'
        assert data["username"] == username
        assert data["content"] == test_message
        assert "timestamp" in data

# 4. 不正な認証情報でのWebSocket接続テスト
def test_websocket_invalid_authentication():
    # WebSocketクライアントを使用して接続
    with client.websocket_connect("/ws") as websocket:
        # 存在しないユーザー名で認証
        websocket.send_json({"username": "nonexistent_user", "password": "wrong_password"})

        # エラーレスポンスを受信（接続は閉じられないが、エラーメッセージが返される）
        response = websocket.receive_json()
        assert "error" in response
        assert "Authentication failed" in response["error"]