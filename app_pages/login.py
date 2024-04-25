from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from app_pages.decorators import logged_in_redirect
from db.db import DBConnection
from __main__ import app

@app.route('/login', methods=['GET', 'POST'])
@logged_in_redirect
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        with DBConnection() as cursor:
            cursor.execute("SELECT * FROM Users WHERE UserEmail=?", (email,))
            user = cursor.fetchone()

        if user and check_password_hash(user['UserPassword'], password):
            session['user_id'] = user['UserID']
            session['user_name'] = user['UserName']
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials, please try again.', 'danger')
        
    return render_template('login.html')