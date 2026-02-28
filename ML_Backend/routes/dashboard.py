"""
routes/dashboard.py — لوحة التحكم
Dashboard blueprint: root redirect + dashboard page.
"""
from flask import Blueprint, redirect, url_for, render_template, session
from auth import login_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    """Root → redirect to dashboard (or login if not authenticated)."""
    return redirect(url_for('dashboard.dashboard'))


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Serve the main dashboard page."""
    return render_template('dashboard.html', user_id=session.get('user_id'))
