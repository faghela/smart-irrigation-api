"""
auth.py — المصادقة والتحقق
Authentication blueprint: login, logout, login_required decorator.
"""
from functools import wraps
from flask import (
    Blueprint, request, redirect, url_for,
    render_template, session, flash
)
from config import DASHBOARD_USER_ID, DASHBOARD_TOKEN

auth_bp = Blueprint('auth', __name__)


# ── Decorator ─────────────────────────────────────
def login_required(f):
    """Redirect to /login if user is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            flash('يرجى تسجيل الدخول أولاً | Please log in first.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ── Routes ────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Render login page and process credentials."""
    if session.get('logged_in'):
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        token   = request.form.get('access_token', '').strip()

        if user_id == DASHBOARD_USER_ID and token == DASHBOARD_TOKEN:
            session['logged_in'] = True
            session['user_id']   = user_id
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('بيانات الدخول غير صحيحة | Invalid credentials.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Clear the session and redirect to login."""
    session.clear()
    flash('تم تسجيل الخروج بنجاح | Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))
