# simple_timeout.py
import asyncio

async def long_task():
    print("長い処理を開始...")
    await asyncio.sleep(5)  # 5秒かかる処理をシミュレート
    print("長い処理が完了！")
    return "成功"

async def main():
    try:
        # タイムアウトを3秒に設定し、3秒以内にlong_task()が完了しなければ例外を発生させる
        result = await asyncio.wait_for(long_task(), timeout=3)
        print(f"結果: {result}")
    except asyncio.TimeoutError:
        print("タイムアウトしました！3秒以内に処理が完了しませんでした。")

asyncio.run(main())