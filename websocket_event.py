import json

class EVENTS:
    MOVIES = 'movies'
    RESULT = 'result'
    UPVOTE = 'upvote'
    DOWNVOTE = 'downvote'


async def send_event_message(websocket, event, data):
    #print(f'Sending event: {event}')
    await websocket.send(event_message_to_json(event, data)) 

def event_message_to_json(event, data):
    return json.dumps({
        'event': event,
        'data': data
    })

async def receive_event_message(websocket):
    message = await websocket.recv()
    #print(f"Receiving: {message}")
    return json.loads(message)
   
async def wait_for_event_message(websocket, event):
    while True:
        message = await receive_event_message(websocket)
        if message['event'] == event:
            return message

