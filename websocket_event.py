import json

class EVENTS:
    MOVIES = 'movies'
    UPVOTE = 'upvote'
    DOWNVOTE = 'downvote'


async def send_event_message(websocket, event, data):
    print(f'Sending event: {event}')
    await websocket.send(json.dumps({
        'event': event,
        'data': data
    })) 

async def receive_event_message(websocket):
    message = await websocket.recv()
    return json.loads(message)
   