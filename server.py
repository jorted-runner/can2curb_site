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
import json

from dotenv import load_dotenv
from functools import wraps
from sqlalchemy import func
from datetime import datetime
from sqlalchemy import and_

import app_config
from retrieval import Retrieval
from data_validation import Data_Validation
from email_handler import EmailHandler
from runtime_config import Config
runtime = Config()

load_dotenv()

RETRIEVER = Retrieval()
VALIDATOR = Data_Validation()
EMAILER = EmailHandler()

app = Flask(__name__)
app.config.from_object(app_config)
app.config['SECRET_KEY'] = app_config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = app_config.DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def current_month_name():
    return datetime.now().strftime('%B') 

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(100), nullable=False)
    lname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(250), nullable=True)
    sign_up_date = db.Column(db.DateTime, default=datetime.now)
    profile_type = db.Column(db.String(100), nullable=False, default='client')
    active_route_id = db.Column(db.Integer, nullable=True)
    active_route_addresses = db.Column(db.Text, nullable=True)
    addresses = db.relationship('Address', backref='user', cascade="all, delete-orphan")
    payment_history = db.relationship('Payment_History', backref='user', cascade="all, delete-orphan")

    @property
    def active_route_addresses_list(self):
        return json.loads(self.active_route_addresses) if self.active_route_addresses else []

    @active_route_addresses_list.setter
    def active_route_addresses_list(self, value):
        self.active_route_addresses = json.dumps(value)

class Payment_History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer, default=lambda: datetime.now().day)
    month = db.Column(db.String(20), default=current_month_name)
    year = db.Column(db.Integer, default=lambda: datetime.now().year)
    amount = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Service_History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer, default=lambda: datetime.now().day)
    month = db.Column(db.String(20), default=current_month_name)
    year = db.Column(db.Integer, default=lambda: datetime.now().year)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=False)

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    house_num = db.Column(db.String(15), nullable=False)
    street_address = db.Column(db.String(250), nullable=False)
    city = db.Column(db.String(250), nullable=False)
    state = db.Column(db.String(250), nullable=False)
    zip_code = db.Column(db.String(15), nullable=False)
    trash_day = db.Column(db.String(15), nullable=False)
    in_route = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trash_can_data = db.relationship('Trash_Can_Data', backref='address', uselist=False, cascade="all, delete-orphan")
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=True)
    service_history = db.relationship('Service_History', backref='address', cascade="all, delete-orphan")

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
        if current_user.profile_type != 'admin':
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


def employee_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.profile_type == 'employee' or current_user.profile_type == 'admin':  
            return f(*args, **kwargs)
        else:
            return abort(403)
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
        if current_user.profile_type == 'admin' or current_user.profile_type == 'employee':
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('manage'))
    return render_template('index.html')

@app.route('/add_employee_account', methods=['POST', 'GET'])
def add_employee_account():
    if request.method == 'POST':
        admin_code = request.form.get('admin_code')
        if admin_code == os.environ.get('ADD_EMPLOYEE_PASSWORD'):
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
                redirect(url_for('add_employee_account'))
        else:
            flash('Incorrect Admin Code')
            return redirect(url_for('add_employee_account'))
    return render_template('add_emp.html')

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
                    profile_type='admin'
                )
                db.session.add(new_user)
                
                db.session.commit()
                flash('Admin Account Created')
                return redirect(url_for('login'))
            except:
                db.session.rollback()
                traceback.print_exc()
                flash('Issue adding Admin account')
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
        body = f'''
        <h3>Welcome {first_name} {last_name}!</h3>
        <p>Thank you for registering with can2curb. Here are the details you provided:</p>
        <ul>
            <li><strong>Email:</strong> {email}</li>
            <li><strong>Phone Number:</strong> {phone_num}</li>
            <li><strong>Address:</strong> {house_num} {street_address}, {city}, {state}, {zipcode}</li>
            <li><strong>Trash Day:</strong> {trash_day}</li>
            <li><strong>Number of Cans:</strong> {num_cans}</li>
            <li><strong>Location:</strong> {location}</li>
            <li><strong>Gate/Garage Code:</strong> {gate_code}</li>
            <li><strong>Pet Information:</strong> {pet_info}</li>
            <li><strong>Notes:</strong> {notes}</li>
        </ul>
        <p>If any of this information is incorrect or needs to be changed, please reply to this email to let us know.</p>
        <p>Thank you!</p>
        <p>Jake Ellis<br>CEO/Founder Can2Curb</p>
        '''
        EMAILER.send_email(email, 'Account Information Confirmation', body=body)
        internal_body = f'''
        <h3>New Client Registration</h3>
        <p>A new client has registered with the following details:</p>
        <ul>
            <li><strong>First Name:</strong> {first_name}</li>
            <li><strong>Last Name:</strong> {last_name}</li>
            <li><strong>Email:</strong> {email}</li>
            <li><strong>Phone Number:</strong> {phone_num}</li>
            <li><strong>Address:</strong> {house_num} {street_address}, {city}, {state}, {zipcode}</li>
            <li><strong>Trash Day:</strong> {trash_day}</li>
            <li><strong>Number of Cans:</strong> {num_cans}</li>
            <li><strong>Location:</strong> {location}</li>
            <li><strong>Gate/Garage Code:</strong> {gate_code}</li>
            <li><strong>Pet Information:</strong> {pet_info}</li>
            <li><strong>Notes:</strong> {notes}</li>
        </ul>
        '''
        
        # Sending email to the internal team
        EMAILER.send_email('can2curbUT@gmail.com', 'NEW CLIENT', body=internal_body)
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
                if user.profile_type == 'admin' or user.profile_type == 'employee':
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
@login_required
@employee_only
def admin():
    title = 'Admin Home'
    addresses = Address.query.filter_by(in_route=False).all()
    return render_template('admin.html', title=title, addresses=addresses, current_user=current_user)

@app.route('/build-route', methods=['GET', 'POST'])
@login_required
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
                update = Address.query.filter_by(id=address).first()
                update.in_route = True
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

@app.route('/add_to_route/<address_id>', methods=['POST', 'GET'])
@login_required
@employee_only
def add_to_route(address_id):
    if request.method == 'POST':
        route_id = request.form.get('route')
        to_add = Route_Addresses(route_id=route_id, address_id=address_id)
        address = Address.query.filter_by(id=address_id).first()
        address.in_route = True
        db.session.add(to_add)
        db.session.commit()
        return redirect(url_for('admin'))
    else:
        address = Address.query.filter_by(id=address_id).first()
        all_routes = Route.query.all()
        return render_template('add_to_route.html', address=address, all_routes=all_routes, current_user=current_user)

@app.route('/assign_route/<route_id>', methods=['POST', 'GET'])
@login_required
@admin_only
def assign_route(route_id):
    if request.method == 'POST':
        route = Route.query.filter_by(id=route_id).first()
        employee_id = request.form.get('employee')
        employee = User.query.filter_by(id=employee_id).first()
        employee.active_route_id = route_id
        employee.active_route_addresses = json.dumps([address.id for address in route.addresses])
        db.session.commit()
        return redirect(url_for('view_routes'))
    else:
        route = Route.query.filter_by(id=route_id).first()
        employees = User.query.filter(User.profile_type != 'client').all()
        return render_template('assign_route.html', title='Assign Route', route=route, employees=employees, current_user=current_user)

@app.route('/active_route', methods=['POST', 'GET'])
@login_required
@employee_only
def active_route():
    route = Route.query.filter_by(id=current_user.active_route_id).first()
    address_ids = current_user.active_route_addresses_list
    addresses = Address.query.filter(Address.id.in_(address_ids)).all()
    return render_template('active_route.html', title='Active Route', route=route, addresses=addresses)

@app.route('/mark_complete/<address_id>', methods=['POST', 'GET'])
@login_required
@employee_only
def mark_complete(address_id):
    try:
        print("Initial active_route_addresses:", current_user.active_route_addresses)
        if current_user.active_route_addresses:
            existing_address_ids = json.loads(current_user.active_route_addresses)
        else:
            existing_address_ids = []

        existing_address_ids = [int(id) for id in existing_address_ids]

        updated_address_ids = [id for id in existing_address_ids if int(id) != int(address_id)]
        current_user.active_route_addresses = json.dumps(updated_address_ids)
        new_history = Service_History(address_id=address_id)
        db.session.add(new_history)
        db.session.commit()

        flash('Address marked complete', 'success')
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Issue marking complete', 'error': str(e)}), 500


@app.route('/edit_route/<route_id>', methods=['POST', 'GET'])
@login_required
@admin_only
def edit_route(route_id):
    if request.method == 'POST':
        try:
            route = Route.query.filter_by(id=route_id).first()
            name = request.form.get('route_name')
            day = request.form.get('trash_day')
            ids_before_edit = request.form.getlist('existing_ids')
            selected_addresses_ids = request.form.getlist('selected_addresses')

            if name != route.name and name != '':
                route.name = VALIDATOR.clean_input(name)
            if route.day != day and day is not None:
                route.day = day

            ids_to_remove = [id for id in ids_before_edit if id not in selected_addresses_ids]
            existing_ids = [id for id in selected_addresses_ids if id in ids_before_edit]
            new_ids = [id for id in selected_addresses_ids if id not in existing_ids and id not in ids_to_remove]
            for id in ids_to_remove:
                route_removed = Route_Addresses.query.filter_by(address_id=id, route_id=route_id).first()
                existing = Address.query.filter_by(id=route_removed.address_id).first()
                existing.in_route = False
                db.session.delete(route_removed)
            for id in new_ids:
                new_route = Route_Addresses(address_id = id, route_id = route_id)
                existing = Address.query.filter_by(id=id).first()
                existing.in_route = True
                db.session.add(new_route)
            db.session.commit()
            flash('Route updated successfully', 'success')
            return jsonify({'success': True}), 200
        except:
            db.session.rollback()
            traceback.print_exc()
            return jsonify({'success': False, 'message': 'Issue updating route'}), 500
    else:
        route = Route.query.filter_by(id=route_id).first()
        route_addresses_id_data = Route_Addresses.query.filter_by(route_id=route_id).all()
        address_ids = [ra.address_id for ra in route_addresses_id_data]
        route_addresses = Address.query.filter(Address.id.in_(address_ids)).all()
        addresses = Address.query.filter(~Address.id.in_(address_ids)).all()
        title = f'Edit Route: {route.name}'
        return render_template('edit_route.html', title=title, route=route, route_addresses=route_addresses, addresses=addresses, current_user=current_user)

@app.route('/delete_route/<route_id>', methods=['POST'])
@login_required
@admin_only
def delete_route(route_id):
    route = Route.query.filter_by(id=route_id).first()
    addresses = Route_Addresses.query.filter_by(route_id=route_id).all()
    for address in addresses:
        existing = Address.query.filter_by(id=address.address_id).first()
        existing.in_route = False
        db.session.delete(address)
    db.session.delete(route)
    db.session.commit()
    flash('Route Deleted Successfully')
    return redirect(url_for('view_routes'))

@app.route('/view-routes', methods=['GET'])
@login_required
@employee_only
def view_routes():
    all_routes = Route.query.all()
    title = 'View Routes'
    return render_template('view_routes.html', title=title, all_routes=all_routes)

@app.route('/view_route/<int:route_id>')
@login_required
@employee_only
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
@login_required
@employee_only
def view_customers():
    customers = User.query.filter_by(profile_type='client').all()
    title = 'View Customers'
    return render_template('view_customers.html', title=title, customers=customers, current_user=current_user)

@app.route('/view_customer/<customer_id>')
@login_required
@employee_only
def view_customer(customer_id):
    customer = User.query.filter_by(id=customer_id).first()
    title = f'View {customer.fname} {customer.lname}'
    return render_template('view_customer.html', title=title, customer=customer, current_user=current_user)

@app.route('/add_payment/<user_id>', methods=['POST', 'GET'])
@login_required
@employee_only
def add_payment(user_id):
    if request.method == 'POST':
        month = request.form.get('month')
        day = request.form.get('day')
        year = request.form.get('year')
        amount = request.form.get('amount')
        new_payment = Payment_History(user_id=user_id, day=day, month=month, year=year, amount=amount)
        db.session.add(new_payment)
        db.session.commit()
        return redirect(url_for('view_customer', customer_id=user_id))
    else:
        return render_template('add_payment.html', title='Add Payment', user_id=user_id, current_user=current_user)

@app.route('/add_address', methods=['POST', 'GET'])
@login_required
def add_address():
    if request.method == 'POST':
        user_id = request.form.get('customer_id')
        house_num = VALIDATOR.clean_input(request.form.get('houseNum'))
        street = VALIDATOR.clean_input(request.form.get('street'))
        city = VALIDATOR.clean_input(request.form.get('city'))
        state = VALIDATOR.clean_input(request.form.get('state'))
        zipcode = VALIDATOR.clean_input(request.form.get('zipcode'))
        trash_day = request.form.get('trash_day')
        num_cans = VALIDATOR.clean_input(request.form.get('number-of-cans'))
        location = VALIDATOR.clean_input(request.form.get('location'))
        gate_code = VALIDATOR.clean_input(request.form.get('gate-code'))
        pets = request.form.get('pets')
        notes = request.form.get('notes')
        new_address = Address(
            house_num=house_num,
            street_address=street,
            city=city,
            state=state,
            zip_code=zipcode,
            trash_day=trash_day,
            user_id=user_id
        )
        db.session.add(new_address)
        db.session.commit()

        new_trash_can = Trash_Can_Data(
            num_cans=num_cans, 
            location=location, 
            gate_garage_code=gate_code, 
            pet_info=pets, 
            notes=notes,
            address_id=new_address.id
        )
        db.session.add(new_trash_can)
        db.session.commit()
        return redirect(url_for('view_customer', customer_id=user_id))
    user_id = request.args.get('customer_id')
    return render_template('add_address.html', title='Add Address', customer_id=user_id, current_user=current_user)


@app.route('/edit_address/<address_id>', methods=['POST', 'GET'])
@login_required
def edit_address(address_id):
    title = 'Edit Address'
    address = Address.query.filter_by(id=address_id).first()
    trash_can = Trash_Can_Data.query.filter_by(address_id=address_id).first()
    next_url = request.args.get('next')
    if request.method == 'POST':
        try:
            origin = request.form.get('origin')
            house_num = VALIDATOR.clean_input(request.form.get('houseNum'))
            street = VALIDATOR.clean_input(request.form.get('street'))
            city = VALIDATOR.clean_input(request.form.get('city'))
            state = VALIDATOR.clean_input(request.form.get('state'))
            zipcode = VALIDATOR.clean_input(request.form.get('zipcode'))
            trash_day = request.form.get('trash_day')
            num_cans = VALIDATOR.clean_input(request.form.get('number-of-cans'))
            location = VALIDATOR.clean_input(request.form.get('location'))
            gate_code = VALIDATOR.clean_input(request.form.get('gate-code'))
            pets = request.form.get('pets')
            notes = request.form.get('notes')
            address.house_num = house_num
            address.street_address = street
            address.city = city
            address.state = state
            address.zipcode = zipcode
            if trash_day:
                address.trash_day = trash_day
            trash_can.num_cans = num_cans
            trash_can.location = location
            trash_can.gate_garage_code = gate_code
            if pets:
                trash_can.pet_info = VALIDATOR.clean_input(pets)
            if notes:
                trash_can.notes = VALIDATOR.clean_input(notes)
            db.session.commit()
            flash('Address Updated Successfully')
            return redirect(origin) if origin else redirect(url_for('admin'))
        except:
            traceback.print_exc()
            db.session.rollback()
    
    return render_template('edit_address.html', title=title, next=next_url, address=address, current_user=current_user)

@app.route('/delete_address/<address_id>', methods=['POST'])
@login_required
@admin_only
def delete_address(address_id):
    address = Address.query.filter_by(id=address_id).first()
    trash_can = Trash_Can_Data.query.filter_by(address_id=address_id).first()
    route_refs = Route_Addresses.query.filter_by(address_id=address_id).all()
    if address:
        db.session.delete(address)
    if trash_can:
        db.session.delete(trash_can)
    if route_refs:
        for route in route_refs:
            db.session.delete(route)
        
    db.session.commit()
    flash('Address Removed Successfully')
    
    next_url = request.form.get('next')
    return redirect(next_url) if next_url else redirect(url_for('admin'))

if __name__ == "__main__":
    app.run(host=runtime.app_host,port=runtime.app_port,debug=runtime.debug_on)
