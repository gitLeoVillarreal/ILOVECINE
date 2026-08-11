from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
import numpy as np

from helpers import Connection

load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')

def create_embeddings():
    movieList = []
    movie_idList = []
    db = Connection()
    cursor = db.cursor()

    cursor.execute("SELECT movie_id, title, overview FROM movies")
    result = cursor.fetchall()

    db.close()
    for m in result:
        movieList.append(f"Title: {m['title']}, Overview: {m['overview']}")
        movie_idList.append(m['movie_id'])

    vectors = model.encode(movieList)
    np.save("movies_embeddings.npy", vectors)

    
    np.save("movies_id_embeddings.npy", movie_idList)

create_embeddings()



