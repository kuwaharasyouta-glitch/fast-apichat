# simple_sync.py
import time

def task1():
    print("タスク1を開始")
    time.sleep(1)  # 1秒待機
    print("タスク1を完了")
    return "タスク1の結果"

def task2():
    print("タスク2を開始")
    time.sleep(2)  # 2秒待機
    print("タスク2を完了")
    return "タスク2の結果"

# 処理開始時間を記録
start_time = time.time()

# 実行
result1 = task1()  # 1秒かかる
result2 = task2()  # 2秒かかる

# 処理終了時間を記録
end_time = time.time()

print(f"結果1: {result1}")
print(f"結果2: {result2}")
print(f"合計処理時間: {end_time - start_time:.2f}秒")
