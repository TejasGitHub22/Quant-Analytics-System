import asyncio
import json
import websockets
import pandas as pd
from datetime import datetime

ticks = []

async def connect(symbols):
    streams = "/".join([f"{s}@trade" for s in symbols])
    url = f"wss://fstream.binance.com/stream?streams={streams}"

    async with websockets.connect(url) as ws:
        while True:
            msg = await ws.recv()
            data = json.loads(msg)["data"]

            ticks.append({
                "timestamp": datetime.fromtimestamp(data["T"]/1000),
                "symbol": data["s"].lower(),
                "price": float(data["p"]),
                "qty": float(data["q"])
            })

def start_ws(symbols):
    asyncio.run(connect(symbols))

