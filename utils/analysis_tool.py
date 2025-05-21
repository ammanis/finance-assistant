# Week 9

import mysql.connector
from mysql.connector import Error
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import calendar
from data_connect import create_connection, execute_read_query, get_db_config

# Statistics by category for user expenses
def get_expense_by_category(user_id, start_date, end_date):
    connection = create_connection()
    if connection is not None:
        query = """
        SELECT c.name as category_name, SUM(t.amount) as total_amount
        FROM transactions t 
        JOIN categories c ON t.category_id = c.category_id
        WHERE t.user_id = %s AND t.type = 2 
              AND t.transaction_date BETWEEN %s AND %s
        GROUP BY c.name
        ORDER BY total_amount DESC
        """
        params = (user_id, start_date, end_date)
        result = execute_read_query(connection, query, params)
        connection.close()
        return result
    else:
        print("Cannot create database connection")
        return None

# Monthly income and expense trends
def get_monthly_summary(user_id, year):
    connection = create_connection()
    if connection is not None:
        query = """
        SELECT 
            DATE_FORMAT(transaction_date, '%Y-%m') as month,
            SUM(CASE WHEN type = 1 THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN type = 2 THEN amount ELSE 0 END) as expense,
            SUM(CASE WHEN type = 1 THEN amount ELSE -amount END) as net
        FROM transactions
        WHERE user_id = %s AND YEAR(transaction_date) = %s
        GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')
        ORDER BY month
        """
        params = (user_id, year)
        result = execute_read_query(connection, query, params)
        connection.close()
        return result
    else:
        print("Cannot create database connection")
        return None

# Budget execution rate analysis (monthly)
def get_budget_execution_rate(user_id, year):
    connection = create_connection()
    if connection is not None:
        query = """
        SELECT 
            b.budget_period,
            b.total_amount as budget_amount,
            COALESCE(SUM(t.amount), 0) as actual_expense,
            CASE 
                WHEN b.total_amount > 0 THEN 
                    ROUND((COALESCE(SUM(t.amount), 0) / b.total_amount) * 100, 2)
                ELSE 0 
            END as execution_rate
        FROM budgets b
        LEFT JOIN transactions t ON b.user_id = t.user_id 
                              AND t.type = 2 
                              AND DATE_FORMAT(t.transaction_date, '%Y-%m') = b.budget_period
        WHERE b.user_id = %s AND b.budget_period LIKE %s
        GROUP BY b.budget_id, b.budget_period, b.total_amount
        ORDER BY b.budget_period
        """
        params = (user_id, f"{year}%")
        result = execute_read_query(connection, query, params)
        connection.close()
        return result
    else:
        print("Cannot create database connection")
        return None

# User spending habits analysis (by day of week)
def get_spending_habits(user_id, months=3):
    connection = create_connection()
    if connection is not None:
        # Calculate start date for the past few months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30*months)
        
        # Query by day of week
        query_weekday = """
        SELECT 
            DAYOFWEEK(transaction_date) as weekday,
            SUM(amount) as total_amount,
            COUNT(*) as transaction_count
        FROM transactions
        WHERE user_id = %s AND type = 2 
              AND transaction_date BETWEEN %s AND %s
        GROUP BY DAYOFWEEK(transaction_date)
        ORDER BY weekday
        """
        
        params = (user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        weekday_result = execute_read_query(connection, query_weekday, params)
        
        # Convert numeric weekday to name
        weekday_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        if weekday_result:
            for item in weekday_result:
                item['weekday_name'] = weekday_names[item['weekday']-1]
        
        connection.close()
        return weekday_result
    else:
        print("Cannot create database connection")
        return None

# Income source analysis
def get_income_sources(user_id, year):
    connection = create_connection()
    if connection is not None:
        query = """
        SELECT 
            c.name as category_name,
            SUM(t.amount) as total_amount,
            COUNT(*) as transaction_count,
            ROUND(AVG(t.amount), 2) as average_amount
        FROM transactions t
        JOIN categories c ON t.category_id = c.category_id
        WHERE t.user_id = %s AND t.type = 1 AND YEAR(t.transaction_date) = %s
        GROUP BY c.name
        ORDER BY total_amount DESC
        """
        params = (user_id, year)
        result = execute_read_query(connection, query, params)
        connection.close()
        return result
    else:
        print("Cannot create database connection")
        return None

# Visualize monthly trends
def visualize_monthly_trend(user_id, year):
    data = get_monthly_summary(user_id, year)
    if data and len(data) > 0:
        df = pd.DataFrame(data)
        
        # Create chart
        plt.figure(figsize=(12, 6))
        plt.plot(df['month'], df['income'], marker='o', linewidth=2, label='Income')
        plt.plot(df['month'], df['expense'], marker='o', linewidth=2, label='Expense')
        plt.plot(df['month'], df['net'], marker='o', linewidth=2, label='Net Income')
        
        plt.title(f'Monthly Financial Trends for {year}')
        plt.xlabel('Month')
        plt.ylabel('Amount')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        
        # Save chart
        plt.savefig(f'monthly_trend_{user_id}_{year}.png')
        plt.close()
        
        return f'monthly_trend_{user_id}_{year}.png'
    return None

# Example execution
if __name__ == "__main__":
    user_id = 1
    current_year = datetime.now().year
    
    # Expense by category
    print("===== Expenses by Category =====")
    start_date = f"{current_year}-01-01"
    end_date = f"{current_year}-12-31"
    expenses = get_expense_by_category(user_id, start_date, end_date)
    if expenses:
        for expense in expenses:
            print(f"Category: {expense['category_name']}, Total Amount: {expense['total_amount']}")
    
    # Monthly summary
    print("\n===== Monthly Financial Summary =====")
    monthly_data = get_monthly_summary(user_id, current_year)
    if monthly_data:
        for month in monthly_data:
            print(f"Month: {month['month']}, Income: {month['income']}, Expense: {month['expense']}, Net: {month['net']}")
    
    # Budget execution rate
    print("\n===== Budget Execution Rate =====")
    budget_execution = get_budget_execution_rate(user_id, current_year)
    if budget_execution:
        for budget in budget_execution:
            print(f"Period: {budget['budget_period']}, Budget: {budget['budget_amount']}, Actual Expense: {budget['actual_expense']}, Execution Rate: {budget['execution_rate']}%")
    
    # Spending habits analysis
    print("\n===== Spending Habits by Day of Week =====")
    habits = get_spending_habits(user_id)
    if habits:
        for habit in habits:
            print(f"{habit['weekday_name']}: {habit['transaction_count']} transactions, Total: {habit['total_amount']}")
    
    # Income sources analysis
    print("\n===== Income Sources Analysis =====")
    incomes = get_income_sources(user_id, current_year)
    if incomes:
        for income in incomes:
            print(f"Source: {income['category_name']}, Total: {income['total_amount']}, Average: {income['average_amount']}, Count: {income['transaction_count']}")
    
    # Visualize monthly trend
    chart_path = visualize_monthly_trend(user_id, current_year)
    if chart_path:
        print(f"\nMonthly trend chart saved as: {chart_path}")