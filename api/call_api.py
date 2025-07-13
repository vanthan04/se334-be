from flask import request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import pandas as pd
import requests
import asyncio
import httpx
from .config import Config
import time

def split_batches(data, batch_size):
    for i in range(0, len(data), batch_size):
        yield data[i:i+batch_size]

# ---------------------------
# HÀM ASYNC
# ---------------------------
async def predict_batch(batch, client):
    try:
        resp = await client.post(
            Config.base_url + "/predict",
            json={"sentences": batch},
            timeout=30
        )

        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("application/json"):
            data = resp.json()
            return data.get("results", [])
        else:
            print(f"API lỗi status {resp.status_code}, body: {resp.text}")
            return []

    except Exception as e:
        print("Lỗi gọi API async:", e)
        return []


async def async_predict(sentences):
    batches = list(split_batches(sentences, 100))

    async with httpx.AsyncClient() as client:
        start = time.time()
        tasks = [predict_batch(b, client) for b in batches]
        results = await asyncio.gather(*tasks)
        end = time.time()
        print(f"⏱ Tổng thời gian chạy các API song song (async): {end - start:.2f} giây")

    # gộp kết quả
    merged = []
    for r in results:
        merged.extend(r)
    return merged

# ---------------------------
# HÀM SYNC
# ---------------------------
def sync_predict(sentences):
    batches = list(split_batches(sentences, 100))

    start = time.time()
    merged = []
    for batch in batches:
        try:
            resp = requests.post(
                f"{Config.base_url}/predict",
                json={"sentences": batch},
                timeout=30
            )
            predictions = resp.json().get("results", [])
            merged.extend(predictions)
        except Exception as e:
            print("Lỗi gọi API sync:", e)

    end = time.time()
    print(f"⏱ Tổng thời gian chạy các API tuần tự (sync): {end - start:.2f} giây")
    return merged
