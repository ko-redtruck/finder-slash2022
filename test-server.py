#WS server example

import asyncio
import logging
import websockets

logging.basicConfig(level=logging.DEBUG)

async def hello(websocket, path):

    async def send_hello():
        await asyncio.sleep(2)
        await websocket.send("Hello from server!")
        await asyncio.sleep(3)
        await websocket.send("How are you client?")

    task = asyncio.create_task(send_hello())

    await websocket.recv()
    await websocket.recv()

    await task

async def main():
    async with websockets.serve(hello, "localhost", 8765):
        await asyncio.Future()  # run forever

asyncio.run(main())