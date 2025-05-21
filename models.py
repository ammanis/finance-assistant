from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'  # Make sure this matches your SQL table name
    user_id = db.Column(db.Integer, primary_key=True)  # Ensure this is 'user_id'
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.SmallInteger, default=1) # yup, cannot use db.TinyInteger here (used in MySQL LIU did)
    initial_income = db.Column(db.Float, default=0.0) # to set initial income

    # Transactions relationship
    transactions = db.relationship('Transaction', backref='user', lazy=True)

    def set_password(self, password): # stored hash password
        self.password_hash = generate_password_hash(password)

    def check_password(self, password_hash): # verify the hash password
        return check_password_hash(self.password_hash, password_hash)

class Category(db.Model):
    __tablename__ = 'categories'  # Make sure this matches the table name in your SQL schema
    category_id = db.Column(db.Integer, primary_key=True)  # This should be 'category_id'
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)

    # Relationship to transactions
    transactions = db.relationship('Transaction', backref='transaction_category', lazy=True)

class Transaction(db.Model):
    __tablename__ = 'transactions'  # This should match your SQL table name
    transaction_id = db.Column(db.Integer, primary_key=True)  # Ensure this is 'transaction_id'
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign key to user and category
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # Match the foreign key
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'), nullable=True)

class Budget(db.Model):
    __tablename__ = 'budgets'
    budget_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    budget_period = db.Column(db.String(50), nullable=False)  # e.g., "2023-06"
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Ensure that user_id and budget_period are unique together
    __table_args__ = (db.UniqueConstraint('user_id', 'budget_period', name='unique_user_budget_period'),)