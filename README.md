# Splitwise Clone

A full-stack expense splitting web application built with **Flask** and **SQLAlchemy**, inspired by Splitwise. It lets groups of people track shared expenses, split costs, and settle debts — with multi-currency support, PDF export, and a role-based permission system.

---

## Features

- **User Authentication** — Register, login, logout with secure password hashing. Rate-limited login (5 attempts/minute) to prevent brute-force attacks.
- **Guest Mode** — Try the app without an account. Guest sessions are ephemeral and cleaned up automatically on logout or tab close.
- **Group Management** — Create and manage groups with invite links and 6-character join codes. Up to 5 groups per user (free tier).
- **Flexible Membership** — Add members by email (registered users) or by name (non-registered participants). Admins can approve/reject join requests.
- **Expense Tracking** — Log expenses with description, amount, currency, date, and who paid.
- **Smart Splitting** — Split expenses equally among selected participants, or define custom split amounts per person.
- **Balance Calculation** — Greedy debt-minimization algorithm calculates the minimum number of transactions needed to settle all debts.
- **Multi-Currency Support** — Supports INR, USD, EUR, GBP, JPY, AUD, CAD, SGD. Balances are tracked per currency.
- **Edit Requests** — Non-admin members can request edits to expenses; admins review and approve or reject.
- **PDF Export** — Download a full group summary (members, expenses, settlements) as a formatted PDF using ReportLab.
- **CSRF Protection** — All forms protected against Cross-Site Request Forgery.
- **Custom Error Pages** — Friendly 404 and 500 error pages.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database ORM | Flask-SQLAlchemy |
| Authentication | Flask-Login, Werkzeug |
| Forms & Security | Flask-WTF (CSRF), Flask-Limiter |
| PDF Generation | ReportLab |
| Templating | Jinja2 |
| Database | SQLite (dev) / MySQL / PostgreSQL (prod) |
| Deployment | Gunicorn + Procfile (Render/Heroku-compatible) |

---

## Project Structure

```
Splitwise/
├── app/
│   ├── __init__.py          # App factory, extensions init
│   ├── models.py            # SQLAlchemy models
│   ├── auth/
│   │   └── routes.py        # Register, login, logout, guest session
│   ├── groups/
│   │   ├── routes.py        # Group CRUD, membership, join requests
│   │   └── pdf.py           # PDF report generation
│   ├── expenses/
│   │   └── routes.py        # Add/edit expenses, balance calculation
│   ├── main/
│   │   └── routes.py        # Dashboard
│   └── templates/
│       ├── base.html
│       ├── auth/            # login.html, register.html
│       ├── groups/          # list, create, detail, join, join_code
│       ├── expenses/        # add, edit, balances
│       ├── main/            # dashboard
│       └── errors/          # 404, 500
├── config.py                # Configuration classes (dev/prod)
├── run.py                   # Entry point + Flask CLI commands
├── database_setup.sql       # Raw SQL schema (reference)
├── requirements.txt
├── Procfile                 # For Render/Heroku deployment
├── runtime.txt              # Python version pin
└── .env.example             # Environment variable template
```

---

## Database Models

- **User** — Registered and guest accounts with hashed passwords.
- **Group** — A shared expense group with a unique invite token and join code.
- **GroupMember** — Join table linking users to groups, with roles (`admin`/`member`) and statuses (`active`/`pending`). Supports non-registered participants (name-only).
- **JoinRequest** — Tracks pending/approved/rejected requests to join a group.
- **Expense** — A logged expense with amount, currency, payer, and date.
- **ExpenseSplit** — Records each member's share of an expense.
- **EditRequest** — A member's proposal to change an existing expense, pending admin review.

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/adityatejash/splitwise.git
cd splitwise

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and set your SECRET_KEY and DATABASE_URL
```

### Running Locally

```bash
# Initialize the database
flask init-db

# Start the development server
python run.py
```

The app will be available at `http://127.0.0.1:5000`.

### Environment Variables

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Flask secret key for sessions | `change-this-to-a-long-random-string` |
| `DATABASE_URL` | Database connection string | `sqlite:///splitwise.db` |
| `FLASK_ENV` | Environment (`development`/`production`) | `development` |

---

## Deployment (Render / Heroku)

The project includes a `Procfile` for WSGI deployment:

```
web: gunicorn run:app
```

Set the environment variables (`SECRET_KEY`, `DATABASE_URL`) in your hosting platform's dashboard and deploy. For PostgreSQL on Render:

```
DATABASE_URL=postgresql://user:password@host/dbname
```

---

## Supported Currencies

INR · USD · EUR · GBP · JPY · AUD · CAD · SGD

Expenses are tracked per currency. Balances and settlements are calculated independently for each currency within a group.

---

## How Balance Settlement Works

The app uses a **greedy debt minimization** algorithm:

1. Compute each member's net balance (total paid minus total owed) per currency.
2. Sort creditors (positive balance) and debtors (negative balance).
3. Greedily match the largest creditor with the largest debtor to minimize the number of transactions.

This produces the fewest possible payments needed to fully settle all debts.

---

## License

This project is open source and available under the [MIT License](LICENSE).
