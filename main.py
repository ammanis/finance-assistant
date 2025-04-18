from flask import Flask, render_template, request, redirect, url_for, session # move from 1 page to other pages
from werkzeug.security import generate_password_hash, check_password_hash # security?
from datetime import datetime # time, duh..
from pytz import timezone # convert UTC -> KST
from models import db, User, Transaction # import from file models.py
from utils.budget_analysis import get_budget_vs_expense # import from file /utils/budget_analysis

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure key

# Configuring SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/finance_manager'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

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

@app.route('/budget_analysis')
def budget_analysis():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    user=User.query.filter_by(username=session['username']).first()
    current_month = datetime.now().strftime('%Y-%m')
    analysis = get_budget_vs_expense(user.id, current_month)
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
