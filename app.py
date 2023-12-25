from flask import Flask, session, render_template, redirect, request, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import psycopg2

app = Flask(__name__)


app.secret_key = 'smell'  # Ключ для сессий


def dbConnect():
    conn = psycopg2.connect(
        host="127.0.0.1",
        database="cinema",
        user="tkach",
        password="stink")

    return conn