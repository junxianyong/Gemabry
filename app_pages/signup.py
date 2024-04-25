from flask import flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash
from app_pages.decorators import logged_in_redirect
from db.db import DBConnection
from __main__ import app

@app.route('/signup', methods=['GET', 'POST'])
@logged_in_redirect
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        # Check if email already exists
        with DBConnection() as cursor:
            cursor.execute('SELECT * FROM Users WHERE UserEmail = ?', (email,))
            if cursor.fetchone():
                flash('Email already exists. Please use a different email.', 'danger')
                return render_template('signup.html')

        # Insert the new user into the database
        cursor.execute('INSERT INTO Users (UserName, UserEmail, UserPassword) VALUES (?, ?, ?)',
                    (name, email, hashed_password))
        flash('Sign up successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')