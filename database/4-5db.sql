DROP DATABASE IF EXISTS finance_manager;
-- Create database
CREATE DATABASE IF NOT EXISTS finance_manager DEFAULT CHARACTER
SET
  utf8mb4 COLLATE utf8mb4_general_ci;

-- Use the database
USE finance_manager;

-- Users table
CREATE TABLE
  users (
    user_id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'User ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT 'Username',
    password VARCHAR(255) NOT NULL COMMENT 'Password (encrypted)',
    email VARCHAR(100) UNIQUE COMMENT 'Email address',
    phone VARCHAR(20) COMMENT 'Phone number',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Create time',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
    status TINYINT NOT NULL DEFAULT 1 COMMENT 'Status (1-active, 0-disabled)'
  ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = 'Users table';

-- Transactions table
-- CREATE TABLE
--   transactions (
--     transaction_id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Transaction ID',
--     user_id INT NOT NULL COMMENT 'User ID',
--     amount DECIMAL(12, 2) NOT NULL COMMENT 'Amount',
--     type TINYINT NOT NULL COMMENT 'Type (1-income, 2-expense)',
--     category_id INT NOT NULL COMMENT 'Category ID',
--     payment_method VARCHAR(50) COMMENT 'Payment method',
--     account_name VARCHAR(50) COMMENT 'Account name',
--     transaction_date DATE NOT NULL COMMENT 'Transaction date',
--     description VARCHAR(255) COMMENT 'Description',
--     create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Create time',
--     update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
--     FOREIGN KEY (user_id) REFERENCES users (user_id),
--     FOREIGN KEY (category_id) REFERENCES categories (category_id)
--   ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = 'Transactions record table';
  

  CREATE TABLE transactions (
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
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time'
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = 'Transactions record table';