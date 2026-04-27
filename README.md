# 💸 Splitwise Clone — Expense Splitter App

A full-stack **group expense splitting web app** that lets friends, roommates, and teams track shared costs, split bills, and settle debts — with multi-currency support and PDF export.

---

## 🌐 Live Demo

🚀 **Live Website:** [https://adityatejash-splitwise.up.railway.app](https://adityatejash-splitwise.up.railway.app)

---

## ✨ Features

* 👤 User Registration, Login & Logout with secure password hashing
* 🕵️ Guest Mode — try the app without creating an account
* 👥 Create & manage groups with invite links and join codes
* 💰 Add expenses with description, amount, currency, and who paid
* ➗ Equal or custom split among selected group members
* 📊 Auto-calculated balances with minimum settlement transactions
* 🌍 Multi-Currency Support — INR, USD, EUR, GBP, JPY, AUD, CAD, SGD
* ✏️ Edit Request System — members request edits, admins approve/reject
* 📄 Export full group summary as a PDF report
* 🔒 CSRF Protection on all forms
* 🚦 Rate-limited login to prevent brute-force attacks
* ❌ Custom 404 & 500 error pages

---

## 🖥️ Tech Stack

* **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-Migrate
* **Database:** PostgreSQL (Production) / SQLite (Development)
* **PDF Generation:** ReportLab
* **Security:** Flask-WTF (CSRF), Flask-Limiter, Werkzeug
* **Templating:** Jinja2
* **Deployment:** Railway (Gunicorn)

---

## ⚙️ How to Use

1. Open the [live website](https://adityatejash-splitwise.up.railway.app)
2. Register an account or continue as a Guest
3. Create a group and add members
4. Log expenses and choose how to split them
5. View balances to see who owes whom
6. Export a PDF summary of the group

---

## 📁 Project Structure

```
Splitwise/
│
├── app/
│   ├── __init__.py          # App factory & extensions
│   ├── models.py            # Database models
│   ├── auth/                # Register, Login, Logout, Guest
│   ├── groups/              # Group management & PDF export
│   ├── expenses/            # Expense tracking & balances
│   ├── main/                # Dashboard
│   └── templates/           # Jinja2 HTML templates
│
├── config.py                # App configuration
├── run.py                   # Entry point
├── requirements.txt
├── Procfile                 # Railway/Heroku deployment
└── README.md
```

---

## 💡 Highlights

* Greedy debt-minimization algorithm for fewest settlement transactions
* Supports both registered users and name-only (guest) group members
* Balances tracked independently per currency within a group
* Auto table creation on first deploy — no manual DB setup needed
* Clean, responsive UI with role-based access (admin vs member)

---

## 👨‍💻 Author

**Aditya Prakash**

Found a bug or have a suggestion? Feel free to open an issue or **DM me on [LinkedIn](https://www.linkedin.com/in/adityatejash)** — feedback is always welcome!

---

## ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub!
