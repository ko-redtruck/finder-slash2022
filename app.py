#!/usr/bin/env python

import asyncio
import json
import websockets

PORT = 8001

USERS = set()


async def handler(websocket):
    global USERS
    try:
        # Register user
        USERS.add(websocket)
        print(f"Connection received from {websocket}")
  
        while True:
            try:
                response = await websocket.recv()
            except websockets.ConnectionClosed:
                print(f"Terminated connection with client: {websocket}")
                break

            print(f"< {response}")
            greeting = f"Hello {response}!"

            await websocket.send(greeting)
            print(f"> {greeting}")
    finally:
        # Unregister user
        USERS.remove(websocket)
        print(f"Currently there are {len(USERS)} connected")


async def main():
    async with websockets.serve(handler, "", PORT):
        print(f"Running websocket on port {PORT}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
