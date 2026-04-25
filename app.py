import os
from flask import Flask, render_template, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

def connect_db():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'splitwise'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '')
        )
        return conn
    except Error as e:
        return None

# ---------------- ROUTES ----------------

@app.route('/')
def index():
    return render_template('index.html')

# ---------------- GROUPS ----------------

@app.route('/api/groups', methods=['GET'])
def get_groups():
    conn = connect_db()
    if not conn:
        return jsonify({'error': 'DB connection failed'}), 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM app_groups ORDER BY group_id DESC")
    groups = cursor.fetchall()
    for g in groups:
        if g.get('created_date'):
            g['created_date'] = str(g['created_date'])
    conn.close()
    return jsonify(groups)

@app.route('/api/groups', methods=['POST'])
def add_group():
    data = request.json
    group_name = data.get('group_name', '').strip()
    if not group_name:
        return jsonify({'error': 'Group name is required'}), 400
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO app_groups (group_name, created_date) VALUES (%s, CURDATE())", (group_name,))
    conn.commit()
    group_id = cursor.lastrowid
    conn.close()
    return jsonify({'success': True, 'group_id': group_id, 'group_name': group_name})

# ---------------- USERS ----------------

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = connect_db()
    if not conn:
        return jsonify({'error': 'DB connection failed'}), 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM app_users ORDER BY user_id DESC")
    users = cursor.fetchall()
    conn.close()
    return jsonify(users)

@app.route('/api/users', methods=['POST'])
def add_user():
    data = request.json
    user_name = data.get('user_name', '').strip()
    if not user_name:
        return jsonify({'error': 'User name is required'}), 400
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO app_users (user_name) VALUES (%s)", (user_name,))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return jsonify({'success': True, 'user_id': user_id, 'user_name': user_name})

# ---------------- GROUP MEMBERS ----------------

@app.route('/api/groups/<int:group_id>/members', methods=['GET'])
def get_members(group_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.user_id, u.user_name
        FROM group_members gm
        JOIN app_users u ON gm.user_id = u.user_id
        WHERE gm.group_id = %s
    """, (group_id,))
    members = cursor.fetchall()
    conn.close()
    return jsonify(members)

@app.route('/api/groups/<int:group_id>/members', methods=['POST'])
def add_member(group_id):
    data = request.json
    user_ids = data.get('user_ids', [])
    conn = connect_db()
    cursor = conn.cursor()
    added = []
    skipped = []
    for uid in user_ids:
        cursor.execute("SELECT * FROM group_members WHERE user_id=%s AND group_id=%s", (uid, group_id))
        if cursor.fetchone():
            skipped.append(uid)
        else:
            cursor.execute("INSERT INTO group_members (user_id, group_id) VALUES (%s, %s)", (uid, group_id))
            added.append(uid)
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'added': added, 'skipped': skipped})

# ---------------- EXPENSES ----------------

@app.route('/api/groups/<int:group_id>/expenses', methods=['GET'])
def get_expenses(group_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.expense_id, e.description, e.total_amount, e.expense_date,
               GROUP_CONCAT(DISTINCT u.user_name ORDER BY u.user_name SEPARATOR ', ') as contributors
        FROM group_expenses e
        LEFT JOIN expense_contributions ec ON e.expense_id = ec.expense_id
        LEFT JOIN app_users u ON ec.user_id = u.user_id
        WHERE e.group_id = %s
        GROUP BY e.expense_id
        ORDER BY e.expense_date DESC
    """, (group_id,))
    expenses = cursor.fetchall()
    for ex in expenses:
        if ex.get('expense_date'):
            ex['expense_date'] = str(ex['expense_date'])
        ex['total_amount'] = float(ex['total_amount'])
    conn.close()
    return jsonify(expenses)

@app.route('/api/groups/<int:group_id>/expenses', methods=['POST'])
def add_expense(group_id):
    data = request.json
    description = data.get('description', '').strip()
    contributions = data.get('contributions', [])

    if not description:
        return jsonify({'error': 'Description is required'}), 400
    if not contributions:
        return jsonify({'error': 'At least one contributor is required'}), 400

    conn = connect_db()
    cursor = conn.cursor()

    total_amount = sum(float(c['amount_paid']) for c in contributions)

    cursor.execute(
        "INSERT INTO group_expenses (group_id, description, total_amount, expense_date) VALUES (%s,%s,%s,CURDATE())",
        (group_id, description, total_amount)
    )
    expense_id = cursor.lastrowid

    for c in contributions:
        uid = int(c['user_id'])
        amt = float(c['amount_paid'])
        participants = [int(p) for p in c.get('participants', [])]

        cursor.execute(
            "INSERT INTO expense_contributions (expense_id, user_id, amount_paid) VALUES (%s,%s,%s)",
            (expense_id, uid, amt)
        )
        if participants:
            split_amt = round(amt / len(participants), 2)
            for pid in participants:
                cursor.execute(
                    "INSERT INTO expense_splits (expense_id, user_id, amount_owed) VALUES (%s,%s,%s)",
                    (expense_id, pid, split_amt)
                )

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'expense_id': expense_id, 'total_amount': total_amount})

# ---------------- BALANCES ----------------

@app.route('/api/groups/<int:group_id>/balances', methods=['GET'])
def get_balances(group_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT u.user_id, u.user_name
        FROM group_members gm
        JOIN app_users u ON gm.user_id = u.user_id
        WHERE gm.group_id = %s
    """, (group_id,))
    users = cursor.fetchall()

    if not users:
        conn.close()
        return jsonify([])

    net_balance = {}
    for user in users:
        uid = user['user_id']
        cursor.execute("""
            SELECT IFNULL(SUM(amount_paid),0) as total
            FROM expense_contributions ec
            JOIN group_expenses e ON ec.expense_id = e.expense_id
            WHERE e.group_id=%s AND ec.user_id=%s
        """, (group_id, uid))
        total_paid = float(cursor.fetchone()['total'])

        cursor.execute("""
            SELECT IFNULL(SUM(amount_owed),0) as total
            FROM expense_splits es
            JOIN group_expenses e ON es.expense_id = e.expense_id
            WHERE e.group_id=%s AND es.user_id=%s
        """, (group_id, uid))
        total_owed = float(cursor.fetchone()['total'])

        net_balance[uid] = round(total_paid - total_owed, 2)

    creditors = [(u['user_id'], u['user_name'], net_balance[u['user_id']]) for u in users if net_balance[u['user_id']] > 0]
    debtors   = [(u['user_id'], u['user_name'], -net_balance[u['user_id']]) for u in users if net_balance[u['user_id']] < 0]

    settlements = []
    for d_uid, d_name, d_amt in debtors:
        amt_left = d_amt
        for i, (c_uid, c_name, c_amt) in enumerate(creditors):
            if amt_left == 0:
                break
            pay_amt = min(amt_left, c_amt)
            settlements.append({'from': d_name, 'to': c_name, 'amount': round(pay_amt, 2)})
            amt_left -= pay_amt
            creditors[i] = (c_uid, c_name, round(c_amt - pay_amt, 2))

    conn.close()
    return jsonify(settlements)

if __name__ == '__main__':
    app.run(debug=True)
