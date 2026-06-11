# simple_async.py
import asyncio
import time

async def task1():
    print("タスク1を開始")
    await asyncio.sleep(1)  # 非同期で1秒待機
    print("タスク1を完了")
    return "タスク1の結果"

async def task2():
    print("タスク2を開始")
    await asyncio.sleep(2)  # 非同期で2秒待機
    print("タスク2を完了")
    return "タスク2の結果"

async def main():
    # 処理開始時間を記録
    start_time = time.time()

    # 同時実行（両方のタスクを同時に開始し、完了を待つ）
    result1, result2 = await asyncio.gather(
        task1(),
        task2()
    )

    # 処理終了時間を記録
    end_time = time.time()

    print(f"結果1: {result1}")
    print(f"結果2: {result2}")
    print(f"合計処理時間: {end_time - start_time:.2f}秒")

# 非同期プログラムの実行
asyncio.run(main())