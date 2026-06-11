# hello_async.py
import asyncio

async def hello():
    print("Hello")
    await asyncio.sleep(1)  # 1秒待機（非同期的に待つ）
    print("World")
    return "完了"

# 複数の非同期関数を並行実行
async def main():
    # 3つの hello() を同時に実行し、すべての結果を待つ
    results = await asyncio.gather(
        hello(),
        hello(),
        hello()
    )
    print(f"すべての結果: {results}")

# 非同期関数を実行
asyncio.run(main())