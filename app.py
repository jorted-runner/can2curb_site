from flask import Flask, render_template, redirect, url_for, request, jsonify, abort, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_bootstrap import Bootstrap
from flask_session import Session

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

import app_config
import os

from dotenv import load_dotenv
from functools import wraps
from sqlalchemy import func
from datetime import datetime
from sqlalchemy import and_

app = Flask(__name__)
app.config.from_object(app_config)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = app_config.DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(100), nullable=False)
    lname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=True)
    sign_up_date = db.Column(db.DateTime, default=datetime.now)
    profile_type = db.Column(db.String(100), nullable=False, default='client')
    addresses = db.relationship('Address', backref='user', cascade="all, delete-orphan")

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    house_num = db.Column(db.String(15), nullable=False)
    street_address = db.Column(db.String(250), nullable=False)
    city = db.Column(db.String(250), nullable=False)
    state = db.Column(db.String(250), nullable=False)
    zip_code = db.Column(db.String(15), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trash_can_data = db.relationship('Trash_Can_Data', backref='address', uselist=False, cascade="all, delete-orphan")

class Trash_Can_Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    num_cans = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(250), nullable=False)
    gate_garage_code = db.Column(db.String(250), nullable=False)
    pet_info = db.Column(db.String(250), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), unique=True, nullable=False)

login_manager = LoginManager()
login_manager.init_app(app)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html', e=e)

@app.errorhandler(403)
def not_found(e):
    return render_template('403.html', e=e)

@app.errorhandler(Exception)
def handle_exception(e):
    return render_template('error.html', e=e), 500

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)
