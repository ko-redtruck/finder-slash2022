#!/usr/bin/env python

import asyncio
import json
import websockets
from tmdbv3api import TMDb
from tmdbv3api import Movie

tmdb = TMDb()
tmdb.language = 'en'
tmdb.debug = True

class EVENTS:
    MOVIES = 'movies'
    UPVOTE = 'upvote'
    DOWNVOTE = 'downvote'

PORT = 8001

USERS = set()
SESSIONS = {1:{}}

async def send_event_message(websocket, event, data):
    websocket.send(json.dumps({
        'event': event,
        'data': data
    })) 

async def receive_event_message(websocket):
    try:
        message = await websocket.recv()
        return json.loads(message)
    except websockets.ConnectionClosed:
        print(f"Terminated connection with client: {websocket}")
        raise websockets.ConnectionClosed

def generate_movie_genres():
    MOVIE_GENRES_JSON = """
    {"genres":[{"id":28,"name":"Action"},{"id":12,"name":"Adventure"},{"id":16,"name":"Animation"},{"id":35,"name":"Comedy"},{"id":80,"name":"Crime"},{"id":99,"name":"Documentary"},{"id":18,"name":"Drama"},{"id":10751,"name":"Family"},{"id":14,"name":"Fantasy"},{"id":36,"name":"History"},{"id":27,"name":"Horror"},{"id":10402,"name":"Music"},{"id":9648,"name":"Mystery"},{"id":10749,"name":"Romance"},{"id":878,"name":"Science Fiction"},{"id":10770,"name":"TV Movie"},{"id":53,"name":"Thriller"},{"id":10752,"name":"War"},{"id":37,"name":"Western"}]}
    """
    MOVIE_GENRES_LIST = json.loads(MOVIE_GENRES_JSON)
    genres = {}
    for genre in MOVIE_GENRES_LIST["genres"]:
        genres[genre['id']] = genre['name']
    return genres

MOVIE_GENRES = generate_movie_genres()
print(MOVIE_GENRES)


def movie_to_movie_data(movie_data):
    try:
        movie = {
            'title' : movie_data.title,
            'poster': movie_data.poster_path,
            'release_date': movie_data.release_date,
            'overview': movie_data.overview,
            'genres': [MOVIE_GENRES[genre_id] for genre_id in movie_data.genre_ids],
            'genre_ids' : movie_data.genre_ids
        }
        return movie
    except:
        return None
def movies_to_movie_data(movies):
    return list(filter(None,[movie_to_movie_data(movie) for movie in movies]))

def search_for_movie(movie_name : str):
    movie = Movie()
    search_results = movie.search(movie_name)
    return list(filter(None,[movie_to_movie_data(movie_data) for movie_data in search_results]))

async def validate_session_id(websocket, path):
    session_id = int(path.replace('/',''))
    if session_id not in SESSIONS:
        print(f'Session id: {session_id} not found')
        await websocket.close()
        raise Exception(f'Session id: {session_id} not found')

def register_user(websocket, path):
    # Register user
    USERS.add(websocket)
    print(f"Connection received from {websocket} at path: {path}")

def get_most_popular_movies():
    movie = Movie()
    movies = movie.popular()
    return movies_to_movie_data(movies)

async def handler(websocket, path):
    try:
        register_user(websocket, path)
        await validate_session_id(websocket, path)

        await send_event_message(websocket, EVENTS.MOVIES, get_most_popular_movies())
        while True:
           

            
    except:
        await websocket.close()
    finally:
        # Unregister user
        USERS.remove(websocket)
        print(f"Currently there are {len(USERS)} connected")

"""
async def consumer_handler(websocket, path):
    pass

async def producer_handler(websocket, path):
    pass

async def handler(websocket, path):
    await asyncio.gather(
        consumer_handler(websocket, path),
        producer_handler(websocket),
    )
"""
async def main():
    async with websockets.serve(handler, "", PORT):
        print(f"Running websocket on port {PORT}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
