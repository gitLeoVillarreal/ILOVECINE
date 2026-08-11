import os
import datetime
import requests
import sqlite3
from sentence_transformers import SentenceTransformer, util
from openai import OpenAI
import numpy as np
from dotenv import load_dotenv
import json
 
TMDB_BASE_URL = "https://api.themoviedb.org/3"
load_dotenv()

openrouter_api_key = os.getenv("OPEN_ROUTER_KEY")
api_key = os.getenv("TMDB_API_KEY")

model = SentenceTransformer('all-MiniLM-L6-v2')

client = OpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1"
)

def Connection():
    conn = sqlite3.connect("ILoveCineDB.db")
    conn.row_factory = sqlite3.Row
    return conn

def recommendation(movie):
    recommendations = []
    db = Connection()
    cursor = db.cursor()

    cursor.execute("SELECT movie_id FROM movies WHERE title = ?", (movie,))
    movieID = cursor.fetchall()

    if not movieID:
        return []
    
    response = requests.get(
        TMDB_BASE_URL + f"/movie/{movieID[0][0]}/recommendations",
        params={"api_key": api_key}
    )

    response.raise_for_status()
    data = response.json()

    movieRecomendations = data["results"]

    for mr in movieRecomendations:
        recommendations.append(mr["id"])

    markers = ", ".join(["?"] * len(recommendations))

    cursor.execute(f"SELECT * FROM movies WHERE movie_id IN ({markers})", recommendations)
    recommendedMovies = cursor.fetchall()

    db.close()
    return(recommendedMovies)

def random_poster_movie_home(cursor):
    

    cursor.execute("SELECT title, poster_url FROM movies ORDER BY RANDOM() LIMIT 20")
    randomPosters = cursor.fetchall()

    return randomPosters

def random_poster_movie(cursor):

    cursor.execute("SELECT movie_id, title, poster_url FROM movies ORDER BY RANDOM() LIMIT 1")
    randomPoster = cursor.fetchone()

    return randomPoster

def get_max_score(userID):
    db = Connection()
    cursor = db.cursor()

    cursor.execute("SELECT max_score FROM users WHERE id = ?", (userID,))
    userMaxScore = cursor.fetchone()
    db.close()
    return userMaxScore[0]


def set_max_score(userID, newMaxScore):
    db = Connection()
    cursor = db.cursor()
    values = (newMaxScore, userID)
    print(values)
    cursor.execute("UPDATE users SET max_score = ? WHERE id = ?", values)
    db.commit()
    db.close()

def search(userInput, movieIdList=np.load("movies_id_embeddings.npy")):
    movies = []
    moviesFinal = []
    vectors = np.load("movies_embeddings.npy")
    embendingInput = model.encode(userInput)

    for i in range(0, len(movieIdList)):
        sim = util.cos_sim(vectors[i], embendingInput)
            
        if sim >= 0.35:
            movies.append({"sim":sim, "id":movieIdList[i]})
    movies.sort(key=lambda x: x['sim'], reverse=True)

    base = min(len(movies), 5)

    if base == 0:
        return []

    for m in range(0,base):
        moviesFinal.append(int(movies[m]['id']))

    return moviesFinal

def generate_response(moviesInfo, userInput):
    movies_text = "\n".join([
        f"- {m['title']} ({m['release_date'][:4]}, ⭐ {m['rating']}): {m['overview']} {m['poster_url']}"
        for m in moviesInfo
    ])
     
    system_prompt = """You are ILOVECINE's recommendation assistant.

Your job is to recommend movies based SOLELY on the list provided.
Never make up movies that aren't on the list. If the list is empty, say so honestly.
For each movie, briefly explain why it fits the user's request, in a friendly and enthusiastic tone.

You must respond with ONLY a valid JSON array. No introduction, no explanation, no text before or after the JSON, no markdown code blocks or backticks.

The response must start with [ and end with ].

Format (exact structure, one object per movie):
[
  {"title": "Cars", "poster_url": "/poster1231.png", "recommendation": "recommendation text here"},
  {"title": "Cars 2", "poster_url": "/poster456.png", "recommendation": "recommendation text here"}
]"""

    user_prompt = f"""Available movies:
                {movies_text} User input: "{userInput}" recommend the movies that apply."""

    response = client.chat.completions.create(
    model="poolside/laguna-xs-2.1:free",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
)
    response = response.choices[0].message.content
    return json.loads(response)

def get_moviesinfo_for_openai(user):
    moviesInfo = []
    
    db = Connection()
    cursor = db.cursor()
    
    resultado = search(user)
    
    markers = ", ".join(["?"] * len(resultado))

    cursor.execute(f"SELECT * FROM movies WHERE movie_id IN ({markers})", resultado)
    moviesquery = cursor.fetchall()
    db.close()
    
    for m in moviesquery:
        moviesInfo.append({
        "title": m['title'],
        "overview": m['overview'],
        "poster_url": m['poster_url'],
        "rating": m['rating'],
        "popularity": m['popularity'],
        "release_date": m['release_date']
        }) 

    return moviesInfo




