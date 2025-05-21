DROP DATABASE IF EXISTS finance_manager;

-- Create database
CREATE DATABASE IF NOT EXISTS finance_manager DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

-- Use the database
USE finance_manager;

-- Users table
CREATE TABLE users (
  user_id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'User ID',
  username VARCHAR(150) NOT NULL UNIQUE COMMENT 'Username',
  password_hash VARCHAR(255) NOT NULL COMMENT 'Password (encrypted)',
  email VARCHAR(100) UNIQUE COMMENT 'Email address',
  phone VARCHAR(20) COMMENT 'Phone number',
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Create time',
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
  status SMALLINT NOT NULL DEFAULT 1 COMMENT 'Status (1-active, 0-disabled)',
  initial_income FLOAT DEFAULT 0.0 COMMENT 'Initial income'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Users table';

-- Categories table
CREATE TABLE categories (
  category_id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Category ID',
  name VARCHAR(50) NOT NULL COMMENT 'Category name',
  type TINYINT NOT NULL COMMENT 'Type (1-income, 2-expense)',
  user_id INT COMMENT 'User ID (NULL for system preset)',
  FOREIGN KEY (user_id) REFERENCES users (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Transaction categories table';

-- Transactions table
CREATE TABLE transactions (
  transaction_id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Transaction ID',
  user_id INT NOT NULL COMMENT 'User ID',
  amount FLOAT NOT NULL COMMENT 'Amount',
  type VARCHAR(10) NOT NULL COMMENT 'Transaction type (e.g., income, expense)',
  category VARCHAR(50) NOT NULL COMMENT 'Category name (duplicated for convenience)',
  description VARCHAR(200) COMMENT 'Description',
  date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Transaction date',
  category_id INT COMMENT 'Category ID',
  FOREIGN KEY (user_id) REFERENCES users (user_id),
  FOREIGN KEY (category_id) REFERENCES categories (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Transactions record table';