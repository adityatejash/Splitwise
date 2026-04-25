from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from ..models import Group, GroupMember, Expense, EditRequest, JoinRequest
from .. import db
from . import main


@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main.route('/dashboard')
@login_required
def dashboard():
    memberships = GroupMember.query.filter_by(user_id=current_user.id, status='active').all()
    group_ids = [m.group_id for m in memberships]
    my_groups = Group.query.filter(Group.id.in_(group_ids)).order_by(Group.created_at.desc()).all()
    total_expenses = Expense.query.filter(Expense.group_id.in_(group_ids)).count()

    admin_group_ids = [m.group_id for m in memberships if m.role == 'admin']

    pending_edits = 0
    pending_joins = 0
    if admin_group_ids:
        pending_edits = (EditRequest.query.join(Expense)
                         .filter(Expense.group_id.in_(admin_group_ids),
                                 EditRequest.status == 'pending').count())
        pending_joins = (JoinRequest.query
                         .filter(JoinRequest.group_id.in_(admin_group_ids),
                                 JoinRequest.status == 'pending').count())

    recent = (Expense.query.filter(Expense.group_id.in_(group_ids))
              .order_by(Expense.created_at.desc()).limit(5).all())

    return render_template('main/dashboard.html',
                           my_groups=my_groups,
                           total_expenses=total_expenses,
                           pending_count=pending_edits + pending_joins,
                           recent=recent)
