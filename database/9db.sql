-- Add indexes to frequently queried fields in transactions table
-- Composite index for user_id and transaction_date (for querying a specific user's transactions by date range)
CREATE INDEX idx_user_date ON transactions(user_id, transaction_date);

-- Index for type (to separate income and expense queries)
CREATE INDEX idx_type ON transactions(type);

-- Index for category_id (for category-based statistics)
CREATE INDEX idx_category ON transactions(category_id);

-- Index for payment_method (for filtering by payment method)
CREATE INDEX idx_payment ON transactions(payment_method);

-- Add index to budgets table
-- Index for budget_period (for monthly queries)
CREATE INDEX idx_budget_period ON budgets(budget_period);

-- Script to analyze query performance
EXPLAIN SELECT 
    t.transaction_id, t.amount, t.transaction_date, 
    c.name as category, t.type, t.payment_method, t.description
FROM transactions t
JOIN categories c ON t.category_id = c.category_id
WHERE t.user_id = 1 AND t.transaction_date BETWEEN '2025-01-01' AND '2025-12-31';

-- View index usage information
SHOW INDEX FROM transactions;
SHOW INDEX FROM budgets;

-- Optimize complex queries
EXPLAIN SELECT 
    DATE_FORMAT(transaction_date, '%Y-%m') as month,
    SUM(CASE WHEN type = 1 THEN amount ELSE 0 END) as income,
    SUM(CASE WHEN type = 2 THEN amount ELSE 0 END) as expense
FROM transactions
WHERE user_id = 1 AND YEAR( transaction_date) = 2023
GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')
ORDER BY month;

-- Add function for month name analysis
DELIMITER //
CREATE FUNCTION get_month_name(month_number INT) 
RETURNS VARCHAR(20)
DETERMINISTIC
BEGIN
    DECLARE month_name VARCHAR(20);
    CASE month_number
        WHEN 1 THEN SET month_name = 'January';
        WHEN 2 THEN SET month_name = 'February';
        WHEN 3 THEN SET month_name = 'March';
        WHEN 4 THEN SET month_name = 'April';
        WHEN 5 THEN SET month_name = 'May';
        WHEN 6 THEN SET month_name = 'June';
        WHEN 7 THEN SET month_name = 'July';
        WHEN 8 THEN SET month_name = 'August';
        WHEN 9 THEN SET month_name = 'September';
        WHEN 10 THEN SET month_name = 'October';
        WHEN 11 THEN SET month_name = 'November';
        WHEN 12 THEN SET month_name = 'December';
        ELSE SET month_name = 'Unknown';
    END CASE;
    RETURN month_name;
END//
DELIMITER ;

-- Create view to simplify common queries
CREATE VIEW vw_transaction_details AS
SELECT 
    t.transaction_id,
    t.user_id,
    u.username,
    t.amount,
    CASE WHEN t.type = 1 THEN 'Income' ELSE 'Expense' END as type_name,
    c.name as category_name,
    t.payment_method,
    t.account_name,
    t.transaction_date,
    t.description,
    MONTH(t.transaction_date) as month_number,
    get_month_name(MONTH(t.transaction_date)) as month_name,
    YEAR(t.transaction_date) as year
FROM 
    transactions t
JOIN 
    users u ON t.user_id = u.user_id
JOIN 
    categories c ON t.category_id = c.category_id;

-- Test the view
SELECT * FROM vw_transaction_details WHERE user_id = 1 ORDER BY transaction_date DESC LIMIT 10;