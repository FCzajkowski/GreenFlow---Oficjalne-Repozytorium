from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()
class User(db.Model):
    __table_args__ = {'extend_existing': True}  # Allow extension of the existing table
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
class Item(db.Model):
    __table_args__ = {'extend_existing': True}  # Allow extension of the existing table
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Inne')
    pickup_location = db.Column(db.String, nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
class Order(db.Model):
    __table_args__ = {'extend_existing': True}  # Allow extension of the existing table
    __tablename__ = 'order'  # Custom table name to avoid SQL reserved word issues
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    buyer_email = db.Column(db.String(120), nullable=False)
    seller_email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(50), default='pending')
    order_date = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship('Item', backref='orders')
