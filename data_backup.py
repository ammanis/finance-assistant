# Week 10

import mysql.connector
from mysql.connector import Error
import pandas as pd
import json
import csv
import os
from datetime import datetime
import zipfile
from data_connect import create_connection, execute_read_query, get_db_config

class DataBackupManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.backup_folder = f"backups/user_{user_id}"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure backup folder exists
        if not os.path.exists(self.backup_folder):
            os.makedirs(self.backup_folder)
    
    def backup_user_data(self, format="json"):
        """Backup all user data (user information, categories, transactions, budgets)"""
        try:
            # Get all relevant data
            user_data = self._get_user_data()
            categories = self._get_user_categories()
            transactions = self._get_user_transactions()
            budgets = self._get_user_budgets()
            
            # Create complete data object
            data = {
                "user": user_data,
                "categories": categories,
                "transactions": transactions,
                "budgets": budgets,
                "backup_time": self.timestamp,
                "backup_format_version": "1.0"
            }
            
            # Export data based on format
            if format.lower() == "json":
                return self._export_to_json(data)
            elif format.lower() == "csv":
                return self._export_to_csv(data)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            print(f"Error during backup process: {e}")
            return None
    
    def restore_from_backup(self, backup_path):
        """Restore user data from backup file"""
        try:
            # Check if file exists
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Determine processing method based on file extension
            if backup_path.endswith('.json'):
                with open(backup_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Validate data format and version
                if "backup_format_version" not in data:
                    raise ValueError("Invalid backup file format")
                
                # Perform restoration
                self._restore_data(data)
                return True
                
            elif backup_path.endswith('.zip'):
                # Process CSV backup zip file
                with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                    temp_dir = f"temp_restore_{self.timestamp}"
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)
                    zip_ref.extractall(temp_dir)
                    
                    # Read CSV files and convert to data object
                    data = self._read_csv_backup(temp_dir)
                    
                    # Perform restoration
                    self._restore_data(data)
                    
                    # Clean up temporary directory
                    for file in os.listdir(temp_dir):
                        os.remove(os.path.join(temp_dir, file))
                    os.rmdir(temp_dir)
                    
                    return True
            else:
                raise ValueError(f"Unsupported backup file format: {backup_path}")
                
        except Exception as e:
            print(f"Error during restoration process: {e}")
            return False
    
    def _get_user_data(self):
        """Get user basic information"""
        connection = create_connection()
        if connection is not None:
            query = """
            SELECT user_id, username, email, phone, create_time, status
            FROM users
            WHERE user_id = %s
            """
            params = (self.user_id,)
            result = execute_read_query(connection, query, params)
            connection.close()
            
            if result and len(result) > 0:
                return result[0]
            return None
        else:
            print("Cannot create database connection")
            return None
    
    def _get_user_categories(self):
        """Get user custom categories"""
        connection = create_connection()
        if connection is not None:
            query = """
            SELECT category_id, name, type, user_id
            FROM categories
            WHERE user_id = %s OR user_id IS NULL
            """
            params = (self.user_id,)
            result = execute_read_query(connection, query, params)
            connection.close()
            return result
        else:
            print("Cannot create database connection")
            return None
    
    def _get_user_transactions(self):
        """Get all user transactions"""
        connection = create_connection()
        if connection is not None:
            query = """
            SELECT 
                transaction_id, user_id, amount, type, category_id,
                payment_method, account_name, transaction_date, description,
                create_time, update_time
            FROM transactions
            WHERE user_id = %s
            """
            params = (self.user_id,)
            result = execute_read_query(connection, query, params)
            connection.close()
            
            # Convert dates to string format
            if result:
                for item in result:
                    if 'transaction_date' in item and item['transaction_date']:
                        item['transaction_date'] = item['transaction_date'].strftime('%Y-%m-%d')
                    if 'create_time' in item and item['create_time']:
                        item['create_time'] = item['create_time'].strftime('%Y-%m-%d %H:%M:%S')
                    if 'update_time' in item and item['update_time']:
                        item['update_time'] = item['update_time'].strftime('%Y-%m-%d %H:%M:%S')
            
            return result
        else:
            print("Cannot create database connection")
            return None
    
    def _get_user_budgets(self):
        """Get all user budget records"""
        connection = create_connection()
        if connection is not None:
            query = """
            SELECT 
                budget_id, user_id, budget_period, total_amount,
                create_time, update_time
            FROM budgets
            WHERE user_id = %s
            """
            params = (self.user_id,)
            result = execute_read_query(connection, query, params)
            connection.close()
            
            # Convert dates to string format
            if result:
                for item in result:
                    if 'create_time' in item and item['create_time']:
                        item['create_time'] = item['create_time'].strftime('%Y-%m-%d %H:%M:%S')
                    if 'update_time' in item and item['update_time']:
                        item['update_time'] = item['update_time'].strftime('%Y-%m-%d %H:%M:%S')
            
            return result
        else:
            print("Cannot create database connection")
            return None
    
    def _export_to_json(self, data):
        """Export data to JSON file"""
        file_path = os.path.join(self.backup_folder, f"backup_{self.timestamp}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Data backed up to: {file_path}")
        return file_path
    
    def _export_to_csv(self, data):
        """Export data to CSV files (multiple files packaged as zip)"""
        temp_folder = os.path.join(self.backup_folder, f"temp_{self.timestamp}")
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)
        
        # Export user information
        if data["user"]:
            user_file = os.path.join(temp_folder, "user.csv")
            with open(user_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data["user"].keys())
                writer.writeheader()
                writer.writerow(data["user"])
        
        # Export categories
        if data["categories"]:
            categories_file = os.path.join(temp_folder, "categories.csv")
            with open(categories_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data["categories"][0].keys())
                writer.writeheader()
                writer.writerows(data["categories"])
        
        # Export transactions
        if data["transactions"]:
            transactions_file = os.path.join(temp_folder, "transactions.csv")
            with open(transactions_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data["transactions"][0].keys())
                writer.writeheader()
                writer.writerows(data["transactions"])
        
        # Export budgets
        if data["budgets"]:
            budgets_file = os.path.join(temp_folder, "budgets.csv")
            with open(budgets_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data["budgets"][0].keys())
                writer.writeheader()
                writer.writerows(data["budgets"])
        
        # Create metadata file
        metadata_file = os.path.join(temp_folder, "metadata.csv")
        with open(metadata_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["backup_time", "backup_format_version"])
            writer.writerow([data["backup_time"], data["backup_format_version"]])
        
        # Package all files as zip
        zip_file = os.path.join(self.backup_folder, f"backup_{self.timestamp}.zip")
        with zipfile.ZipFile(zip_file, 'w') as zipf:
            for root, dirs, files in os.walk(temp_folder):
                for file in files:
                    zipf.write(os.path.join(root, file), file)
        
        # Clean up temporary files
        for file in os.listdir(temp_folder):
            os.remove(os.path.join(temp_folder, file))
        os.rmdir(temp_folder)
        
        print(f"Data backed up to: {zip_file}")
        return zip_file
    
    def _read_csv_backup(self, folder_path):
        """Read data from CSV backup folder"""
        data = {
            "backup_format_version": "1.0",
            "backup_time": self.timestamp
        }
        
        # Read metadata
        metadata_file = os.path.join(folder_path, "metadata.csv")
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                values = next(reader)
                data["backup_time"] = values[0]
                data["backup_format_version"] = values[1]
        
        # Read user information
        user_file = os.path.join(folder_path, "user.csv")
        if os.path.exists(user_file):
            with open(user_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data["user"] = row
                    break
        
        # Read categories
        categories_file = os.path.join(folder_path, "categories.csv")
        if os.path.exists(categories_file):
            data["categories"] = []
            with open(categories_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data["categories"].append(row)
        
        # Read transactions
        transactions_file = os.path.join(folder_path, "transactions.csv")
        if os.path.exists(transactions_file):
            data["transactions"] = []
            with open(transactions_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data["transactions"].append(row)
        
        # Read budgets
        budgets_file = os.path.join(folder_path, "budgets.csv")
        if os.path.exists(budgets_file):
            data["budgets"] = []
            with open(budgets_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data["budgets"].append(row)
        
        return data
    
    def _restore_data(self, data):
        """Restore data to database"""
        # Implement specific restoration logic here
        # Note: In actual implementation, need to carefully handle foreign key constraints and data conflicts
        print("Data restoration functionality is ready, but for data safety, actual restoration requires more detailed implementation")
        print(f"Data to be restored contains: {len(data.get('transactions', []))} transactions, {len(data.get('budgets', []))} budget records")
        return True

# Table partitioning optimization example code
def optimize_transactions_with_partition():
    """Implement transaction table partitioning by year"""
    connection = create_connection()
    if connection is not None:
        try:
            cursor = connection.cursor()
            
            # 1. Create temporary table (with partitioning)
            cursor.execute("""
            CREATE TABLE transactions_partitioned (
                transaction_id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Transaction ID',
                user_id INT NOT NULL COMMENT 'User ID',
                amount DECIMAL(12, 2) NOT NULL COMMENT 'Amount',
                type TINYINT NOT NULL COMMENT 'Type (1-income, 2-expense)',
                category_id INT NOT NULL COMMENT 'Category ID',
                payment_method VARCHAR(50) COMMENT 'Payment method',
                account_name VARCHAR(50) COMMENT 'Account name',
                transaction_date DATE NOT NULL COMMENT 'Transaction date',
                description VARCHAR(255) COMMENT 'Description',
                create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Create time',
                update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (category_id) REFERENCES categories (category_id)
            ) ENGINE = InnoDB 
            PARTITION BY RANGE (YEAR(transaction_date)) (
                PARTITION p2020 VALUES LESS THAN (2021),
                PARTITION p2021 VALUES LESS THAN (2022),
                PARTITION p2022 VALUES LESS THAN (2023),
                PARTITION p2023 VALUES LESS THAN (2024),
                PARTITION p2024 VALUES LESS THAN (2025),
                PARTITION p_future VALUES LESS THAN MAXVALUE
            );
            """)
            
            # 2. Copy data
            cursor.execute("""
            INSERT INTO transactions_partitioned
            SELECT * FROM transactions;
            """)
            
            # 3. Rename tables (backup original table)
            cursor.execute("""
            RENAME TABLE transactions TO transactions_old,
                         transactions_partitioned TO transactions;
            """)
            
            # 4. Add original indexes
            cursor.execute("""
            CREATE INDEX idx_user_date ON transactions(user_id, transaction_date);
            CREATE INDEX idx_type ON transactions(type);
            CREATE INDEX idx_category ON transactions(category_id);
            CREATE INDEX idx_payment ON transactions(payment_method);
            """)
            
            connection.commit()
            print("Transaction table partitioning optimization completed")
            
            # Can delete old table after testing confirms everything works
            # cursor.execute("DROP TABLE transactions_old;")
            # connection.commit()
            
        except Error as e:
            print(f"Table partitioning optimization error: {e}")
        finally:
            connection.close()
    else:
        print("Cannot create database connection")

# Simple usage example
if __name__ == "__main__":
    # Backup user data
    backup_manager = DataBackupManager(user_id=1)
    
    # JSON format backup
    json_backup = backup_manager.backup_user_data(format="json")
    print(f"JSON backup completed: {json_backup}")
    
    # CSV format backup
    csv_backup = backup_manager.backup_user_data(format="csv")
    print(f"CSV backup completed: {csv_backup}")
    
    # Restore from backup (example only, not actually performing restoration)
    if json_backup and os.path.exists(json_backup):
        print("Preparing to restore from JSON backup...")
        backup_manager.restore_from_backup(json_backup)
    
    # Table partitioning optimization (Note: This modifies database structure, please execute in test environment)
    # optimize_transactions_with_partition()