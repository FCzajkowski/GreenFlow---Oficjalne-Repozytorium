from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, Item, Order
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_mail import Mail, Message
from datetime import datetime
"""
main root: 

"""


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600  # Recycle connections after 1 hour
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30  # Timeout for obtaining a connection


mail = Mail(app)

db.init_app(app)

from functools import wraps

def retry_on_disconnect(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        for _ in range(max_retries):
            try:
                return func(*args, **kwargs)
            except OperationalError:
                time.sleep(2)  # Wait before retrying
        return None  # Or handle the failure gracefully
    return wrapper

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
import time
from sqlalchemy.exc import OperationalError

with app.app_context():
    db.create_all()
    item_count = Item.query.count()

item_c = item_count

def retry_on_disconnect(func):
    def wrapper(*args, **kwargs):
        max_retries = 3
        for _ in range(max_retries):
            try:
                return func(*args, **kwargs)
            except OperationalError:
                time.sleep(2)  # Wait before retrying
        return None  # Or handle the failure gracefully
    return wrapper

@app.route('/search')
def search():
    user_email = session.get('user_email')
    category = request.args.get('category')
    search_term = request.args.get('search_term')

    # Start the query, filtering by category first if provided
    query = Item.query
    if category:
        query = query.filter_by(category=category)  # Filter by selected category
    if search_term:
        query = query.filter(Item.title.ilike(f'%{search_term}%'))  # Filter within the category by search term

    items = query.all()
    return render_template('search.html', user_email=user_email, items=items)


@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    user_email = session.get('user_email')
    return render_template('index.html', user_email=user_email)

@app.route('/about')
def about():
    return render_template('about.html')



@app.route('/profile')
def profile():
    user_email = session.get('user_email')
    if not user_email:
        flash("Please log in to access your profile.", "danger")
        return redirect(url_for('form'))
    return render_template('profile.html', user_email=user_email)
@app.route('/change_email', methods=['POST'])
def change_email():
    user_email = session.get('user_email')
    new_email = request.form.get('new_email')

    user = User.query.filter_by(email=user_email).first()
    if user:
        user.email = new_email
        db.session.commit()
        session['user_email'] = new_email
        flash('Email updated successfully!', 'success')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('profile'))

@app.route('/change_password', methods=['POST'])
def change_password():
    user_email = session.get('user_email')
    new_password = request.form.get('new_password')
    hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')

    user = User.query.filter_by(email=user_email).first()
    if user:
        user.password = hashed_password
        db.session.commit()
        flash('Password updated successfully!', 'success')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('profile'))



@app.route('/registration', methods=['GET', 'POST'])
def registrate():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')


        # Check if the user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:

            flash('User already exists. Please log in or use a different email.', 'danger')
            return redirect(url_for('form'))  # Redirect to the login form

        # Create a new user with hashed password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        print("new user added!")

        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('form'))  # Redirect to the login form

    return render_template('registrate.html')


@app.route('/add_item', methods=['POST', 'GET'])
def add_item():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        pickup_location = request.form['pickup_location']  # New field
        contact_phone = request.form['contact_phone']      # New field
        author = session.get('user_email')  # Get logged-in user's email

        # Ensure user is logged in
        if author is None:
            flash("You must be logged in to add an item.")
            return redirect(url_for('form'))

        # Check if an image file was uploaded
        if 'image' not in request.files:
            flash('No image part in the form.', 'danger')
            return redirect(request.url)

        file = request.files['image']

        # Check if a valid file was uploaded
        if file.filename == '':
            flash('No selected file.', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            flash('Invalid file type. Allowed types: png, jpg, jpeg, gif.', 'danger')
            return redirect(request.url)

        # Create and add new item to the database
        new_item = Item(
            title=title,
            description=description,
            image=filename,
            author=author,
            category=category,
            pickup_location=pickup_location,  # Save pickup location
            contact_phone=contact_phone       # Save contact phone
        )
        db.session.add(new_item)
        db.session.commit()

        flash('Item added successfully!', 'success')
        return redirect(url_for('search'))  # Redirect to the item list

    return render_template('add_item.html')



@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the user exists and verify password
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_email'] = user.email
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
            return redirect(url_for('form'))

    return render_template('form.html')

@app.route('/order/<int:item_id>')
def order_item(item_id):
    item = Item.query.get(item_id)  # Fetch item from the database
    if item is None:
        return "Item not found", 404
    user_email = session.get('user_email')
    if not user_email:
        flash("Please log in to access your profile.", "danger")
        return redirect(url_for('form'))
    return render_template('order.html', item=item)
@app.route('/orders')
def orders():
    user_email = session.get('user_email')
    if not user_email:
        flash("You must be logged in to view your orders.", "danger")
        return redirect(url_for('form'))

    orders = Order.query.filter_by(seller_email=user_email, status='pending').all()
    return render_template('orders.html', orders=orders)
@app.route('/complete_order/<int:item_id>', methods=['POST'])
def complete_order(item_id):
    item = Item.query.get(item_id)
    if item is None:
        return "Item not found", 404

    buyer_email = session.get('user_email')
    if not buyer_email:
        flash("You must be logged in to place an order.", "danger")
        return redirect(url_for('form'))

    # Create a new order with status 'pending'
    order = Order(item_id=item.id, buyer_email=buyer_email, seller_email=item.author, status='pending')
    db.session.add(order)
    db.session.commit()

    flash('Your order has been placed! Waiting for the seller to accept.', 'success')

    return redirect(url_for('order_confirmation', item_id=item.id))


@app.route('/update_order/<int:order_id>/<string:action>', methods=['POST'])
def update_order(order_id, action):
    # Fetch the order from the database
    order = Order.query.get(order_id)

    if not order:
        # Handle the case where the order doesn't exist
        flash("Order not found.", "error")
        return redirect(url_for('orders'))

    if action == 'accept':
        # Fetch the associated item if you need to delete it
        item = Item.query.get(order.item_id)

        # Delete the order first
        db.session.delete(order)

        # Optionally delete the associated item
        if item:
            db.session.delete(item)

        db.session.commit()
        flash("Order accepted and removed from the list.", "success")
    elif action == 'decline':
        # Update the order status if declined, without deleting it
        order.status = 'declined'
        db.session.commit()
        flash("Order declined.", "info")

    return redirect(url_for('orders'))


@app.route('/item/<int:item_id>')
def item(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('item.html', item=item)

@app.route('/order_confirmation/<int:item_id>')
def order_confirmation(item_id):
    item = Item.query.get(item_id)
    if item is None:
        return "Item not found", 404
    return render_template('order_confirmation.html', item=item)
app.route('/logout')
@app.route('/logout')
def logout():
    # Logic to log the user out, e.g., session.clear()
    session.clear()  # Clear the session if using sessions for login
    return redirect(url_for('home'))  # Redirect to the homepage or login page
if __name__ == '__main__':
    app.run(debug=True)