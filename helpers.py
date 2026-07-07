import os
import requests
import datetime
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

def movieList():
    currentDate = datetime.datetime.now()

    response = requests.get(
        TMDB_BASE_URL + "/movie/changes",
        params={"api_key": api_key}
    )
    data = response.json()

    print(data["results"])

def lookup(name):
    response = requests.get(
        TMDB_BASE_URL + "/search/movie",
        params={"api_key": api_key, "query": name}
    )

    data = response.json()
    movies = data["results"]

    movies_ordenados = sorted(movies, key=lambda m: m["popularity"], reverse=True)

    return movies_ordenados


#lookup("Inception")
movieList()
