from tmdbv3api import TMDb
from tmdbv3api import Movie
import json
import time
import pickle 
tmdb = TMDb()
tmdb.language = 'en'
tmdb.debug = True

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

movie = Movie()

MOVIES = []
MOVIES_TITLE = set()

def save_movie(m):
    title = m.title
    if title not in MOVIES_TITLE:
        MOVIES.append(m)
        MOVIES_TITLE.add(title)

for page in range(1,100):
    time.sleep(1)
    popular_movies = movie.popular(page)
    for m in popular_movies:
        save_movie(m)
    time.sleep(1)
    best_movies = movie.top_rated(page)
    for m in best_movies:
        save_movie(m)
       
    print(len(MOVIES), page)
    time.sleep(1)

    if page % 5 == 0:
        with open('all_movies.obj', 'wb') as file:
            pickle.dump(MOVIES, file)

print(MOVIES)
with open('all_movies.obj', 'wb') as file:
    pickle.dump(MOVIES, file)