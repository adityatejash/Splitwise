-- Create Database
CREATE DATABASE splitwise;
USE splitwise;

-- 1. Users table
CREATE TABLE app_users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(255) NOT NULL
);

-- 2. Groups table
CREATE TABLE app_groups (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    group_name VARCHAR(255) NOT NULL,
    created_date DATE
);

-- 3. Group members table
CREATE TABLE group_members (
    user_id INT NOT NULL,
    group_id INT NOT NULL,
    PRIMARY KEY(user_id, group_id),
    FOREIGN KEY (user_id) REFERENCES app_users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES app_groups(group_id) ON DELETE CASCADE
);

-- 4. Expenses table
CREATE TABLE group_expenses (
    expense_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    description VARCHAR(255),
    total_amount DECIMAL(10,2),
    expense_date DATE,
    FOREIGN KEY (group_id) REFERENCES app_groups(group_id) ON DELETE CASCADE
);

-- 5. Contributions table
CREATE TABLE expense_contributions (
    expense_id INT NOT NULL,
    user_id INT NOT NULL,
    amount_paid DECIMAL(10,2),
    FOREIGN KEY (expense_id) REFERENCES group_expenses(expense_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES app_users(user_id) ON DELETE CASCADE
);

-- 6. Expense splits table
CREATE TABLE expense_splits (
    expense_id INT NOT NULL,
    user_id INT NOT NULL,
    amount_owed DECIMAL(10,2),
    FOREIGN KEY (expense_id) REFERENCES group_expenses(expense_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES app_users(user_id) ON DELETE CASCADE
);
