import uuid
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from .. import db, limiter
from ..models import User
from . import auth


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated and not getattr(current_user, 'is_guest', False):
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')

        if len(username) < 3:
            flash('Username must be at least 3 characters.', 'error')
            return render_template('auth/register.html')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Username is already taken.', 'error')
            return render_template('auth/register.html')

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Clean up guest session if they are registering from one
        was_guest = getattr(current_user, 'is_guest', False)
        guest_id = getattr(current_user, 'id', None)
        
        if current_user.is_authenticated:
            logout_user()
            
        if was_guest and guest_id:
            guest = User.query.get(guest_id)
            if guest:
                db.session.delete(guest)
                db.session.commit()

        login_user(user)
        flash(f'Welcome, {username}! Your account has been created.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/register.html')


@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated and not getattr(current_user, 'is_guest', False):
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email, is_guest=False).first()

        if user is None or not user.check_password(password):
            flash('Invalid email or password.', 'error')
            return render_template('auth/login.html')

        # Clean up guest session if they are logging in from one
        was_guest = getattr(current_user, 'is_guest', False)
        guest_id = getattr(current_user, 'id', None)
        
        if current_user.is_authenticated:
            logout_user()
            
        if was_guest and guest_id:
            guest = User.query.get(guest_id)
            if guest:
                db.session.delete(guest)
                db.session.commit()

        login_user(user, remember=remember)
        next_page = request.args.get('next')
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(next_page or url_for('main.dashboard'))

    return render_template('auth/login.html')


@auth.route('/guest', methods=['POST'])
def guest_login():
    """Create an ephemeral guest session."""
    guest_id = uuid.uuid4().hex[:8]
    guest = User(
        username=f'Guest-{guest_id}',
        email=None,
        is_guest=True
    )
    db.session.add(guest)
    db.session.commit()
    login_user(guest)
    flash('You are browsing as a guest. Your data will be lost when you close the tab.', 'warning')
    return redirect(url_for('main.dashboard'))


@auth.route('/guest/cleanup', methods=['POST'])
def guest_cleanup():
    """Called by JS beforeunload to delete guest user."""
    if current_user.is_authenticated and getattr(current_user, 'is_guest', False):
        user_id = getattr(current_user, 'id', None)
        logout_user()
        
        if user_id:
            guest = User.query.get(user_id)
            if guest:
                db.session.delete(guest)
                db.session.commit()
    return '', 204


@auth.route('/logout')
@login_required
def logout():
    is_guest = getattr(current_user, 'is_guest', False)
    user_id = getattr(current_user, 'id', None)
    
    logout_user()
    
    if is_guest and user_id:
        guest = User.query.get(user_id)
        if guest:
            db.session.delete(guest)
            db.session.commit()
        flash('Guest session ended. See you!', 'info')
    else:
        flash('You have been logged out.', 'info')
        
    return redirect(url_for('auth.login'))
