# 💸 Splitwise — Group Expense Tracker

![Python](https://img.shields.io/badge/Python-3.7+-3776AB?style=flat&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=flat&logo=mysql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat)
![CLI](https://img.shields.io/badge/Interface-CLI-6366f1?style=flat)

A command-line group expense splitting app built with **Python** and **MySQL**.  
Add groups, log expenses, record who paid what, and instantly see who owes whom — just like Splitwise.

---

## ✨ Features

- 👥 Create groups and manage members
- 💰 Log expenses with multiple contributors
- ⚖️ Automatically split costs among participants
- 📊 Calculate net balances — see exactly who pays whom
- 🔒 Credentials stored securely via environment variables

---

## 🗄️ Database Schema

```
app_users          app_groups
─────────          ──────────
user_id (PK)       group_id (PK)
user_name          group_name
                   created_date
     │                   │
     └──── group_members ┘
           (user_id, group_id)
                   │
            group_expenses
            ──────────────
            expense_id (PK)
            group_id (FK)
            description
            total_amount
            expense_date
                   │
       ┌───────────┴────────────┐
expense_contributions     expense_splits
─────────────────────     ──────────────
expense_id (FK)           expense_id (FK)
user_id (FK)              user_id (FK)
amount_paid               amount_owed
```

---

## 🚀 Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/splitwise.git
cd splitwise
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up the MySQL database
```bash
mysql -u root -p < database_setup.sql
```
Or open MySQL and paste the contents of `database_setup.sql`.

### 4. Configure environment variables

Copy the example file and fill in your MySQL credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```
DB_HOST=localhost
DB_NAME=splitwise
DB_USER=root
DB_PASSWORD=your_password_here
```

> ⚠️ `.env` is in `.gitignore` — your password will never be pushed to GitHub.

### 5. Run the app
```bash
python main.py
```

---

## 🖥️ Usage

```
--- Group Expense Tracker ---
1. Add Group / Show Groups
2. Add User / Show Users
3. Add User to Group / Show Group Members
4. Add Expense / Show Expenses
5. Show Balances
6. Exit
```

**Example flow:**
1. Create a group → e.g. `Goa Trip`
2. Add users → e.g. `Alice`, `Bob`, `Charlie`
3. Add them to the group
4. Log an expense → e.g. Alice paid ₹900 for hotel, split among all 3
5. Check balances → see Bob owes Alice ₹300, Charlie owes Alice ₹300

---

## 📁 Project Structure

```
splitwise/
├── main.py               # Main application
├── database_setup.sql    # Creates the database and all tables
├── reset_tables.sql      # Clears all data (fresh start)
├── requirements.txt      # Python dependencies
├── .env.example          # Template for DB credentials
├── .gitignore
└── README.md
```

---

## 🔄 Reset Data

To wipe all records and start fresh:
```bash
mysql -u root -p < reset_tables.sql
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.7+ |
| Database | MySQL 8.0+ |
| DB Driver | mysql-connector-python |
| CLI Tables | prettytable |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
