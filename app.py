#!/usr/bin/env python

import asyncio
from re import S
import websockets
from tmdbv3api import TMDb
from tmdbv3api import Movie
import time
from functools import reduce
from websocket_event import *
import pickle
import random
import signal
import os


tmdb = TMDb()
tmdb.language = 'en'
tmdb.debug = True



PORT = 8001
if 'PORT' in os.environ:
    PORT = int(int(os.environ["PORT"]))

SESSIONS = {}

SESSION_TIMEOUT = 70


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





async def validate_session_id(websocket, session_id):
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {
            'start_time': time.time(),
            'users': dict()
        }
        asyncio.create_task(end_session_on_timeout(session_id, SESSIONS[session_id], SESSION_TIMEOUT))
    return SESSIONS[session_id]

def register_user(websocket, path, session):
    # Register user
    session['users'][websocket] = {
        'page': 1
    }

def get_most_popular_movies(page=1):
    movie = Movie()
    movies = movie.popular(page=page)
    movies_data = movies_to_movie_data(movies)
    random.shuffle(movies_data)
    return movies_data

def handle_vote_event(message, store, vote_value):
    genre_ids = message["data"]["genre_ids"]
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
    if 'votes' not in session:
        return MOVIE_LIST[69]
    else:
        for movie in movies_data:
            movie['score'] = genre_match_score(movie, session['votes'], session['total_votes'])

        best_score = max(movie['score'] for movie in movies_data)
        best_movies = list(filter(lambda m: m['score'] == best_score, movies_data))
        best_movie = reduce(lambda m1, m2: m1 if m1['rating'] > m2['rating'] else m2, best_movies)
        return best_movie

async def end_finder_session(session_id, session):
    winning_movie = find_winning_movie(session)
    websockets.broadcast(session['users'].keys(), event_message_to_json(EVENTS.RESULT, winning_movie))
    users_copy =  [websocket for websocket in session['users'].keys()]
    for websocket in users_copy:
        await websocket.close()

def deactive_session(session_id):
    if session_id in SESSIONS:
        SESSIONS.pop(session_id)
async def handler(websocket, path):
    session_id = 0
    try:
        session_id = int(path.replace('/','')[:20])
    except Exception as e:
        #print(f'Connection failed with {websocket} at path: {path} error: {e}')
        return

    session = await validate_session_id(websocket, session_id)
    register_user(websocket, path, session)

    try:
        
        await send_event_message(websocket, EVENTS.MOVIES, 
            {
                'movies':get_most_popular_movies(),
                'session_time_remaining': SESSION_TIMEOUT - (time.time() - session['start_time']),
                'users': len(session['users'])
            })
        
        while True:
            message = await receive_event_message(websocket)
            if 'votes' not in session:
                session['votes'] = {}
                session['total_votes'] = 0
            if message['event'] == EVENTS.UPVOTE:
                handle_upvote_event(message, session['votes'])
                print(f'{len(session["users"])} users | like {message["data"]["title"]}')    
                session['total_votes'] += 1
            elif message['event'] == EVENTS.DOWNVOTE:
                handle_downvote_event(message, session['votes'])
                print(f'{len(session["users"])} users | dislike {message["data"]["title"]}')    
                session['total_votes'] += 1
            elif message['event'] == EVENTS.MOVIES:
                session['users'][websocket]['page'] += 1
                await send_event_message(websocket, EVENTS.MOVIES, 
                {
                'movies':get_most_popular_movies(page=session['users'][websocket]['page']),
                'session_time_remaining': SESSION_TIMEOUT - (time.time() - session['start_time']),
                'users': len(session['users'])
                })
                 
            if session['total_votes'] % 50 == 0:
                print(f'{session["total_votes"]} total votes | winner: {find_winning_movie(session)["title"]}')

    except Exception as e:
        #print(e)
        await websocket.close()
    finally:
        # Unregister user
        if session is not None:
            session['users'].pop(websocket)
        print(f"Currently there are {sum(len(session['users']) for session in SESSIONS.values())} users connected")

    session_keys_copy = [key for key in SESSIONS.keys()]
    for session_id in session_keys_copy:
        session = SESSIONS[session_id]
        if len(session['users']) == 0:
            deactive_session(session_id)
            print(f'Cleaned session: {session_id}')

async def main():
     # Set the stop condition when receiving SIGTERM.
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    print(f"Running websocket on port {PORT}")
    async with websockets.serve(
        handler,
        host="0.0.0.0",
        port=PORT):
        await stop

if __name__ == "__main__":
    asyncio.run(main())
