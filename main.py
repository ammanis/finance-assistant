from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash # created hashed password
from datetime import datetime, timedelta # time, duh..
from pytz import timezone # convert UTC -> KST
from models import db, User, Transaction # import from file models.py
from utils.budget_analysis import get_budget_vs_expense # import from file /utils/budget_analysis
from sqlalchemy import extract
from flask_cors import CORS
from collections import defaultdict
import calendar
import pytz # converting UTC -> KST

app = Flask(__name__)
CORS(app, supports_credentials=True) # Access-Control-Allow-Origin ?
app.secret_key = 'your_secret_key'  # Change this to a secure key

# Configuring SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/finance_manager' # mysql -u root -p
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False                                          # password: root
db.init_app(app)                                                                              # USE finance_manager;          

@app.route('/')
def home():
    """Redirects logged-in users to man.html, otherwise shows index.html"""
    if 'username' in session:
        return redirect(url_for('homepage'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    """Confirms username and password in the database"""
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password): # the line where to check hash password
        session['username'] = username
        session['user_id'] = user.user_id
        session.modified = True  # Ensure session is updated
        return redirect(url_for('homepage'))
    else:
        return render_template('index.html', error='Invalid username or password.')

@app.route('/register', methods=['POST'])
def register():
    """Registers a new user in the database"""
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    
    if user:
        return render_template('index.html', error='Username already exists.')
    else:
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        session.modified = True  # Ensure session is updated
        return redirect(url_for('homepage'))

@app.route('/homepage')
def homepage():
    """Displays the finance assistant homepage (homepage.html)"""
    if 'username' not in session:
        return redirect(url_for('home'))
    user = User.query.filter_by(username=session['username']).first()

    # if shows this, just write URL .../logout
    if not user:
            return "User not found", 404

    transactions = Transaction.query.filter_by(user_id=user.user_id).all()

    total_income = sum(t.amount for t in transactions if t.amount >0)
    total_expense = sum(t.amount for t in transactions if t.amount < 0)

    #balance = user.initial_income + total_income - total_expense ## why this code is useless, bcs 'total_expense' is -ve value..
    balance = user.initial_income + total_income + total_expense

    return render_template('homepage.html', username=session['username'],
                            transactions=transactions,
                            total_income = total_income,
                            total_expense=abs(total_expense),
                            balance=balance,
                            user=user)

@app.route('/camera')
def camera():
    return render_template('camera.html')

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'username' not in session:
        return redirect(url_for('home'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return "User not found", 404

    amount = float(request.form.get('amount'))
    trans_type = request.form.get('type')
    category = request.form.get('category')
    description = request.form.get('description')

    # Convert UTC to KST
    kst = timezone('Asia/Seoul')
    now_kst = datetime.now(kst)

    new_trans = Transaction(
        amount=amount if trans_type == 'income' else -amount,
        type=trans_type,
        category=category,
        description=description,
        user_id=user.user_id,
        date = now_kst # <-- save KST time here
    )

    db.session.add(new_trans)
    db.session.commit()

    return redirect(url_for('homepage'))

@app.route("/clear_transactions", methods=['POST'])
def clear_transactions():
    if 'username' not in session:
        return redirect(url_for('home'))
    user = User.query.filter_by(username=session['username']).first()
    if user:
        Transaction.query.filter_by(user_id=user.user_id).delete()
        db.session.commit()
    return redirect(url_for('homepage'))    

@app.route('/set_income', methods=['POST'])
def set_income():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return "User not found", 404
    
    user.initial_income = float(request.form.get('initial_income'))
    db.session.commit()

    return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    """Logs out the user"""
    session.pop('username', None)
    return redirect(url_for('home'))

# Routes for Different Pages
@app.route('/stats')
def stats():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('stats.html', username=session['username'])

from datetime import datetime, timedelta

from datetime import datetime, timedelta

from datetime import datetime, timedelta

from datetime import datetime, timedelta
import pytz

@app.route('/api/weekly-spending-data')
def weekly_spending_data():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401

        transactions = Transaction.query.filter_by(user_id=user_id).all()

        # Set up timezone (KST)
        kst = pytz.timezone('Asia/Seoul')
        today_kst = datetime.now(kst)

        # Start of this week (Monday) in KST
        start_of_week_kst = today_kst.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=today_kst.weekday())

        # Days labels for the chart
        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        weekly_spending = {day: 0 for day in days_of_week}

        for t in transactions:
            if t.amount < 0:
                tx_time = t.date

                # Make sure it's timezone-aware
                if tx_time.tzinfo is None:
                    tx_time = pytz.utc.localize(tx_time).astimezone(kst)
                else:
                    tx_time = tx_time.astimezone(kst)

                # Calculate which day of the week (Mon-Sun) this falls into
                delta_days = (tx_time.date() - start_of_week_kst.date()).days

                if 0 <= delta_days < 7:
                    weekday_index = tx_time.weekday()  # 0 = Mon, 6 = Sun
                    day_name = days_of_week[weekday_index]
                    weekly_spending[day_name] += abs(t.amount)

        return jsonify({
            'days': days_of_week,
            'spending': [weekly_spending[day] for day in days_of_week]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/category-breakdown')
def category_breakdown():
    try:
        user_id = session.get('user_id')
        print(f"[DEBUG] Session user_id: {user_id}")
        
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        
        transactions = Transaction.query.filter_by(user_id=user_id).all()
        print(f"[DEBUG] Found {len(transactions)} transactions")
        
        # Dictionary to store category-wise spending
        category_spending = {}
        
        # Iterate over all transactions to group by category
        for t in transactions:
            if t.amount < 0:  # Only considering expenses (negative amounts)
                if t.category not in category_spending:
                    category_spending[t.category] = 0
                category_spending[t.category] += abs(t.amount)
        
        # Prepare the data to be returned
        response_data = {
            'categories': category_spending
        }

        print(f"[DEBUG] Category breakdown data: {response_data}")
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"[ERROR] /api/category-breakdown failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/budget_analysis')
def budget_analysis():
    # Ensure user logged in
    if 'username' not in session:
        return redirect(url_for('home'))
    
    user=User.query.filter_by(username=session['username']).first() # Get data from database
    current_month = datetime.now().strftime('%Y-%m') # Get current month, to match budget_period format
    # Call core analysis fx to compare user's budget & expenses
    analysis = get_budget_vs_expense(user.user_id, current_month) # Use raw SQL and joins budgets and transactions
    return render_template('budget_analysis.html', data=analysis)

@app.route('/ai')
def ai():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('ai.html', username=session['username'])

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    # Get the user object from database
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return "User not found", 404
    
    # Get this user's transactions
    transactions = Transaction.query.filter_by(user_id=user.user_id).all()

    total_income = user.initial_income + sum(t.amount for t in transactions if t.amount >0)
    total_expense = sum(t.amount for t in transactions if t.amount < 0)
    return render_template('profile.html', username=session['username'],
                           total_income=total_income,
                           total_expense=abs(total_expense),
                           user=user) # abs() so not -ve

@app.template_filter('format_won')
def format_won(value):
    """Formats number with commas for Korean Won"""
    return "{:,}".format(value)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
