import os
from flask import Flask, flash, redirect, render_template, request, session
import json
from argon2 import PasswordHasher
from helpers import recommendation, Connection, random_poster_movie, get_max_score, set_max_score

app = Flask(__name__)

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise ValueError("Theres no SECRET_KEY at env variables")
app.secret_key = secret_key
@app.route('/')
def index():
   
    return redirect("/home")

@app.route('/login', methods=['GET','POST'])
def login():

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
                    return render_template("login.html")
                userID, hash_p = row[0][0], row[0][1]

                print(userID, hash_p)

                ph.verify(hash_p, password)

                db.close()

                session["user_id"] = userID
                print(session['user_id'])
                session["username"] = username
                flash(f"Welcome {username} to I Love Cine", 'message')
                return redirect("/home")
                
            except Exception as e:
                flash("Invalid values!", 'error')
                print(e)
                return render_template("login.html")
    else:
        return render_template("login.html")

@app.route('/register', methods=['GET','POST'])
def register():
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
                except:
                    flash("Username already in use!", 'alert')
                    return render_template("register.html")
            except Exception:
                flash("Invalid values!", 'error')
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
    for _ in range(1,30):
        movies_home.append(random_poster_movie(cursor))
    #for m in movies_home:
    #    print(m['title'])
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
    if session['user_id'] != None:
            session['maxScore'] = get_max_score(session['user_id'])
    else:
        session['maxScore'] = 0
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
                if score > int(session['maxScore']):
                    print(f"{score} > {session['maxScore']}")
                    if session['user_id']:
                        print(session['user_id'])
                        set_max_score(session['user_id'], score)
                        session['maxScore'] = get_max_score(session['user_id'])
                    else:
                        session['maxScore'] = score

                    flash(f"Game over! Your final score is {score}. Your new highest score is {session['maxScore']}.")
                    db.close()
                    return redirect("/guessthemovie")
                
                flash(f"Game over! Your final score is {score}. Your highest score is {session['maxScore']}.")
                db.close()
                return redirect("/guessthemovie")

            flash(f"Incorrect guess -{10 * guesses}pts! You have {5 - guesses} guesses left.", 'alert')
            
        
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