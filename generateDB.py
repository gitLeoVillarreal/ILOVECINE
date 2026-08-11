import sqlite3
import os
import datetime
import requests
from dotenv import load_dotenv
from helpers import Connection

TMDB_BASE_URL = "https://api.themoviedb.org/3"

MAX_PAGE = 150
LEN = "en-US"

load_dotenv()
api_key = os.getenv("TMDB_API_KEY")

def UsersDataBase():
    db = Connection()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        hash TEXT NOT NULL,
        max_score INTEGER NOT NULL DEFAULT 0
        )
""")
    print("Table users created")

#MAKE A LIST OF ALL THE MOVIES TIL PAGE 100 APROX. 1600 MOVIES DEPENDING ON THE LEN
def MovieList():
    movies = []
    i = 1
    today = datetime.date.today().isoformat()

    while i <= MAX_PAGE:
        response = requests.get(
        TMDB_BASE_URL + f"/discover/movie",
        params={"api_key": api_key, "include_adult": "false", "language": LEN, "page": i, "sort_by": "popularity.desc", "vote_count.gte": 80, "certification_country": "US", "region": "US"}
        )

        response.raise_for_status()
        
        data = response.json()
        movies.extend(data["results"])
        

        i += 1

    movies = [
        m for m in movies
        if m.get("release_date") and m["release_date"] <= today
    ]

    sorted_movies = sorted(movies, key=lambda m: m["popularity"], reverse=True)
    
    return sorted_movies

#SEARCH AND RETURN THE MOST VOTED POSTER OF A MOVIE BY MOVIE_ID

def LookupPoster(poster):
    if poster:
        return f"https://image.tmdb.org/t/p/w500{poster}?"
    else:
        return "Not Found"

#CREATES THE DATABASE FOR APP USAGE

def MovieDataBase():
    
    db = Connection()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_id INTEGER NOT NULL UNIQUE,
        title TEXT NOT NULL,
        poster_url TEXT NOT NULL,
        genre_ids TEXT NOT NULL,
        overview TEXT NOT NULL,
        popularity NUMERIC NOT NULL,
        rating NUMERIC NOT NULL,
        release_date DATE NOT NULL
    )
""")
    
    moviesList = MovieList()

    for m in moviesList:

        addMovie = (m["id"], m["title"], LookupPoster(m["poster_path"]), m["overview"] ,str(m["genre_ids"]), m["popularity"], m["vote_average"], m["release_date"])
    
        cursor.execute("INSERT OR IGNORE INTO movies (movie_id, title, poster_url, overview, genre_ids, popularity, rating, release_date) VALUES (?,?,?,?,?,?,?,?)", addMovie)
        
    db.commit()
    db.close()
    print("Movies saved")

def GenreList():
    genres = []

    response = requests.get(
        TMDB_BASE_URL + f"/genre/movie/list",
        params={"api_key": api_key}
        )

    response.raise_for_status()
        
    data = response.json()
    genres = (data["genres"])
    
    return genres

def GenreDataBase():
    
    db = Connection()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS genres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        genre_id INTEGER NOT NULL UNIQUE,
        name TEXT NOT NULL
    )
""")
    
    genreList = GenreList()

    for g in genreList:
        addGenre = (g["id"], g["name"])
    
        cursor.execute("INSERT OR IGNORE INTO genres (genre_id, name) VALUES (?,?)", addGenre)
    db.commit()    
    db.close()
    print("Genres saved")

def main():
    MovieDataBase()
    GenreDataBase()
    UsersDataBase()


if __name__ == "__main__":
    main()