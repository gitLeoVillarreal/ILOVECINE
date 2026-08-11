import os
from flask import Flask, flash, redirect, render_template, request, session
import json
from argon2 import PasswordHasher
from helpers import recommendation, Connection, random_poster_movie, random_poster_movie_home,  get_max_score, set_max_score, get_moviesinfo_for_openai, generate_response
import numpy as np
import sqlite3

app = Flask(__name__)

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise ValueError("Theres no SECRET_KEY at env variables")
app.secret_key = secret_key

movieIdListEmbeddings = np.load("movies_id_embeddings.npy")

@app.route('/')
def index():
   
    return redirect("/home")

@app.route('/login', methods=['GET','POST'])
def login():
    db = None
    session.clear()

    if request.method == "POST":
        ph = PasswordHasher()
        username = request.form.get("username")
        password = request.form.get("password")
        if username:
            try:
                db = Connection()
                cursor = db.cursor()

                cursor.execute("SELECT id, hash FROM users WHERE username = ?", (username,))
                row = cursor.fetchall()

                if not row:
                    flash("Invalid values!", 'error')
                    db.close()
                    return render_template("login.html")
                userID, hash_p = row[0][0], row[0][1]

                ph.verify(hash_p, password)

                db.close()

                session["user_id"] = userID
                
                session["username"] = username
                flash(f"Welcome {username} to I Love Cine", 'message')
                return redirect("/home")
                
            except Exception as e:
                flash("Invalid values!", 'error')
                if db:
                    db.close()
                return render_template("login.html")
    else:
        return render_template("login.html")

@app.route('/register', methods=['GET','POST'])
def register():
    db = None
    if request.method == "POST":
        ph = PasswordHasher()
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        if username and password == confirm:
            try:
                hash_p = ph.hash(password)
                db = Connection()
                cursor = db.cursor()
                values = (username, hash_p, 0)
                
                try:
                    cursor.execute("INSERT INTO users (username, hash, max_score) VALUES (?, ?, ?)", values)
                    flash("Your account have been created!", 'message')
                    db.commit()
                    db.close()
                    return redirect("/login")
                except sqlite3.IntegrityError :
                    flash("Username already in use!", 'alert')
                    if db:
                        db.close()
                    return render_template("register.html")
            except Exception:
                flash("Invalid values!", 'error')
                if db:
                    db.close()
                return render_template("register.html")
        else:
            flash("Missing username or passwords did not match!", 'error')
            return render_template("register.html")
    else:
        return render_template("register.html")
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route('/home')
def home():
    db = Connection()
    cursor = db.cursor()
    movies_home = []
    
    movies_home = random_poster_movie_home(cursor)
    db.close()
    return render_template("home.html", movies_home=movies_home)

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
            flash("Movie not found in the database. Please try again.", 'error')
            db.close()
            return render_template('recommend.html', movies=movies)
        
        for rm in recommendMovie:
            markers = ", ".join(["?"] * len(json.loads(rm['genre_ids'])))
            
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
    if session.get("user_id"):
            session['maxScore'] = get_max_score(session['user_id'])

    else:
       session['maxScore'] = session.get('maxScore', 0)
       
    db = Connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM movies")
    movies = cursor.fetchall()
    randomPosterFinal = []
    if request.method == 'POST':
        
        if str(request.form.get('movie')).lower() == str(request.form.get('movie_title')).lower():
            session['score'] = int(session['score']) + 100
            session['guesses'] = 0

            randomPoster = random_poster_movie(cursor)
            

            randomPosterFinal = {   
                "movie_id": randomPoster['movie_id'],
                "title": randomPoster['title'],
                "poster_url": randomPoster['poster_url'],
            }
            db.close()
            return render_template('guess.html', movies=movies, randomPoster=randomPosterFinal)
            
        else:
            session['guesses'] = int(session['guesses']) + 1
            session['score'] = int(session['score']) - (10 * session['guesses'])
            if session['guesses'] >= 5:
                if session['score'] > int(session['maxScore']):
                    
                    if session.get("user_id"):
                        
                        set_max_score(session['user_id'], session['score'])
                        session['maxScore'] = get_max_score(session['user_id'])
                    else:
                        
                        session['maxScore'] = session['score']

                    flash(f"Game over! Your final score was {session['score']}. Your new highest score is {session['maxScore']}.")
                    db.close()
                    return redirect("/guessthemovie")
                
                flash(f"Game over! Your final score was {session['score']}. Your highest score is {session['maxScore']}.")
                db.close()
                return redirect("/guessthemovie")

            flash(f"Incorrect guess -{10 * session['guesses']}pts! You have {5 - session['guesses']} guesses left.", 'alert')
            
        
        movie_id = request.form.get('movie_id')
        movie_title = request.form.get('movie_title')
        cursor.execute("SELECT poster_url FROM movies WHERE movie_id = ?", (movie_id,))
        randomPoster = cursor.fetchone()
        
        randomPosterFinal = {   
            "movie_id": movie_id,
            "title": movie_title,
            "poster_url": randomPoster[0],
        }
        db.close()
        return render_template('guess.html', movies=movies, randomPoster=randomPosterFinal)

    else:
        session['score'] = 0
        session['guesses'] = 0
        randomPoster = random_poster_movie(cursor)
        db.close()
        return render_template('guess.html', movies=movies, randomPoster=randomPoster)

@app.route("/ask", methods=["POST", "GET"])
def askAboutMovies():
    if request.method == "POST":
        userInput = request.form.get('input')
        
        if not userInput:
            return render_template("ask.html")
        
        moviesInfo = get_moviesinfo_for_openai(userInput, movieIdListEmbeddings)
        AIRecommend = generate_response(moviesInfo, userInput)
        
        return render_template("ask.html", AIRecommend=AIRecommend)
    else:
        return render_template("ask.html")