import os
from app import create_app, db
from app.models import User, Group, GroupMember, Expense, ExpenseSplit, EditRequest, JoinRequest

app = create_app(os.environ.get('FLASK_ENV', 'default'))


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Group=Group, GroupMember=GroupMember,
                Expense=Expense, ExpenseSplit=ExpenseSplit, EditRequest=EditRequest)


@app.cli.command('init-db')
def init_db():
    """Create all database tables."""
    with app.app_context():
        db.create_all()
    print('Database tables created.')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
