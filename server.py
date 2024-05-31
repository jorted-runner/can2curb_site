from flask import Flask, render_template, redirect, url_for, request, jsonify, abort, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_bootstrap import Bootstrap
from flask_session import Session

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
import os
import traceback

from dotenv import load_dotenv
from functools import wraps
from sqlalchemy import func
from datetime import datetime
from sqlalchemy import and_

import app_config
from retrieval import Retrieval
from data_validation import Data_Validation

load_dotenv()
RETRIEVER = Retrieval()
VALIDATOR = Data_Validation()

app = Flask(__name__)
app.config.from_object(app_config)
app.config['SECRET_KEY'] = app_config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = app_config.DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(100), nullable=False)
    lname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
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
    trash_day = db.Column(db.String(15), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trash_can_data = db.relationship('Trash_Can_Data', backref='address', uselist=False, cascade="all, delete-orphan")
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=True)

class Route_Addresses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column('route_id', db.Integer, db.ForeignKey('route.id'))
    address_id = db.Column('address_id', db.Integer, db.ForeignKey('address.id'))

class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    day = db.Column(db.String(15), nullable=False)
    addresses = db.relationship("Route_Addresses", backref='routes', cascade="all, delete-orphan")

class Trash_Can_Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    num_cans = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(250), nullable=False)
    gate_garage_code = db.Column(db.String(250), nullable=True)
    pet_info = db.Column(db.String(250), nullable=True)
    notes = db.Column(db.String(250), nullable=True)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), unique=True, nullable=False)

login_manager = LoginManager()
login_manager.init_app(app)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.profile_type == 'client':
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

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
    if current_user.is_authenticated:
        if current_user.profile_type != 'client' or current_user.email in app_config.ADMIN_EMAILS:
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('manage'))
    return render_template('index.html')

@app.route('/add_admin_account', methods=['POST', 'GET'])
def add_admin_account():
    if request.method == 'POST':
        admin_code = request.form.get('admin_code')
        if admin_code == os.environ.get('ADD_ADMIN_PASSWORD'):
            first_name = VALIDATOR.clean_input(request.form.get('first-name'))
            last_name = VALIDATOR.clean_input(request.form.get('last-name'))
            email = VALIDATOR.clean_input(request.form.get('email'))
            phone_num = VALIDATOR.clean_input(request.form.get('phone'))
            password = request.form.get('password_conf')
            new_user_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            try:
                new_user = User(
                    fname=first_name, 
                    lname=last_name,
                    email=email,
                    phone=phone_num,      
                    password=new_user_password,
                    profile_type='employee'
                )
                db.session.add(new_user)
                
                db.session.commit()
                flash('Employee Account Created')
                return redirect(url_for('login'))
            except:
                db.session.rollback()
                traceback.print_exc()
                flash('Issue adding Employee account')
                return render_template('add_admin.html')
        else:
            flash('Incorrect Admin Code')
            return render_template('add_admin.html')
    return render_template('add_admin.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        first_name = VALIDATOR.clean_input(request.form.get('first-name'))
        last_name = VALIDATOR.clean_input(request.form.get('last-name'))
        email = VALIDATOR.clean_input(request.form.get('email'))
        phone_num = VALIDATOR.clean_input(request.form.get('phone'))
        password = request.form.get('password_conf')
        house_num = VALIDATOR.clean_input(request.form.get('houseNum'))
        street_address = VALIDATOR.clean_input(request.form.get('street'))
        city = VALIDATOR.clean_input(request.form.get('city'))
        state = VALIDATOR.clean_input(request.form.get('state'))
        zipcode = VALIDATOR.clean_input(request.form.get('zipcode'))
        trash_day = VALIDATOR.clean_input(request.form.get('trash_day'))
        num_cans = VALIDATOR.clean_input(request.form.get('number-of-cans'))
        location = VALIDATOR.clean_input(request.form.get('location'))
        gate_code = VALIDATOR.clean_input(request.form.get('gate-code'))
        pet_info = VALIDATOR.clean_input(request.form.get('pets'))
        notes = VALIDATOR.clean_input(request.form.get('notes'))

        if RETRIEVER.get_user(User, email, 'email'):
            flash("You've already signed up with that email, <a href='" + url_for('login') + "'>log in</a> instead!")
            return redirect(url_for('register'))
        
        new_user_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        
        new_user = User(
            fname=first_name, 
            lname=last_name,
            email=email,
            phone=phone_num,      
            password=new_user_password
        )
        db.session.add(new_user)
        
        db.session.commit()
        new_address = Address(
            house_num=house_num,
            street_address=street_address,
            city=city,
            state=state,
            zip_code=zipcode,
            trash_day=trash_day,
            user_id=new_user.id
        )
        db.session.add(new_address)
        db.session.commit()

        new_trash_can = Trash_Can_Data(
            num_cans=num_cans, 
            location=location, 
            gate_garage_code=gate_code, 
            pet_info=pet_info, 
            notes=notes,
            address_id=new_address.id
        )
        db.session.add(new_trash_can)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('manage'))
    return render_template('register.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = VALIDATOR.clean_input(request.form.get('email'))
        password = VALIDATOR.clean_input(request.form.get('password'))
        user = User.query.filter(or_(User.email == email)).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                if user.profile_type != 'client' or user.email in app_config.ADMIN_EMAILS:
                    return redirect(url_for('admin'))
                return redirect(url_for('manage'))
            else:
                flash("Incorrect Password, try again!")
                return render_template("login.html", current_user=current_user)
        else:
            flash("No user associated with that email, try <a href='" + url_for('register') + "'>registering</a>!")
            return redirect(url_for('login'))
    else:
        return render_template("login.html", current_user=current_user)


@app.route('/manage')
@login_required
def manage():
    user = User.query.filter_by(id=current_user.id).first()
    return render_template('manage.html', user=user)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/admin')
@admin_only
def admin():
    title = 'Admin Home'
    addresses = Address.query.all()
    return render_template('admin.html', title=title, addresses=addresses, current_user=current_user)

@app.route('/build-route', methods=['GET', 'POST'])
@admin_only
def build_route():
    if request.method == 'POST':
        try:
            name = request.form.get('route_name')
            day = request.form.get('trash_day')
            selected_addresses_ids = request.form.getlist('selected_addresses')
            new_route = Route(name=name, day=day)
            db.session.add(new_route)
            db.session.commit()
            for address in selected_addresses_ids:
                new_addy = Route_Addresses(route_id=new_route.id, address_id=int(address))
                db.session.add(new_addy)
                db.session.commit()
            flash('Route successfully saved', 'success')
            return jsonify({'success': True}), 200
        except:
            db.session.rollback()
            traceback.print_exc()
            return jsonify({'success': False, 'message': 'Issue saving route'})
    addresses = Address.query.all()
    title = 'Build Route'
    return render_template('build_route.html', title=title, addresses=addresses, current_user=current_user)

@app.route('/view-routes', methods=['GET'])
@admin_only
def view_routes():
    all_routes = Route.query.all()
    title = 'View Routes'
    return render_template('view_routes.html', title=title, all_routes=all_routes)

@app.route('/view_route/<int:route_id>')
@admin_only
def view_route(route_id):
    route = Route.query.filter_by(id=route_id).first()
    title = f'View {route.name} Route'
    if route is None:
        flash("Route not found")
        return redirect(url_for('view_routes'))
    route_addresses_id_data = Route_Addresses.query.filter_by(route_id=route_id).all()
    address_ids = [ra.address_id for ra in route_addresses_id_data]
    route_addresses = Address.query.filter(Address.id.in_(address_ids)).all()
    return render_template('view_route.html', route=route, title=title, addresses=route_addresses)

@app.route('/view_customers')
@admin_only
def view_customers():
    customers = User.query.filter_by(profile_type='client').all()
    title = 'View Customers'
    return render_template('view_customers.html', title=title, customers=customers, current_user=current_user)

@app.route('/view_customer/<customer_id>')
@admin_only
def view_customer(customer_id):
    customer = User.query.filter_by(id=customer_id).first()
    title = f'View {customer.fname} {customer.lname}'
    return render_template('view_customer.html', title=title, customer=customer, current_user=current_user)

if __name__ == '__main__':
    app.run(debug=True)
