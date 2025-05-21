import mysql.connector
from mysql.connector import Error
import pandas as pd

# Database connection configuration file
def get_db_config():
    return {
        'host': 'localhost',
        'database': 'finance_manager',
        'user': 'root',  # Please change to actual username
        'password': 'root',  # Please change to actual password
        'port': 3306
    }

# Create database connection
def create_connection():
    connection = None
    try:
        config = get_db_config()
        connection = mysql.connector.connect(**config)
        print("Successfully connected to MySQL database")
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

# Execute query
def execute_query(connection, query, params=None):
    cursor = connection.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        connection.commit()
        print("Query executed successfully")
        return cursor
    except Error as e:
        print(f"Error executing query: {e}")
        return None

# Get query results
def execute_read_query(connection, query, params=None):
    cursor = connection.cursor(dictionary=True)
    result = None
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"Error executing query: {e}")
        return None