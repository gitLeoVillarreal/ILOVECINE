import os
from flask import Flask, flash, redirect, render_template, request, session
import json
from helpers import recommendation, Connection, random_poster_movie

app = Flask(__name__)

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise ValueError("Falta la variable de entorno SECRET_KEY")
app.secret_key = secret_key

@app.route('/')
def index():
    session['maxScore'] = 0
    return render_template("home.html")

@app.route('/recomendations', methods=['GET', 'POST'])
def recommend():
    db = Connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT title, poster_url FROM movies")
    movies = cursor.fetchall()

    if request.method == "POST":
        recommendMovieFinal = []
        movie = request.form.get("movie")
        recommendMovie = recommendation(movie)

        if not recommendMovie:
            flash("Movie not found in the database. Please try again.")
            return render_template('recommend.html', movies=movies)
        
        for rm in recommendMovie:
            markers = ", ".join(["?"] * len(json.loads(rm['genre_ids'])))
            #print(rm[4], markers, len(rm[4]))
            cursor.execute(f"SELECT name FROM genres WHERE genre_id IN ({markers})", json.loads(rm['genre_ids']))
            genres = cursor.fetchall()
            genresClean = [g[0] for g in genres]
            
            recommendMovieFinal.append(
                {"title": rm['title'],
                "poster": rm['poster_url'],
                "genres": genresClean,
                "popularity": rm['popularity'],
                "rating": rm['rating'],
                "release_date": rm['release_date']}
            )
        db.close()
        return render_template('recommend.html', movies=movies, recommendedMovie=recommendMovieFinal)
    else:
        
        db.close()

        return render_template('recommend.html', movies=movies)

@app.route('/guessthemovie', methods=['GET', 'POST'])
def guess():
    db = Connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM movies")
    movies = cursor.fetchall()
    randomPosterFinal = []
    if request.method == 'POST':
        
        if str(request.form.get('movie')).lower() == str(request.form.get('movie_title')).lower():
            score = int(request.form.get('score')) + 100
            guesses = int(request.form.get('guesses'))

            randomPoster = random_poster_movie(cursor)
            

            randomPosterFinal = {   
                "movie_id": randomPoster['movie_id'],
                "title": randomPoster['title'],
                "poster_url": randomPoster['poster_url'],
                "score": score,
                "guesses": 0
            }
            db.close()
            return render_template('guess.html', movies=movies, randomPoster=randomPosterFinal)
            
        else:
            guesses = int(request.form.get('guesses')) + 1
            score = int(request.form.get('score')) - (10 * guesses)
            if guesses >= 5:
                if score > session.get('maxScore', 0):
                    session['maxScore'] = score

                flash(f"Game over! Your final score is {score}. Your highest score is {session['maxScore']}.")
                db.close()
                return redirect("/guessthemovie")

            flash(f"Incorrect guess! You have {5 - guesses} guesses left.")
            
        
        movie_id = request.form.get('movie_id')
        movie_title = request.form.get('movie_title')
        cursor.execute("SELECT poster_url FROM movies WHERE movie_id = ?", (movie_id,))
        randomPoster = cursor.fetchone()
        randomPosterFinal = {   
            "movie_id": movie_id,
            "title": movie_title,
            "poster_url": randomPoster[0],
            "score": score,
            "guesses": guesses
        }
        #print(randomPosterFinal, "post")
        db.close()
        return render_template('guess.html', movies=movies, randomPoster=randomPosterFinal)

    else:
        randomPoster = random_poster_movie(cursor)
        #print(randomPoster)

        randomPosterFinal = {   
            "movie_id": randomPoster['movie_id'],
            "title": randomPoster['title'],
            "poster_url": randomPoster['poster_url'],
            "score": 0,
            "guesses": 0
        }

        #print(randomPosterFinal, "get")
        db.close()
        return render_template('guess.html', movies=movies, randomPoster=randomPosterFinal)