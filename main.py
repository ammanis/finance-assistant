# git add .
# git commit -m ""
# git push origin main
# git tag -a v1.0 -m ""
# git push origin v1.0
## current tag v2.2

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash # created hashed password
from datetime import datetime, timedelta # time, duh..
from pytz import timezone # convert UTC -> KST
from models import db, User, Transaction, Category # import from file models.py
from utils.budget_analysis import get_budget_vs_expense # import from file /utils/budget_analysis
from sqlalchemy import extract, text, func # text - for year API
from flask_cors import CORS
from collections import defaultdict
import calendar
from utils.budget_analysis import get_budget_vs_expense
from utils.analysis_tool import get_expense_by_category
from utils.performance_tester import PerformanceTester

import pytz # converting UTC -> KST

# for data_backup
from flask import send_file
from utils.data_backup import DataBackupManager

# for connecting AI w/ Flask
from pathlib import Path
import subprocess
import os

# for Scan routing 
from werkzeug.utils import secure_filename

# Document Scanner
from utils.document_scanner import process_uploaded_file
import time

app = Flask(__name__)
CORS(app, supports_credentials=True) # Access-Control-Allow-Origin ?
app.secret_key = 'your_secret_key'  # Change this to a secure key
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads') # for OCR connection

# Configuring SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/finance_manager' # mysql -u root -p
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False                                          # password: 1234
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

    # Making the 'Recent Transaction' at top for recent one
    # transactions = Transaction.query.filter_by(user_id=user.user_id).all()
    transactions = Transaction.query.filter_by(user_id=user.user_id).order_by(Transaction.date.desc()).all()

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

# Just showing camera
@app.route('/camera')
def camera():
    return render_template('camera.html')

# Subprocess the ocr
@app.route('/scan', methods=['POST'])
def scan():

    # Map Chinese OCR category to English
    CATEGORY_MAPPING = {
        "购物": "Shopping",
        "超市": "Groceries",
        "其他": "Others",
        "餐饮": "Dining"
    }

    # Check if user is logged in via session
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 401

     # Get user from DB
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        # Check if an image file is included in the request
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        # Get the uploaded image file and process it (scan + enhance + save)
        image_file = request.files['image']
        image_path = process_uploaded_file(image_file.stream)

        # Make sure the image was successfully saved
        if not os.path.exists(image_path):
            return jsonify({"error": f"Image file does not exist: {image_path}"}), 400
        
    except Exception as e:
        return jsonify({"error": f"Failed to scan image: {e}"}), 500

    # Setup OCR execution via external Python script
    OCR_PROJECT_DIR = Path(__file__).parent.parent / "flask-auth-ai" / "ocr_project"
    ocr_python = Path("C:/Users/ammar/anaconda3/envs/ocr_py311/python.exe")
    ocr_script = OCR_PROJECT_DIR / "main_ai.py"

    try:
        # Run external OCR script with subprocess
        result = subprocess.run(
            [str(ocr_python), str(ocr_script), "classify", str(image_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=False  # Don't raise exception, handle manually
        )
        # Check for error in stderr or stdout
        error_line = None
        for line in (result.stderr.strip() + '\n' + result.stdout.strip()).split('\n'):
            if line.startswith("ERROR|"):
                error_line = line
                break

        if error_line:
            # Extract error message after "ERROR|"
            error_msg = error_line.split('|', 1)[1] if '|' in error_line else error_line
            output = {"error": f"OCR failed: {error_msg}"}
        elif result.stdout:
            last_line = result.stdout.strip().split('\n')[-1]
            if last_line.startswith("ERROR|"):
                output = {"error": f"OCR failed: {last_line.split('|', 1)[1]}"}
            else:
                # Parse successful result (expected format: category|amount|merchant)
                parts = last_line.strip().split('|')
                if len(parts) == 3:
                    category, amount, merchant = parts
                    output = {"category": category, "amount": amount, "merchant": merchant}
                else:
                    output = {"error": "OCR output format error"}
        else:
            output = {"error": "OCR returned no output"}
    except Exception as e:
        output = {"error": f"OCR subprocess failed: {e}"}

    # # Insert transcation here..
    # if error indented, maybe bcs after 'if' statement, no space!

    # If OCR succeeded, store the transaction in the database
    if 'error' not in output:

        # After subprocess returns result
        category_cn = output['category']
        category_name = CATEGORY_MAPPING.get(category_cn, category_cn)  # fallback to original if unmapped
        output['category'] = category_name

        # Prepare fields for transaction
        category_name = output['category']
        try:
            amount = float(output['amount'])  # Ensure it's float
        except ValueError:
            return jsonify({"error": "Invalid amount format from OCR."}), 400

        # Prepare description (currently just the merchant)
        description_parts = []
        if 'merchant' in output:
            description_parts.append(f"Merchant: {output['merchant']}")

        # Add more fields like place/employee/foods if available
        # For now just use merchant
        description = ' | '.join(description_parts)

        trans_type = 'expense'  # Default assumption
        cat_type = 2  # Expense category type

        # Check if category exists (system default), else create it
        category = Category.query.filter_by(name=category_name, type=cat_type, user_id=None).first()
        if not category:
            category = Category(name=category_name, type=cat_type, user_id=None)
            db.session.add(category)
            db.session.commit()

        # Get current time in Korea
        kst = timezone('Asia/Seoul')
        now_kst = datetime.now(kst)

        # Create and insert transaction (expenses are stored as negative)
        new_trans = Transaction(
            amount=-amount,  # Expenses are stored as negative
            type=trans_type,
            category=category.name,
            category_id=category.category_id,
            description=description,
            user_id=user.user_id,
            date=now_kst
        )

        db.session.add(new_trans)
        db.session.commit()

        output["status"] = "Transaction added"

    return jsonify(output)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'username' not in session:
        return redirect(url_for('home'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return "User not found", 404

    amount = float(request.form.get('amount'))
    trans_type = request.form.get('type')  # 'income' or 'expense'
    category_name = request.form.get('category')
    description = request.form.get('description')

    cat_type = 1 if trans_type == 'income' else 2

    # Check if category exists (system preset), else create
    category = Category.query.filter_by(name=category_name, type=cat_type, user_id=None).first()
    if not category:
        category = Category(name=category_name, type=cat_type, user_id=None)
        db.session.add(category)
        db.session.commit()

    kst = timezone('Asia/Seoul')
    now_kst = datetime.now(kst)

    new_trans = Transaction(
        amount=amount if trans_type == 'income' else -amount,
        type=trans_type,
        category=category.name,
        category_id=category.category_id,
        description=description,
        user_id=user.user_id,
        date=now_kst
    )

    db.session.add(new_trans)
    db.session.commit()

    return redirect(url_for('homepage'))

# Category for printing in 'Recent Transactions'
@app.template_filter('category_emoji')
def category_emoji(category):
    emoji_map = {
        # Income
        'Salary': '💼',
        'Allowance': '💰',
        'Other Income': '🪙',
        # Expense
        'Groceries': '🛒',
        'Dining': '🍽️',
        'Transport': '🚌',
        'Bills': '🧾',
        'Rent': '🏠',
        'Healthcare': '💊',
        'Education': '📚',
        'Shopping': '🛍️',
        'Entertainment': '🎮',
        'Subscription': '🔄',
        'Travel': '✈️',
        'Gift': '🎁',
        'Insurance': '🛡️',
        'Others': '❓',
    }
    return emoji_map.get(category, '❔')


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

@app.route('/stats')
def stats():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('stats.html', username=session['username'])

@app.route('/stats/week')
def stats_week():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('stats_week.html', active_tab='week')

@app.route('/stats/month')
def stats_month():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('stats_month.html', active_tab='month')

@app.route('/stats/year')
def stats_year():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('stats_year.html', activate_tab='year')

# Logic to aggregate expense data by week/month/year
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

@app.route('/api/monthly-category-data')
def monthly_category_data():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Get current date and calc first day of current month
        today = datetime.today()
        start_of_month = today.replace(day=1)

        # Query user transactions only from this month + only expenses
        transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.date >= start_of_month,
            Transaction.amount < 0
        ).all()

        # Aggregate spending by category
        category_totals = {}
        for txn in transactions:
            category = txn.category or 'Uncategorized'
            category_totals[category] = category_totals.get(category, 0) + abs(txn.amount)

        # Prepare data for the chart
        response_data = {
            'categories': list(category_totals.keys()),
            'amounts': list(category_totals.values())
        }

        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/yearly-spending-data')
def yearly_spending_data():
    # print("👉 Entered yearly_spending_data route")
    user_id = session.get('user_id')
    # print("✅ user_id:", user_id)

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    try:
        result = db.session.execute(
            text("""
                SELECT YEAR(date) AS year, SUM(ABS(amount)) AS total
                FROM transactions
                WHERE user_id = :user_id
                GROUP BY year
                ORDER BY year
            """),
            {"user_id": user_id}
        )

        rows = result.fetchall()
        data = [{"year": row.year, "total": float(row.total)} for row in rows]

        # print("📦 Yearly data sent to frontend:", data)
        return jsonify(data)

    except Exception as e:
        # print("❌ Error in /api/yearly-spending-data:", str(e))
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/category-breakdown')
def category_breakdown():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401

        mode = request.args.get('mode', 'week')
        now = datetime.now(timezone('Asia/Seoul'))

        query = Transaction.query.filter_by(user_id=user_id, type='expense')

        if mode == 'week':
            start = now - timedelta(days=now.weekday())  # start of this week (Monday)
            query = query.filter(Transaction.date >= start)
        elif mode == 'month':
            query = query.filter(
                extract('year', Transaction.date) == now.year,
                extract('month', Transaction.date) == now.month
            )
        elif mode == 'year':
            query = query.filter(
                extract('year', Transaction.date) == now.year
            )

        results = query.with_entities(Transaction.category, func.sum(Transaction.amount)).group_by(Transaction.category).all()

        category_spending = {cat: round(abs(total), 2) for cat, total in results}

        return jsonify({'categories': category_spending})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/budget_vs_expense')
def budget_vs_expense():
    user_id = request.args.get('user_id', type=int)
    period = request.args.get('period')  # e.g., "2024=04"
    
    if not user_id or not period:
        return jsonify({'error': 'Missing user_id or period'}), 400
    
    result = get_budget_vs_expense(user_id, period)
    
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'No data found'}), 404
    
@app.route('/expense_by_category')
def expense_by_category():
    user_id = request.args.get('user_id', type=int)
    start_date = request.args.get('start_date')  # e.g., "2024-01-01"
    end_date = request.args.get('end_date')      # e.g., "2024-12-31"
    
    if not user_id or not start_date or not end_date:
        return jsonify({'error': 'Missing parameters'}), 400
    
    data = get_expense_by_category(user_id, start_date, end_date)
    return jsonify(data)

@app.route('/download-performance-report')
def download_performance_report():
    tester = PerformanceTester()
    tester.test_basic_queries()
    tester.generate_performance_report()
    filename = os.path.join(tester.results_folder, f'performance_report_{tester.timestamp}.csv')
    tester.save_report_to_csv(filename)  # You'll need to add this method
    return send_file(filename, as_attachment=True)

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

@app.route('/backup/json/<int:user_id>')
def backup_json(user_id):
    backup = DataBackupManager(user_id)
    path = backup.backup_user_data(format='json')
    if path:
        return send_file(path, as_attachment=True)
    return "Backup failed", 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)