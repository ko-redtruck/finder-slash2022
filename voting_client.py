#!/usr/bin/env python


import asyncio
import sys
import websockets
from websocket_event import *
import asyncio as aio

from concurrent.futures import ThreadPoolExecutor

async def ainput(prompt: str = "") -> str:
    with ThreadPoolExecutor(1, "AsyncInput") as executor:
        return await asyncio.get_event_loop().run_in_executor(executor, input, prompt)

async def vote(websocket, movies):
    for movie in movies:
        print(movie['title'])
        vote = await ainput('Your vote? (+/-)')
        if vote == '+':
            await send_event_message(websocket, EVENTS.UPVOTE, movie)
        elif vote == '-':
            await send_event_message(websocket, EVENTS.DOWNVOTE, movie)

async def vote_on(websocket):
    message = await wait_for_event_message(websocket, EVENTS.MOVIES)
    task = asyncio.create_task(vote(websocket, message['data']))
    await wait_for_result(websocket)
    await task
    

async def wait_for_result(websocket):
    print('waiting')
    message = await wait_for_event_message(websocket, EVENTS.RESULT)
    print('FINISHED VOTING!')
    print(f'Winning movie: {message["data"]}')

async def finder_voting_and_result(websocket):
    message = await wait_for_event_message(websocket, EVENTS.MOVIES)

    #vote_on(websocket, message['data'])
    #await wait_for_result(websocket)
    #await asyncio.gather(wait_for_result(websocket), vote_on(websocket, message['data']))

async def result(websocket):
    message = await wait_for_event_message(websocket, EVENTS.RESULT)
    print('FINISHED VOTING!')
    print(f'Winning movie: {message["data"]}')

async def hello():

    uri = "ws://localhost:8001/2"

    async with websockets.connect(uri) as websocket:
        #asyncio.create_task(wait_for_result(websocket))
        await vote_on(websocket)
if __name__ == "__main__":
    asyncio.run(hello())