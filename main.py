from flask import Flask, render_template, request, redirect, url_for, session # move from 1 page to other pages
from werkzeug.security import generate_password_hash, check_password_hash # security?
from models import db, User, Transaction # import from file models.py
from datetime import datetime # time, duh..
from pytz import timezone # convert UTC -> KST

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
    
    if user and user.check_password(password):
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

    transactions = Transaction.query.filter_by(user_id=user.user_id).order_by(Transaction.date.desc()).all()
    return render_template('homepage.html', username=session['username'], transactions=transactions)

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

@app.route('/ai')
def ai():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('ai.html', username=session['username'])

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('profile.html', username=session['username'])


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
