from fastapi import FastAPI
import aiohttp
import asyncio
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

@app.get("/sequential")
async def call_apis_one_by_one():
    """APIを順番に呼び出す（非効率）"""
    api1 = "https://httpbin.org/delay/1"
    api2 = "https://httpbin.org/delay/2"
    
    start_time = time.time()
    
    # 順番に実行
    data1 = await get_data_from_api(api1)
    data2 = await get_data_from_api(api2)
    
    end_time = time.time()
    
    return {
        "data1": data1,
        "data2": data2,
        "processing_time": f"{end_time - start_time:.2f}秒"
    }

@app.get("/parallel")
async def call_apis_in_parallel():
    """APIを並列に呼び出す（効率的）"""
    api1 = "https://httpbin.org/delay/1"
    api2 = "https://httpbin.org/delay/2"
    
    start_time = time.time()
    
    # 並列実行
    data1, data2 = await asyncio.gather(
        get_data_from_api(api1),
        get_data_from_api(api2)
    )
    
    end_time = time.time()
    
    return {
        "data1": data1,
        "data2": data2,
        "processing_time": f"{end_time - start_time:.2f}秒"
    }