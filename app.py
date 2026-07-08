import os
from flask import Flask, flash, redirect, render_template, request, session
import sqlite3

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('layout.html')

@app.route('/Recomendations')
def recommend():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM movies")
    movies = cursor.fetchall()
    
    cursor.close()
    
    conn.close()
    return render_template('recommend.html', movies=movies)

@app.route('/GuessTheMovie')
def gues():
    return render_template('guess.html')