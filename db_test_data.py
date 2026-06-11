import asyncio
from sqlalchemy import select
from db_setup import engine, async_session_maker
from models import UserDb

# パスワードハッシュ化のための関数
def fake_hash_password(password: str):
    return "hashed_" + password

async def create_test_users():
    async with async_session_maker() as session:
        # 作成するテストユーザー
        test_users = [
            {"username": "alice", "email": "alice@example.com", "password": "password123"},
            {"username": "bob", "email": "bob@example.com", "password": "password123"}
        ]

        for user_data in test_users:
            # ユーザーが既に存在するか確認
            result = await session.execute(
                select(UserDb).filter(UserDb.username == user_data["username"])
            )
            existing_user = result.scalars().first()

            if existing_user:
                print(f"ユーザー {user_data['username']} は既に存在します")
            else:
                # 新しいユーザーを作成
                new_user = UserDb(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=fake_hash_password(user_data["password"])
                )
                session.add(new_user)
                await session.commit()
                print(f"ユーザー {user_data['username']} を作成しました")

        print("テストユーザーの作成が完了しました")

if __name__ == "__main__":
    asyncio.run(create_test_users())