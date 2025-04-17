-- Budget table
CREATE TABLE
  budgets (
    budget_id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Budget ID',
    user_id INT NOT NULL COMMENT 'User ID',
    budget_period VARCHAR(50) NOT NULL COMMENT 'Year-Month (format: 2023-06)',
    total_amount DECIMAL(12, 2) NOT NULL COMMENT 'Total budget amount',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Create time',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    UNIQUE KEY (user_id, budget_period) COMMENT 'Ensure one budget record per user per month'
  ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = 'Budget table';