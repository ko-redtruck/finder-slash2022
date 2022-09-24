#!/usr/bin/env python


import asyncio

import websockets


async def hello():

    uri = "ws://localhost:8001/1"

    async with websockets.connect(uri) as websocket:
        response = await websocket.recv()

        print(f"Initial response: {response}")
        while True:
            message = input("Send message:")
            await websocket.send(message)


            response = await websocket.recv()

            print(f"Response: {response}")


if __name__ == "__main__":

    asyncio.run(hello())