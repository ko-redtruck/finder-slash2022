#!/usr/bin/env python


import asyncio

import websockets


async def hello():

    uri = "ws://localhost:8001"

    async with websockets.connect(uri) as websocket:
        while True:
            message = input("Send message:")
            await websocket.send(message)


            response = await websocket.recv()

            print(f"Response: {response}")


if __name__ == "__main__":

    asyncio.run(hello())