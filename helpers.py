import os
import datetime
import requests
import sqlite3
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

MAX_PAGE = 100


#MAKE A LIST OF ALL THE MOVIES TIL PAGE 100 APROX. 2000 MOVIES
def MovieList():
    movies = []
    i = 1
    today = datetime.date.today().isoformat()

    while i <= MAX_PAGE:
        response = requests.get(
        TMDB_BASE_URL + f"/movie/popular?page={i}",
        params={"api_key": api_key}
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

def lookupPoster(poster):
    if poster:
        return f"https://image.tmdb.org/t/p/w500{poster}?"
    else:
        return "Not Found"

#CREATES THE DATABASE FOR APP USAGE

def MovieDataBase():
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_id INTEGER NOT NULL UNIQUE,
        title TEXT NOT NULL,
        poster_url TEXT NOT NULL,
        genre_ids TEXT NOT NULL,
        popularity NUMERIC NOT NULL,
        rating NUMERIC NOT NULL,
        release_date DATE NOT NULL
    )
""")
    
    moviesList = MovieList()

    for m in moviesList:

        addMovie = (m["id"], m["title"], lookupPoster(m["poster_path"]), str(m["genre_ids"]), m["popularity"], m["vote_average"], m["release_date"])
    
        cursor.execute("INSERT OR IGNORE INTO movies (movie_id, title, poster_url, genre_ids, popularity, rating, release_date) VALUES (?,?,?,?,?,?,?)", addMovie)
        
    conn.commit()
    conn.close()
    print("Movies saved")


def main():
    MovieDataBase()

if __name__ == "__main__":
    main()
    
