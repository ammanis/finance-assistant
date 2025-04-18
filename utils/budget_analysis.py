from sqlalchemy import func, extract
from models import db, Budget, Transaction

def get_budget_vs_expense(user_id, period):
    year,month = map(int, period.split("=")) #"2024-04"

    # SQLAlchemy query to calculate:
    # - actual expense: total of expense transaction in the given month
    # - budget amount: from the user's Budget table for the same month
    # - remaining budget: budget - actual expense
    query = (
        db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0).label("actual_expense"), # Handle null values as 0
            Budget.total_amount.label("budget_amount"),
            (Budget.total_amount - func.coalesce(func.sum(Transaction.amount), 0)).label("remaining_budget")
        )
        .leftjoin(Transaction,
                  (Transaction.user_id == Budget.user_id) & # Join only transaction by the same user
                  (Transaction.type == 2) & # Only consier expense (type 2) 
                  (extract("year", Transaction.transaction_date) == year) & # Match the year
                  (extract("month", Transaction.transaction_date) == month)) # Match the month
        .filter(
            Budget.user_id == user_id, 
            Budget.budget_period == period) # Ensure budget entry is for the requested period
        .group_by(Budget.budget_id, Budget.total_amount) # Required bcs of aggregation functions
        .first() # Only fetch the first result (each user should only have one budget per month)
    )
    if query: # If we have a result, convert data to float and return in dictionary format
        return{
            "budget_amount": float(query.budget_amount),
            "actual_expense": float(query.actual_expense),
            "remaining_budget": float(query.remaining_budget)
        }
    return None #If no data found