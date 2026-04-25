from datetime import datetime
import json, uuid, random
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def _gen_token():
    return uuid.uuid4().hex


def _gen_code():
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(random.choices(chars, k=6))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    is_guest = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    memberships = db.relationship('GroupMember', backref='user', lazy='dynamic',
                                  foreign_keys='GroupMember.user_id')
    join_requests = db.relationship('JoinRequest', backref='user', lazy='dynamic',
                                    foreign_keys='JoinRequest.user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def get_membership(self, group_id):
        return GroupMember.query.filter_by(
            user_id=self.id, group_id=group_id, status='active').first()

    def is_admin_of(self, group_id):
        m = self.get_membership(group_id)
        return m is not None and m.role == 'admin'

    def is_member_of(self, group_id):
        return self.get_membership(group_id) is not None

    def has_pending_request(self, group_id):
        return JoinRequest.query.filter_by(
            user_id=self.id, group_id=group_id, status='pending').first() is not None

    def __repr__(self):
        return f'<User {self.username}>'


class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), default='')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invite_token = db.Column(db.String(32), unique=True, nullable=False,
                             default=_gen_token)
    join_code = db.Column(db.String(8), unique=True, nullable=False,
                          default=_gen_code)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by])
    members = db.relationship('GroupMember', backref='group', lazy='dynamic',
                              cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='group', lazy='dynamic',
                               cascade='all, delete-orphan')
    join_requests = db.relationship('JoinRequest', backref='group', lazy='dynamic',
                                    cascade='all, delete-orphan')

    def get_active_members(self):
        return self.members.filter_by(status='active').all()

    def get_member_count(self):
        return self.members.filter_by(status='active').count()


class GroupMember(db.Model):
    __tablename__ = 'group_members'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # nullable = non-registered
    name = db.Column(db.String(80), nullable=False)          # display name
    role = db.Column(db.String(10), default='member')        # admin / member
    status = db.Column(db.String(10), default='active')      # active / pending
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    expenses_paid = db.relationship('Expense', backref='payer', lazy='dynamic',
                                    foreign_keys='Expense.paid_by')
    splits = db.relationship('ExpenseSplit', backref='member', lazy='dynamic',
                             foreign_keys='ExpenseSplit.member_id')

    @property
    def is_registered(self):
        return self.user_id is not None


class JoinRequest(db.Model):
    __tablename__ = 'join_requests'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(10), default='pending')   # pending / approved / rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('group_id', 'user_id'),)


CURRENCIES = ['INR', 'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'SGD']


class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    paid_by = db.Column(db.Integer, db.ForeignKey('group_members.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(10), default='INR')
    expense_date = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    logger = db.relationship('User', foreign_keys=[created_by])
    splits = db.relationship('ExpenseSplit', backref='expense', lazy='dynamic',
                             cascade='all, delete-orphan')
    edit_requests = db.relationship('EditRequest', backref='expense', lazy='dynamic',
                                    cascade='all, delete-orphan')

    def has_pending_request(self):
        return self.edit_requests.filter_by(status='pending').first() is not None


class ExpenseSplit(db.Model):
    __tablename__ = 'expense_splits'
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('group_members.id'), nullable=False)
    share_amount = db.Column(db.Numeric(12, 2), nullable=False)


class EditRequest(db.Model):
    __tablename__ = 'edit_requests'
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=False)
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    new_description = db.Column(db.String(255))
    new_amount = db.Column(db.Numeric(12, 2))
    new_currency = db.Column(db.String(10))
    new_splits_json = db.Column(db.Text)   # [{member_id, share_amount}]
    status = db.Column(db.String(10), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    requester = db.relationship('User', foreign_keys=[requested_by])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])

    def get_splits(self):
        return json.loads(self.new_splits_json) if self.new_splits_json else []

    def set_splits(self, splits_list):
        self.new_splits_json = json.dumps(splits_list)
