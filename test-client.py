#!/usr/bin/env python

# WS client example

import asyncio
import logging
import websockets

logging.basicConfig(level=logging.DEBUG)

async def hello():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:

        async def send_hello():
            await websocket.send("Hello from client!")
            await websocket.send("How are you server?")

        await websocket.recv()
        task = asyncio.create_task(send_hello())

        
        await websocket.recv()

        await task

asyncio.run(hello())