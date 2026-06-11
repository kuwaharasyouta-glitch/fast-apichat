from fastapi import FastAPI
import aiohttp
import time

app = FastAPI()

async def get_data_from_api(url: str):
    print(f"APIリクエスト開始: {url}")
    start_time = time.time()

    proxy_url = "http://lab-12:Slpl-201@proxy.doshisha.ac.jp:8080"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxy_url) as response:
            data = await response.json()
            
    end_time = time.time()
    print(f"APIリクエスト完了: {url} ({end_time - start_time:.2f}秒)")
    return data

@app.get("/call-api")
async def call_api():
    # JSONPlaceholderの無料APIを使用
    api_url = "https://catfact.ninja/fact"
    
    start_time = time.time()
    data = await get_data_from_api(api_url)
    end_time = time.time()
    
    return {
        "result": data,
        "processing_time": f"{end_time - start_time:.2f}秒"
    }