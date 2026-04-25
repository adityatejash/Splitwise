from decimal import Decimal
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from .. import db
from ..models import Group, GroupMember, Expense, ExpenseSplit, EditRequest, CURRENCIES
from . import expenses


def _compute_balances(group_id):
    members = GroupMember.query.filter_by(group_id=group_id, status='active').all()
    group_expenses = Expense.query.filter_by(group_id=group_id).all()
    currencies_used = list(set(e.currency for e in group_expenses)) or ['INR']
    all_settlements = []

    for currency in currencies_used:
        net = {m.id: {'name': m.name, 'balance': Decimal('0')} for m in members}

        for exp in group_expenses:
            if exp.currency != currency:
                continue
            if exp.paid_by in net:
                net[exp.paid_by]['balance'] += Decimal(str(exp.amount))
            for split in exp.splits:
                if split.member_id in net:
                    net[split.member_id]['balance'] -= Decimal(str(split.share_amount))

        creditors = sorted([(k, v) for k, v in net.items() if v['balance'] > 0],
                           key=lambda x: -x[1]['balance'])
        debtors = sorted([(k, v) for k, v in net.items() if v['balance'] < 0],
                         key=lambda x: x[1]['balance'])

        ci, di = 0, 0
        while ci < len(creditors) and di < len(debtors):
            c_id, c_data = creditors[ci]
            d_id, d_data = debtors[di]
            pay = min(c_data['balance'], -d_data['balance'])
            if pay > Decimal('0.01'):
                all_settlements.append({'from_user': d_data['name'], 'to_user': c_data['name'],
                                        'amount': float(round(pay, 2)), 'currency': currency})
            c_data['balance'] -= pay
            d_data['balance'] += pay
            if c_data['balance'] <= Decimal('0.01'):
                ci += 1
            if d_data['balance'] >= Decimal('-0.01'):
                di += 1

    return all_settlements


# ── ADD EXPENSE ────────────────────────────────────────────────────────────────
@expenses.route('/group/<int:group_id>/add', methods=['GET', 'POST'])
@login_required
def add_expense(group_id):
    group = Group.query.get_or_404(group_id)
    if not current_user.is_member_of(group_id):
        abort(403)

    members = GroupMember.query.filter_by(group_id=group_id, status='active').all()
    # find current user's GroupMember record
    my_member = GroupMember.query.filter_by(
        group_id=group_id, user_id=current_user.id, status='active').first()

    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        amount_str = request.form.get('amount', '').strip()
        currency = request.form.get('currency', 'INR')
        paid_by_member_id = request.form.get('paid_by_member_id')
        split_type = request.form.get('split_type', 'equal')
        selected_ids = [int(i) for i in request.form.getlist('split_members')]

        if not description:
            flash('Description is required.', 'error')
            return render_template('expenses/add.html', group=group, members=members,
                                   currencies=CURRENCIES, my_member=my_member)
        try:
            amount = Decimal(amount_str)
            assert amount > 0
        except Exception:
            flash('Enter a valid positive amount.', 'error')
            return render_template('expenses/add.html', group=group, members=members,
                                   currencies=CURRENCIES, my_member=my_member)

        if not paid_by_member_id:
            flash('Select who paid.', 'error')
            return render_template('expenses/add.html', group=group, members=members,
                                   currencies=CURRENCIES, my_member=my_member)

        if not selected_ids:
            flash('Select at least one participant.', 'error')
            return render_template('expenses/add.html', group=group, members=members,
                                   currencies=CURRENCIES, my_member=my_member)

        expense = Expense(group_id=group_id, paid_by=int(paid_by_member_id),
                          created_by=current_user.id, description=description,
                          amount=amount, currency=currency)
        db.session.add(expense)
        db.session.flush()

        if split_type == 'equal':
            share = round(amount / len(selected_ids), 2)
            for mid in selected_ids:
                db.session.add(ExpenseSplit(expense_id=expense.id,
                                            member_id=mid, share_amount=share))
        else:
            total_custom = Decimal('0')
            splits_data = []
            for mid in selected_ids:
                val = Decimal(request.form.get(f'custom_{mid}', '0') or '0')
                splits_data.append((mid, val))
                total_custom += val
            if abs(total_custom - amount) > Decimal('0.10'):
                db.session.rollback()
                flash(f'Custom split sum ({total_custom}) must equal total ({amount}).', 'error')
                return render_template('expenses/add.html', group=group, members=members,
                                       currencies=CURRENCIES, my_member=my_member)
            for mid, s in splits_data:
                db.session.add(ExpenseSplit(expense_id=expense.id, member_id=mid, share_amount=s))

        db.session.commit()
        flash(f'Expense "{description}" saved!', 'success')
        return redirect(url_for('groups.detail', group_id=group_id))

    return render_template('expenses/add.html', group=group, members=members,
                           currencies=CURRENCIES, my_member=my_member)


# ── EDIT EXPENSE ───────────────────────────────────────────────────────────────
@expenses.route('/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    group_id = expense.group_id
    if not current_user.is_member_of(group_id):
        abort(403)

    group = Group.query.get(group_id)
    members = GroupMember.query.filter_by(group_id=group_id, status='active').all()
    current_splits = {s.member_id: float(s.share_amount) for s in expense.splits}
    is_admin = current_user.is_admin_of(group_id)

    if expense.has_pending_request() and not is_admin:
        flash('A pending edit request already exists for this expense.', 'warning')
        return redirect(url_for('groups.detail', group_id=group_id))

    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        amount_str = request.form.get('amount', '').strip()
        currency = request.form.get('currency', expense.currency)
        split_type = request.form.get('split_type', 'equal')
        selected_ids = [int(i) for i in request.form.getlist('split_members')]

        try:
            amount = Decimal(amount_str)
            assert amount > 0
        except Exception:
            flash('Enter a valid amount.', 'error')
            return render_template('expenses/edit.html', expense=expense, group=group,
                                   members=members, currencies=CURRENCIES,
                                   current_splits=current_splits, is_admin=is_admin)

        if not selected_ids:
            flash('Select at least one participant.', 'error')
            return render_template('expenses/edit.html', expense=expense, group=group,
                                   members=members, currencies=CURRENCIES,
                                   current_splits=current_splits, is_admin=is_admin)

        if split_type == 'equal':
            share = float(round(amount / len(selected_ids), 2))
            splits_list = [{'member_id': mid, 'share_amount': share} for mid in selected_ids]
        else:
            splits_list = [{'member_id': mid,
                            'share_amount': float(request.form.get(f'custom_{mid}', 0) or 0)}
                           for mid in selected_ids]

        if is_admin:
            expense.description = description
            expense.amount = amount
            expense.currency = currency
            ExpenseSplit.query.filter_by(expense_id=expense.id).delete()
            for s in splits_list:
                db.session.add(ExpenseSplit(expense_id=expense.id,
                                            member_id=s['member_id'],
                                            share_amount=s['share_amount']))
            db.session.commit()
            flash('Expense updated.', 'success')
        else:
            req = EditRequest(expense_id=expense.id, requested_by=current_user.id,
                              new_description=description, new_amount=amount,
                              new_currency=currency)
            req.set_splits(splits_list)
            db.session.add(req)
            db.session.commit()
            flash('Edit request submitted — awaiting admin approval.', 'info')

        return redirect(url_for('groups.detail', group_id=group_id))

    return render_template('expenses/edit.html', expense=expense, group=group,
                           members=members, currencies=CURRENCIES,
                           current_splits=current_splits, is_admin=is_admin)


# ── DELETE ─────────────────────────────────────────────────────────────────────
@expenses.route('/<int:expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if not current_user.is_admin_of(expense.group_id):
        abort(403)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted.', 'success')
    return redirect(url_for('groups.detail', group_id=expense.group_id))


# ── BALANCES ───────────────────────────────────────────────────────────────────
@expenses.route('/group/<int:group_id>/balances')
@login_required
def balances(group_id):
    group = Group.query.get_or_404(group_id)
    if not current_user.is_member_of(group_id):
        abort(403)

    settlements = _compute_balances(group_id)
    members = GroupMember.query.filter_by(group_id=group_id, status='active').all()

    # Pre-fetch expense IDs in this group for efficient lookup
    group_expense_ids = {e.id for e in Expense.query.filter_by(group_id=group_id).all()}

    net_summary = []
    for m in members:
        total_paid = sum(float(e.amount) for e in m.expenses_paid
                         if e.group_id == group_id)
        total_owed = sum(float(s.share_amount) for s in m.splits
                         if s.expense_id in group_expense_ids)
        net_summary.append({'name': m.name, 'total_paid': round(total_paid, 2),
                             'total_owed': round(total_owed, 2),
                             'net': round(total_paid - total_owed, 2),
                             'is_registered': m.is_registered})

    return render_template('expenses/balances.html', group=group,
                           settlements=settlements, net_summary=net_summary)


# ── APPROVE / REJECT EDIT REQUEST ─────────────────────────────────────────────
@expenses.route('/requests/<int:request_id>/approve', methods=['POST'])
@login_required
def approve_request(request_id):
    edit_req = EditRequest.query.get_or_404(request_id)
    expense = edit_req.expense
    if not current_user.is_admin_of(expense.group_id):
        abort(403)

    expense.description = edit_req.new_description
    expense.amount = edit_req.new_amount
    expense.currency = edit_req.new_currency
    ExpenseSplit.query.filter_by(expense_id=expense.id).delete()
    for s in edit_req.get_splits():
        db.session.add(ExpenseSplit(expense_id=expense.id,
                                    member_id=s['member_id'],
                                    share_amount=s['share_amount']))
    edit_req.status = 'approved'
    edit_req.reviewed_at = datetime.utcnow()
    edit_req.reviewed_by = current_user.id
    db.session.commit()
    flash('Edit approved and applied.', 'success')
    return redirect(url_for('groups.detail', group_id=expense.group_id))


@expenses.route('/requests/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_request(request_id):
    edit_req = EditRequest.query.get_or_404(request_id)
    if not current_user.is_admin_of(edit_req.expense.group_id):
        abort(403)
    edit_req.status = 'rejected'
    edit_req.reviewed_at = datetime.utcnow()
    edit_req.reviewed_by = current_user.id
    db.session.commit()
    flash('Edit request rejected.', 'info')
    return redirect(url_for('groups.detail', group_id=edit_req.expense.group_id))
