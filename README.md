# Splitwise Clone - Group Expense Tracker

A fully functional, production-ready web application to track shared expenses, split bills, and settle balances among friends.

## Features
- **Secure Authentication**: Hashed passwords, session management, and rate-limited logins.
- **Guest Sessions**: Ephemeral accounts for quick testing.
- **Group Management**: Create groups (max 5 per user), invite members via URL or join codes.
- **Flexible Members**: Add members by name (no account required) or email.
- **Expense Tracking**: Add, edit, and delete shared expenses with equal or custom split options.
- **Automated Balances**: Smart settlement calculations (who owes whom) with multi-currency support.
- **Export**: Download group summaries as cleanly formatted PDFs.
- **Security**: Full CSRF protection, SQLAlchemy ORM (prevents SQL injection).

---

## Deployment (Render Free Tier)

This application is configured for direct deployment on [Render](https://render.com).

### 1. Push to GitHub
First, commit all your files and push them to a public or private GitHub repository:
```bash
<<<<<<< HEAD
git clone https://github.com/adityatejash/splitwise.git
cd splitwise
=======
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
>>>>>>> ccc4104 (Ready for trial deployment)
```

### 2. Create Render Web Service
1. Go to your Render Dashboard and create a **New Web Service**.
2. Connect your GitHub repository.
3. Configure the service:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app --workers 2 --threads 4 --bind 0.0.0.0:$PORT`
   - **Instance Type**: Free

### 3. Create Render PostgreSQL Database
1. Go to Render Dashboard -> **New PostgreSQL**.
2. Name it (e.g., `splitwise-db`) and select the Free tier.
3. Once created, copy the **Internal Database URL** (if deploying Web Service in the same region) or **External Database URL**.

### 4. Set Environment Variables
Go to your Web Service **Environment** tab and add the following variables:
- `FLASK_ENV`: `production`
- `SECRET_KEY`: `<generate a long random string>`
- `DATABASE_URL`: `<paste your PostgreSQL URL here>` *(The app automatically handles Render's `postgres://` to `postgresql://` conversion).*

**That's it!** Render will deploy your application. The database tables will be automatically created on the first successful startup.

---

## Local Development Setup

1. **Clone the repository**
2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Variables**
   Rename `.env.example` to `.env` and fill in the values. For local testing, the default SQLite config works perfectly.
5. **Run the app**
   ```bash
   python run.py
   ```

## Database Migrations (Optional)
If you modify the database models (`app/models.py`), you can use Flask-Migrate to update the schema:
```bash
flask db init      # Only run once to create the migrations folder
flask db migrate -m "Added new column"
flask db upgrade
```

## Developer
Developed by Aditya Prakash  
[GitHub Profile](https://github.com/adityatejash) | [LinkedIn Profile](https://www.linkedin.com/in/adityatejash/)
