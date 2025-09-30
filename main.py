import mysql.connector
from mysql.connector import Error
from prettytable import PrettyTable

# ---------------- Database Connection ----------------
def connect_db():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='splitwise',  # your database name
            user='root',
            password='05460441'
        )
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None

# ---------------- Add Functions ----------------
def add_group(group_name):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO app_groups (group_name, created_date) VALUES (%s, CURDATE())",
        (group_name,)
    )
    conn.commit()
    print(f"✅ Group '{group_name}' added successfully.")
    conn.close()

def add_user(user_name):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO app_users (user_name) VALUES (%s)", 
        (user_name,)
    )
    conn.commit()
    print(f"✅ User '{user_name}' added successfully.")
    conn.close()

def add_user_to_group(user_id, group_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO group_members (user_id, group_id) VALUES (%s, %s)",
        (user_id, group_id)
    )
    conn.commit()
    print(f"✅ User {user_id} added to Group {group_id}.")
    conn.close()

# ---------------- Add Expense ----------------
def add_expense(group_id, description, contributions):
    """
    contributions: list of tuples (user_id, amount_paid, participants_list)
    participants_list: list of user_ids for whom this user paid
    """
    conn = connect_db()
    cursor = conn.cursor()

    total_amount = sum([amt for uid, amt, plist in contributions])

    # Insert expense
    cursor.execute(
        "INSERT INTO group_expenses (group_id, description, total_amount, expense_date) VALUES (%s,%s,%s,CURDATE())",
        (group_id, description, total_amount)
    )
    expense_id = cursor.lastrowid

    # Insert contributions and splits
    for uid, amt, plist in contributions:
        # Record contribution
        cursor.execute(
            "INSERT INTO expense_contributions (expense_id, user_id, amount_paid) VALUES (%s,%s,%s)",
            (expense_id, uid, amt)
        )
        # Split amount among participants
        num_participants = len(plist)
        split_amt = round(amt / num_participants, 2) if num_participants else 0
        for pid in plist:
            cursor.execute(
                "INSERT INTO expense_splits (expense_id, user_id, amount_owed) VALUES (%s,%s,%s)",
                (expense_id, pid, split_amt)
            )

    conn.commit()
    print(f"✅ Expense '{description}' added. Total: {total_amount}")
    conn.close()

# ---------------- Show Tables ----------------
def show_table(table_name):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    table = PrettyTable()
    table.field_names = columns
    for row in rows:
        table.add_row(row)

    print(f"\n--- {table_name.upper()} ---")
    print(table)
    conn.close()

def show_group_members(group_id=None):
    conn = connect_db()
    cursor = conn.cursor()
    
    query = """
        SELECT gm.user_id, u.user_name, gm.group_id, g.group_name
        FROM group_members gm
        JOIN app_users u ON gm.user_id = u.user_id
        JOIN app_groups g ON gm.group_id = g.group_id
    """
    if group_id is not None:
        query += " WHERE gm.group_id = %s"
        cursor.execute(query, (group_id,))
    else:
        cursor.execute(query)

    rows = cursor.fetchall()
    columns = ["UserID", "UserName", "GroupID", "GroupName"]

    table = PrettyTable()
    table.field_names = columns
    for row in rows:
        table.add_row(row)

    title = f"MEMBERS OF GROUP {group_id}" if group_id else "ALL GROUP MEMBERS"
    print(f"\n--- {title} ---")
    print(table)
    conn.close()

def show_expenses():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.expense_id, g.group_id, g.group_name, e.description, e.total_amount, e.expense_date
        FROM group_expenses e
        JOIN app_groups g ON e.group_id = g.group_id
    """)
    rows = cursor.fetchall()
    columns = ["ExpenseID", "GroupID", "GroupName", "Description", "TotalAmount", "ExpenseDate"]

    table = PrettyTable()
    table.field_names = columns
    for row in rows:
        table.add_row(row)

    print("\n--- EXPENSES ---")
    print(table)
    conn.close()

# ---------------- Calculate Balances ----------------
def calculate_balances(group_id):
    conn = connect_db()
    cursor = conn.cursor()

    # Get all users in the group
    cursor.execute("""
        SELECT u.user_id, u.user_name
        FROM group_members gm
        JOIN app_users u ON gm.user_id = u.user_id
        WHERE gm.group_id = %s
    """, (group_id,))
    users = cursor.fetchall()
    if not users:
        print("⚠️ No users in this group.")
        conn.close()
        return

    # Calculate net balance: paid - owed
    net_balance = {}
    for uid, uname in users:
        cursor.execute("""
            SELECT IFNULL(SUM(amount_paid),0)
            FROM expense_contributions ec
            JOIN group_expenses e ON ec.expense_id = e.expense_id
            WHERE e.group_id=%s AND ec.user_id=%s
        """, (group_id, uid))
        total_paid = cursor.fetchone()[0]

        cursor.execute("""
            SELECT IFNULL(SUM(amount_owed),0)
            FROM expense_splits es
            JOIN group_expenses e ON es.expense_id = e.expense_id
            WHERE e.group_id=%s AND es.user_id=%s
        """, (group_id, uid))
        total_owed = cursor.fetchone()[0]

        net_balance[uid] = round(total_paid - total_owed, 2)

    # Separate creditors and debtors
    creditors = [(uid, uname, bal) for uid, (uname, bal) in zip([u[0] for u in users], [(u[1], net_balance[u[0]]) for u in users]) if bal > 0]
    debtors = [(uid, uname, -bal) for uid, (uname, bal) in zip([u[0] for u in users], [(u[1], net_balance[u[0]]) for u in users]) if bal < 0]

    table = PrettyTable()
    table.field_names = ["FromUser", "ToUser", "Amount"]

    # Calculate who pays whom
    for d_uid, d_name, d_amt in debtors:
        amt_left = d_amt
        for i, (c_uid, c_name, c_amt) in enumerate(creditors):
            if amt_left == 0:
                break
            pay_amt = min(amt_left, c_amt)
            table.add_row([d_name, c_name, round(pay_amt, 2)])
            amt_left -= pay_amt
            # Update creditor's remaining balance
            creditors[i] = (c_uid, c_name, round(c_amt - pay_amt, 2))

    print(f"\n--- BALANCES IN GROUP {group_id} ---")
    print(table)
    conn.close()

# ---------------- Interactive Menu ----------------
def main():
    while True:
        print("\n--- Group Expense Tracker ---")
        print("1. Add Group / Show Groups")
        print("2. Add User / Show Users")
        print("3. Add User to Group / Show Group Members")
        print("4. Add Expense / Show Expenses")
        print("5. Show Balances")
        print("6. Exit")

        choice = input("Enter choice: ")

        if choice == '1':
            show_table("app_groups")
            group_name = input("Enter group name to add (-1 to cancel): ")
            if group_name == "-1": continue
            add_group(group_name)
            show_table("app_groups")

        elif choice == '2':
            show_table("app_users")
            user_name = input("Enter user name to add (-1 to cancel): ")
            if user_name == "-1": continue
            add_user(user_name)
            show_table("app_users")
            # show_group_members()

        elif choice == '3':
            show_table("app_users")
            show_table("app_groups")

            user_input = input("Enter user IDs to add to group (comma-separated, -1 to cancel): ")
            if user_input == "-1": continue
            try:
                user_ids = [int(x.strip()) for x in user_input.split(",")]
                group_id = int(input("Enter group ID: "))
                conn = connect_db()
                cursor = conn.cursor()
                for uid in user_ids:
                    cursor.execute("SELECT * FROM group_members WHERE user_id=%s AND group_id=%s", (uid, group_id))
                    if cursor.fetchone():
                        print(f"User {uid} already in Group {group_id}, skipped.")
                        continue
                    cursor.execute("INSERT INTO group_members (user_id, group_id) VALUES (%s, %s)", (uid, group_id))
                    print(f"✅ User {uid} added to Group {group_id}.")
                conn.commit()
                conn.close()
                show_group_members(group_id)
            except ValueError:
                print("⚠️ Invalid input! Please enter numeric IDs separated by commas.")

        elif choice == '4':
            show_table("app_groups")
            try:
                group_id = int(input("Enter group ID (-1 to cancel): "))
                if group_id == -1: continue
                description = input("Enter expense description: ")
                show_group_members(group_id)

                n = int(input("How many contributors? "))
                contributions = []

                for _ in range(n):
                    while True:
                        try:
                            uid = int(input("Contributor User ID: "))
                            break
                        except ValueError:
                            print("⚠️ Enter a valid user ID (number).")
                    while True:
                        try:
                            amt = float(input("Amount paid by this user: "))
                            break
                        except ValueError:
                            print("⚠️ Enter a valid number for the amount.")

                    participants_input = input("Enter user IDs this contributor paid for (comma-separated): ")
                    participants_list = []
                    try:
                        participants_list = [int(x.strip()) for x in participants_input.split(",")]
                    except ValueError:
                        print("⚠️ Invalid participant IDs! Skipping.")
                    contributions.append((uid, amt, participants_list))

                add_expense(group_id, description, contributions)
                show_expenses()

            except ValueError:
                print("⚠️ Invalid input!")

        elif choice == '5':
            show_table("app_groups")
            try:
                group_id = int(input("Enter group ID to calculate balances (-1 to cancel): "))
                if group_id == -1: continue
                calculate_balances(group_id)
            except ValueError:
                print("⚠️ Invalid input!")

        elif choice == '6':
            print("Exiting... 👋")
            break
        else:
            print("⚠️ Invalid choice! Try again.")

if __name__ == "__main__":
    main()
