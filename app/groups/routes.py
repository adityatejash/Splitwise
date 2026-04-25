import uuid, random
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from .. import db
from ..models import Group, GroupMember, User, Expense, EditRequest, JoinRequest
from . import groups


def _gen_join_code():
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    for _ in range(20):
        code = ''.join(random.choices(chars, k=6))
        if not Group.query.filter_by(join_code=code).first():
            return code
    return uuid.uuid4().hex[:6].upper()


# ── LIST ──────────────────────────────────────────────────────────────────────
@groups.route('/')
@login_required
def list_groups():
    memberships = GroupMember.query.filter_by(user_id=current_user.id, status='active').all()
    group_ids = [m.group_id for m in memberships]
    my_groups = Group.query.filter(Group.id.in_(group_ids)).order_by(Group.created_at.desc()).all()
    return render_template('groups/list.html', my_groups=my_groups)


# ── CREATE ─────────────────────────────────────────────────────────────────────
@groups.route('/create', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        if not name:
            flash('Group name is required.', 'error')
            return render_template('groups/create.html')
            
        # Enforce max 5 groups per user constraint
        active_memberships = GroupMember.query.filter_by(user_id=current_user.id, status='active').count()
        if active_memberships >= 5:
            flash('Group limit reached. You can only be a member of up to 5 groups (Free Tier limit).', 'error')
            return redirect(url_for('groups.list_groups'))

        group = Group(
            name=name,
            description=description,
            created_by=current_user.id,
            invite_token=uuid.uuid4().hex,
            join_code=_gen_join_code(),
        )
        db.session.add(group)
        db.session.flush()

        db.session.add(GroupMember(
            group_id=group.id, user_id=current_user.id,
            name=current_user.username, role='admin', status='active'
        ))
        db.session.commit()
        flash(f'Group "{name}" created!', 'success')
        return redirect(url_for('groups.detail', group_id=group.id))

    return render_template('groups/create.html')


# ── DETAIL ─────────────────────────────────────────────────────────────────────
@groups.route('/<int:group_id>')
@login_required
def detail(group_id):
    group = Group.query.get_or_404(group_id)
    if not current_user.is_member_of(group_id):
        abort(403)

    active_members = GroupMember.query.filter_by(group_id=group_id, status='active').all()
    expenses = (Expense.query.filter_by(group_id=group_id)
                .order_by(Expense.created_at.desc()).limit(10).all())
    is_admin = current_user.is_admin_of(group_id)

    pending_edits, pending_joins = [], []
    if is_admin:
        pending_edits = (EditRequest.query.join(Expense)
                         .filter(Expense.group_id == group_id, EditRequest.status == 'pending')
                         .order_by(EditRequest.created_at.desc()).all())
        pending_joins = (JoinRequest.query
                         .filter_by(group_id=group_id, status='pending')
                         .order_by(JoinRequest.created_at.desc()).all())

    invite_url = url_for('groups.join_invite', token=group.invite_token, _external=True)
    return render_template('groups/detail.html',
                           group=group, active_members=active_members,
                           expenses=expenses, is_admin=is_admin,
                           pending_edits=pending_edits, pending_joins=pending_joins,
                           invite_url=invite_url)


# ── ADD MEMBER (name or email) ─────────────────────────────────────────────────
@groups.route('/<int:group_id>/add-member', methods=['POST'])
@login_required
def add_member(group_id):
    if not current_user.is_admin_of(group_id):
        abort(403)
    group = Group.query.get_or_404(group_id)
    add_type = request.form.get('add_type', 'name')

    if add_type == 'email':
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash('Enter an email address.', 'error')
            return redirect(url_for('groups.detail', group_id=group_id))
        user = User.query.filter_by(email=email, is_guest=False).first()
        if not user:
            flash(f'No account found for "{email}". Add them by name instead.', 'warning')
            return redirect(url_for('groups.detail', group_id=group_id))
        if user.is_member_of(group_id):
            flash(f'{user.username} is already in this group.', 'warning')
            return redirect(url_for('groups.detail', group_id=group_id))
        db.session.add(GroupMember(group_id=group_id, user_id=user.id,
                                   name=user.username, role='member', status='active'))
        db.session.commit()
        flash(f'{user.username} added.', 'success')

    else:  # name-only (no account)
        name = request.form.get('member_name', '').strip()
        if not name:
            flash('Enter a member name.', 'error')
            return redirect(url_for('groups.detail', group_id=group_id))
        db.session.add(GroupMember(group_id=group_id, user_id=None,
                                   name=name, role='member', status='active'))
        db.session.commit()
        flash(f'"{name}" added as a placeholder member.', 'success')

    return redirect(url_for('groups.detail', group_id=group_id))


# ── REMOVE / PROMOTE ───────────────────────────────────────────────────────────
@groups.route('/<int:group_id>/remove-member/<int:member_id>', methods=['POST'])
@login_required
def remove_member(group_id, member_id):
    if not current_user.is_admin_of(group_id):
        abort(403)
    m = GroupMember.query.filter_by(id=member_id, group_id=group_id).first_or_404()
    if m.user_id == current_user.id:
        flash('You cannot remove yourself.', 'error')
        return redirect(url_for('groups.detail', group_id=group_id))
    db.session.delete(m)
    db.session.commit()
    flash('Member removed.', 'success')
    return redirect(url_for('groups.detail', group_id=group_id))


@groups.route('/<int:group_id>/promote/<int:member_id>', methods=['POST'])
@login_required
def promote_member(group_id, member_id):
    if not current_user.is_admin_of(group_id):
        abort(403)
    m = GroupMember.query.filter_by(id=member_id, group_id=group_id).first_or_404()
    m.role = 'admin' if m.role == 'member' else 'member'
    db.session.commit()
    flash(f'{"Promoted to admin" if m.role == "admin" else "Demoted to member"}.', 'success')
    return redirect(url_for('groups.detail', group_id=group_id))


# ── INVITE LINK ────────────────────────────────────────────────────────────────
@groups.route('/invite/<token>', methods=['GET', 'POST'])
@login_required
def join_invite(token):
    group = Group.query.filter_by(invite_token=token).first_or_404()

    if current_user.is_member_of(group.id):
        flash('You are already a member of this group.', 'info')
        return redirect(url_for('groups.detail', group_id=group.id))

    if current_user.has_pending_request(group.id):
        flash('You already have a pending join request.', 'info')
        return render_template('groups/join.html', group=group, already_requested=True)

    if request.method == 'POST':
        try:
            jr = JoinRequest(group_id=group.id, user_id=current_user.id)
            db.session.add(jr)
            db.session.commit()
            flash('Join request sent! Waiting for admin approval.', 'success')
        except Exception:
            db.session.rollback()
            flash('Could not send request (already submitted?).', 'warning')
        return render_template('groups/join.html', group=group, already_requested=True)

    return render_template('groups/join.html', group=group, already_requested=False)


# ── JOIN BY CODE ───────────────────────────────────────────────────────────────
@groups.route('/join-by-code', methods=['GET', 'POST'])
@login_required
def join_by_code():
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        group = Group.query.filter_by(join_code=code).first()
        if not group:
            flash('Invalid join code. Please check and try again.', 'error')
            return render_template('groups/join_code.html')
        return redirect(url_for('groups.join_invite', token=group.invite_token))
    return render_template('groups/join_code.html')


# ── APPROVE / REJECT JOIN REQUEST ─────────────────────────────────────────────
@groups.route('/join-request/<int:req_id>/approve', methods=['POST'])
@login_required
def approve_join(req_id):
    jr = JoinRequest.query.get_or_404(req_id)
    if not current_user.is_admin_of(jr.group_id):
        abort(403)
    jr.status = 'approved'
    # Create active membership
    user = User.query.get(jr.user_id)
    existing = GroupMember.query.filter_by(user_id=jr.user_id, group_id=jr.group_id).first()
    if not existing:
        db.session.add(GroupMember(group_id=jr.group_id, user_id=jr.user_id,
                                   name=user.username, role='member', status='active'))
    db.session.commit()
    flash(f'{user.username} approved and added to the group.', 'success')
    return redirect(url_for('groups.detail', group_id=jr.group_id))


@groups.route('/join-request/<int:req_id>/reject', methods=['POST'])
@login_required
def reject_join(req_id):
    jr = JoinRequest.query.get_or_404(req_id)
    if not current_user.is_admin_of(jr.group_id):
        abort(403)
    jr.status = 'rejected'
    db.session.commit()
    flash('Join request rejected.', 'info')
    return redirect(url_for('groups.detail', group_id=jr.group_id))


# ── DELETE GROUP ──────────────────────────────────────────────────────────────
@groups.route('/<int:group_id>/delete', methods=['POST'])
@login_required
def delete_group(group_id):
    group = Group.query.get_or_404(group_id)
    if not current_user.is_admin_of(group_id):
        abort(403)
    
    db.session.delete(group)
    db.session.commit()
    flash('Group deleted successfully.', 'success')
    return redirect(url_for('groups.list_groups'))


# ── EXPORT PDF ────────────────────────────────────────────────────────────────
@groups.route('/<int:group_id>/export-pdf')
@login_required
def export_pdf(group_id):
    from flask import send_file
    from .pdf import generate_group_pdf
    from ..expenses.routes import _compute_balances
    
    group = Group.query.get_or_404(group_id)
    if not current_user.is_member_of(group_id):
        abort(403)
        
    members = group.get_active_members()
    expenses = Expense.query.filter_by(group_id=group_id).order_by(Expense.expense_date.asc()).all()
    
    settlements = _compute_balances(group_id)
    
    group_expense_ids = {e.id for e in expenses}
    net_summary = []
    for m in members:
        total_paid = sum(float(e.amount) for e in m.expenses_paid if e.group_id == group_id)
        total_owed = sum(float(s.share_amount) for s in m.splits if s.expense_id in group_expense_ids)
        net_summary.append({
            'name': m.name, 
            'total_paid': round(total_paid, 2),
            'total_owed': round(total_owed, 2),
            'net': round(total_paid - total_owed, 2),
            'is_registered': m.is_registered
        })
        
    pdf_buffer = generate_group_pdf(group, members, expenses, settlements, net_summary)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"splitwise_{group.name.replace(' ', '_')}.pdf",
        mimetype='application/pdf'
    )
