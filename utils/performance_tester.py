import mysql.connector
from mysql.connector import Error
import pandas as pd
import time
import matplotlib.pyplot as plt
import numpy as np
import os
import random
from datetime import datetime, timedelta
from data_connect import create_connection, execute_read_query, get_db_config

class PerformanceTester:
    """Database performance testing class for finance manager system"""
    
    def __init__(self):
        """Initialize the performance tester"""
        self.results_folder = "performance_results"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure results folder exists
        if not os.path.exists(self.results_folder):
            os.makedirs(self.results_folder)
        
        # Dictionary to store test results
        self.test_results = {}
    
    def run_query_with_timer(self, query, params=None, iterations=5):
        """Run a query multiple times and measure its execution time"""
        connection = create_connection()
        if connection is not None:
            cursor = connection.cursor(dictionary=True)
            execution_times = []
            
            # Run the query multiple times to get average performance
            for i in range(iterations):
                start_time = time.time()
                try:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    
                    # Fetch results to simulate real usage
                    results = cursor.fetchall()
                except Error as e:
                    print(f"Error executing query: {e}")
                    connection.close()
                    return None
                    
                end_time = time.time()
                execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
                execution_times.append(execution_time)
                
                # Small pause between iterations
                time.sleep(0.1)
            
            connection.close()
            return {
                "min": min(execution_times),
                "max": max(execution_times),
                "avg": sum(execution_times) / len(execution_times),
                "median": sorted(execution_times)[len(execution_times) // 2],
                "all_times": execution_times
            }
        else:
            print("Cannot create database connection")
            return None
    
    def test_basic_queries(self):
        """Test performance of basic CRUD queries"""
        print("Testing basic CRUD queries...")
        
        # Test simple SELECT query
        select_query = "SELECT * FROM users WHERE user_id = %s"
        select_params = (1,)
        select_result = self.run_query_with_timer(select_query, select_params)
        self.test_results["basic_select"] = select_result
        
        # Test JOIN query
        join_query = """
        SELECT t.transaction_id, t.amount, t.transaction_date, c.name as category
        FROM transactions t
        JOIN categories c ON t.category_id = c.category_id
        WHERE t.user_id = %s
        LIMIT 100
        """
        join_params = (1,)
        join_result = self.run_query_with_timer(join_query, join_params)
        self.test_results["basic_join"] = join_result
        
        # Test GROUP BY query
        group_query = """
        SELECT c.name, COUNT(*) as count, SUM(t.amount) as total
        FROM transactions t
        JOIN categories c ON t.category_id = c.category_id
        WHERE t.user_id = %s
        GROUP BY c.name
        """
        group_params = (1,)
        group_result = self.run_query_with_timer(group_query, group_params)
        self.test_results["basic_group_by"] = group_result
        
        print("Basic query testing completed.")
    
    def test_complex_queries(self):
        """Test performance of complex analytical queries"""
        print("Testing complex analytical queries...")
        
        # Monthly trend analysis
        monthly_query = """
        SELECT 
            DATE_FORMAT(transaction_date, '%Y-%m') as month,
            SUM(CASE WHEN type = 1 THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN type = 2 THEN amount ELSE 0 END) as expense,
            SUM(CASE WHEN type = 1 THEN amount ELSE -amount END) as net
        FROM transactions
        WHERE user_id = %s AND transaction_date >= %s AND transaction_date <= %s
        GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')
        ORDER BY month
        """
        monthly_params = (1, "2020-01-01", "2025-12-31")
        monthly_result = self.run_query_with_timer(monthly_query, monthly_params)
        self.test_results["monthly_trend"] = monthly_result
        
        # Category distribution with subquery
        category_query = """
        SELECT 
            c.name as category_name,
            SUM(t.amount) as total_amount,
            (SUM(t.amount) / (
                SELECT SUM(amount) 
                FROM transactions 
                WHERE user_id = %s AND type = 2 AND transaction_date >= %s AND transaction_date <= %s
            )) * 100 as percentage
        FROM transactions t
        JOIN categories c ON t.category_id = c.category_id
        WHERE t.user_id = %s AND t.type = 2 AND t.transaction_date >= %s AND t.transaction_date <= %s
        GROUP BY c.name
        ORDER BY total_amount DESC
        """
        category_params = (1, "2020-01-01", "2025-12-31", 1, "2020-01-01", "2025-12-31")
        category_result = self.run_query_with_timer(category_query, category_params)
        self.test_results["category_distribution"] = category_result
        
        # Budget execution rate (complex join)
        budget_query = """
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
        budget_params = (1, "2025%")
        budget_result = self.run_query_with_timer(budget_query, budget_params)
        self.test_results["budget_execution"] = budget_result
        
        # View query performance
        view_query = """
        SELECT * FROM vw_transaction_details 
        WHERE user_id = %s AND year = %s 
        ORDER BY transaction_date DESC
        """
        view_params = (1, 2025)
        view_result = self.run_query_with_timer(view_query, view_params)
        self.test_results["view_query"] = view_result
        
        print("Complex query testing completed.")
    
    def test_index_effectiveness(self):
        """Test the effectiveness of indexes"""
        print("Testing index effectiveness...")
        
        # Query with indexed fields
        indexed_query = """
        SELECT * FROM transactions 
        WHERE user_id = %s AND transaction_date BETWEEN %s AND %s
        """
        indexed_params = (1, "2025-01-01", "2025-12-31")
        indexed_result = self.run_query_with_timer(indexed_query, indexed_params)
        self.test_results["indexed_query"] = indexed_result
        
        # Similar query with non-indexed fields
        non_indexed_query = """
        SELECT * FROM transactions 
        WHERE description LIKE %s
        """
        non_indexed_params = ("%payment%",)
        non_indexed_result = self.run_query_with_timer(non_indexed_query, non_indexed_params)
        self.test_results["non_indexed_query"] = non_indexed_result
        
        print("Index effectiveness testing completed.")
    
    def test_data_volume_impact(self):
        """Test impact of data volume on performance"""
        print("Testing data volume impact...")
        
        # Test with different LIMIT values
        volumes = [10, 100, 1000, 5000]
        for volume in volumes:
            query = f"""
            SELECT * FROM transactions 
            WHERE user_id = %s 
            ORDER BY transaction_date DESC
            LIMIT {volume}
            """
            params = (1,)
            result = self.run_query_with_timer(query, params)
            self.test_results[f"volume_{volume}"] = result
        
        print("Data volume impact testing completed.")
    
    def generate_performance_report(self):
        """Generate performance test report"""
        # Create DataFrame from results
        data = []
        for test_name, result in self.test_results.items():
            if result:
                data.append({
                    "Test": test_name,
                    "Min (ms)": round(result["min"], 2),
                    "Max (ms)": round(result["max"], 2),
                    "Avg (ms)": round(result["avg"], 2),
                    "Median (ms)": round(result["median"], 2)
                })
        
        df = pd.DataFrame(data)
        
        # Create bar chart of average execution times
        plt.figure(figsize=(12, 8))
        bars = plt.barh(df["Test"], df["Avg (ms)"], color='skyblue')
        plt.xlabel('Average Execution Time (ms)')
        plt.title

def save_report_to_csv(self, filepath):
    data = []
    for test_name, result in self.test_results.items():
        if result:
            data.append({
                "Test": test_name,
                "Min (ms)": round(result["min"], 2),
                "Max (ms)": round(result["max"], 2),
                "Avg (ms)": round(result["avg"], 2),
                "Median (ms)": round(result["median"], 2)
            })
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
