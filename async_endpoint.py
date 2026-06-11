import asyncio
import time
import aiohttp

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()

async def async_endpoint(url, num_requests=10):
    async with aiohttp.ClientSession() as session:
        start_time = time.time()

        # 複数のリクエストを同時に送信
        tasks = [fetch(session, url) for _ in range(num_requests)]
        await asyncio.gather(*tasks)

        end_time = time.time()
        return end_time - start_time

async def main():
    # 非同期エンドポイントのテスト
    print("非同期エンドポイントのテスト開始...")
    async_time = await async_endpoint("http://localhost:8000/async", 100)
    print(f"非同期エンドポイント - 100リクエスト: {async_time:.2f}秒")

    # 少し待機して次のテストに備える
    await asyncio.sleep(2)

    # 同期エンドポイントのテスト
    print("同期エンドポイントのテスト開始...")
    sync_time = await async_endpoint("http://localhost:8000/sync", 100)
    print(f"同期エンドポイント - 100リクエスト: {sync_time:.2f}秒")

    print(f"速度差: {sync_time / async_time:.1f}倍")

if __name__ == "__main__":
    asyncio.run(main())