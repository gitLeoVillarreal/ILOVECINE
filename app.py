import os
from flask import Flask, flash, redirect, render_template, request, session
import sqlite3
import json
from helpers import recommendation

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


@app.route('/')
def index():
    session['maxScore'] = 0
    return redirect("/recomendations")

@app.route('/recomendations', methods=['GET', 'POST'])
def recommend():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM movies")
    movies = cursor.fetchall()

    if request.method == "POST":
        recommendMovieFinal = []
        movie = request.form.get("movie")
        recommendMovie = recommendation(movie)

        if not recommendMovie:
            flash("Movie not found in the database. Please try again.")
            return render_template('recommend.html', movies=movies)
        
        for rm in recommendMovie:
            markers = ", ".join(["?"] * len(json.loads(rm[4])))
            #print(rm[4], markers, len(rm[4]))
            cursor.execute(f"SELECT name FROM genres WHERE genre_id IN ({markers})", json.loads(rm[4]))
            genres = cursor.fetchall()
            genresClean = [g[0] for g in genres]
            
            recommendMovieFinal.append(
                {"title": rm[2],
                "poster": rm[3],
                "genres": genresClean,
                "popularity": rm[5],
                "rating": rm[6],
                "release_date": rm[7]}
            )
        cursor.close()
        conn.close()
        return render_template('recommend.html', movies=movies, recommendedMovie=recommendMovieFinal)
    else:
        
        cursor.close()
        conn.close()

        return render_template('recommend.html', movies=movies)

@app.route('/guessthemovie', methods=['GET', 'POST'])
def guess():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies")
    movies = cursor.fetchall()
    randomPosterFinal = []
    if request.method == 'POST':
        
        if str(request.form.get('movie')).lower() == str(request.form.get('movie_title')).lower():
            score = int(request.form.get('score')) + 100
            guesses = int(request.form.get('guesses'))

            cursor.execute("SELECT movie_id FROM movies ORDER BY RANDOM() LIMIT 1")
            randomMovieId = cursor.fetchone()
            print(randomMovieId)
            cursor.execute("SELECT title, poster_url FROM movies WHERE movie_id = ?", (randomMovieId[0],))
            randomPoster = cursor.fetchall()
            #print(randomPoster)

            randomPosterFinal = {   
                "movie_id": randomMovieId[0],
                "title": randomPoster[0][0],
                "poster_url": randomPoster[0][1],
                "score": score,
                "guesses": 0
            }
            
            return render_template('guess.html', movies=movies, randomPoster=randomPosterFinal)
            
        else:
            guesses = int(request.form.get('guesses')) + 1
            score = int(request.form.get('score')) - (10 * guesses)
            if guesses >= 5:
                if score > session['maxScore']:
                    session['maxScore'] = score
                flash(f"Game over! Your final score is {score}. Your highest score is {session['maxScore']}.")
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
        return render_template('guess.html', movies=movies, randomPoster=randomPosterFinal)

    else:
        cursor.execute("SELECT movie_id FROM movies ORDER BY RANDOM() LIMIT 1")
        randomMovieId = cursor.fetchone()
        print(randomMovieId)
        cursor.execute("SELECT title, poster_url FROM movies WHERE movie_id = ?", (randomMovieId[0],))
        randomPoster = cursor.fetchall()
        #print(randomPoster)

        randomPosterFinal = {   
            "movie_id": randomMovieId[0],
            "title": randomPoster[0][0],
            "poster_url": randomPoster[0][1],
            "score": 0,
            "guesses": 0
        }

        #print(randomPosterFinal, "get")
        return render_template('guess.html', movies=movies, randomPoster=randomPosterFinal)