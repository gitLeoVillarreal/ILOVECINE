import os

from flask import Flask, flash, redirect, render_template, request, session

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('layout.html')

@app.route('/Recomendations')
def recommend():
    movie
    return render_template('recommend.html')

@app.route('/GuessTheMovie')
def gues():
    return render_template('guess.html')