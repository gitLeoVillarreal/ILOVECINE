import os
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session

load_dotenv()
api_key = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

app = Flask(__name__)

