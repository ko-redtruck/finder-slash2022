#!/usr/bin/env python

import asyncio
import websockets
from tmdbv3api import TMDb
from tmdbv3api import Movie
import time
from functools import reduce
from websocket_event import *
import pickle

tmdb = TMDb()
tmdb.language = 'en'
tmdb.debug = True



PORT = 8001

SESSIONS = {}

SESSION_TIMEOUT = 10


def movie_to_movie_data(movie_data):
    try:
        movie = {
            'title' : movie_data.title,
            'poster': 'https://image.tmdb.org/t/p/original' + movie_data.poster_path,
            'release_date': movie_data.release_date,
            'overview': movie_data.overview,
            'genres': [MOVIE_GENRES[genre_id] for genre_id in movie_data.genre_ids],
            'genre_ids' : movie_data.genre_ids,
            'rating': movie_data.vote_average
        }
        return movie
    except:
        return None
def movies_to_movie_data(movies):
    return list(filter(None,[movie_to_movie_data(movie) for movie in movies]))

def generate_movie_list():
    with open('all_movies.obj','rb') as file:
        movies = pickle.load(file)
        return movies_to_movie_data(movies)

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
MOVIE_LIST = generate_movie_list()
print(f'{len(MOVIE_GENRES)} genres and {len(MOVIE_LIST)} movies')





def search_for_movie(movie_name : str):
    movie = Movie()
    search_results = movie.search(movie_name)
    return list(filter(None,[movie_to_movie_data(movie_data) for movie_data in search_results]))

async def validate_session_id(websocket, path):
    session_id = int(path.replace('/',''))
    """
    if session_id not in SESSIONS:
        print(f'Session id: {session_id} not found')
        await websocket.close()
        raise Exception(f'Session id: {session_id} not found')
    """
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {
            'start_time': time.time(),
            'users': set()
        }
    return session_id, SESSIONS[session_id]

def register_user(websocket, path, session):
    # Register user
    session['users'].add(websocket)
    print(f"Connection received from {websocket} at path: {path}")

def get_most_popular_movies():
    movie = Movie()
    movies = movie.popular()
    return movies_to_movie_data(movies)

def handle_vote_event(message, store, vote_value):
    genre_ids = message["data"]["genre_ids"]
    print(genre_ids)
    for id in genre_ids:
        try:
            store[id] += vote_value
        except:
            store[id] = vote_value

def genre_match_score(movie, votes, total_votes) -> int:
    score = 0
    genres = movie['genre_ids']
    if len(genres) == 0:
        return 0
    for genre in genres:
        if genre in votes:
            score += votes[genre] / total_votes
    score *=  1 / len(genres)
    int_score = round(score * 100)
    return int_score

def handle_upvote_event(message, store):
    handle_vote_event(message, store, 1)
    
def handle_downvote_event(message, store):
    handle_vote_event(message, store, -1)

async def end_session_on_timeout(session_id, session, timeout):
    await asyncio.sleep(timeout)
    await end_finder_session(session_id, session)

def find_winning_movie(session):
    movie = Movie()
    movies_data = MOVIE_LIST
    for movie in movies_data:
        movie['score'] = genre_match_score(movie, session['votes'], session['total_votes'])

    best_score = max(movie['score'] for movie in movies_data)
    best_movies = list(filter(lambda m: m['score'] == best_score, movies_data))
    best_movie = reduce(lambda m1, m2: m1 if m1['rating'] > m2['rating'] else m2, best_movies)
    return best_movie

async def end_finder_session(session_id, session):
    print('ENDING SESSIOn')
    winning_movie = find_winning_movie(session)
    print(f"winner: {winning_movie['title']}")
    websockets.broadcast(session['users'], event_message_to_json(EVENTS.RESULT, winning_movie))
    print('closing connections')
    for websocket in session['users']:
        await websocket.close()
    print(f'Closing session: {session_id}')
    SESSIONS.pop(session_id)

async def handler(websocket, path):
    session = None
    try:
        session_id, session = await validate_session_id(websocket, path)
        register_user(websocket, path, session)
        await send_event_message(websocket, EVENTS.MOVIES, get_most_popular_movies())
        asyncio.create_task(end_session_on_timeout(session_id, session, SESSION_TIMEOUT))
        
        while True:
            message = await receive_event_message(websocket)
            if 'votes' not in session:
                session['votes'] = {}
                session['total_votes'] = 0
            if message['event'] == EVENTS.UPVOTE:
                handle_upvote_event(message, session['votes'])
            elif message['event'] == EVENTS.DOWNVOTE:
                handle_downvote_event(message, session['votes'])
            session['total_votes'] += 1
            print("Session:",session)

    except Exception as e:
        print(e)
        await websocket.close()
    finally:
        # Unregister user
        if session is not None:
            session['users'].remove(websocket)
        print(f"Currently there are {sum(len(session['users']) for session in SESSIONS.values())} connected")

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
    async with websockets.serve(handler, host='0.0.0.0', port=PORT):
        print(f"Running websocket on port {PORT}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
