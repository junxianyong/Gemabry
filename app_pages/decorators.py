from functools import wraps
from flask import flash, jsonify, redirect, session, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'User not logged in'}), 401  # HTTP 401 Unauthorized status code
        return f(*args, **kwargs)
    return decorated_function

def logged_in_redirect(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
