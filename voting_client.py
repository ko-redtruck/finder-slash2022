#!/usr/bin/env python


import asyncio

import websockets
from websocket_event import *

async def hello():

    uri = "ws://localhost:8001/1"

    async with websockets.connect(uri) as websocket:
        message = await receive_event_message(websocket)

        for movie in message['data']:
            print(movie['title'])
            vote = input('Your vote? (+/-)')
            if vote == '+':
                await send_event_message(websocket, EVENTS.UPVOTE, movie)
            elif vote == '-':
                await send_event_message(websocket, EVENTS.DOWNVOTE, movie)

if __name__ == "__main__":

    asyncio.run(hello())