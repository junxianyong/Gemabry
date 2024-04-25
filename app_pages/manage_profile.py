from flask import flash, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from app_pages.decorators import login_required
from db.db import DBConnection
from __main__ import app

@app.route('/manage_profile', methods=['GET', 'POST'])
@login_required
def manage_profile():
    user_id = session['user_id']
    with DBConnection() as cursor:
        
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            current_password = request.form['current_password']
            new_password = request.form['new_password']

            # Fetch the existing user details
            cursor.execute('SELECT UserPassword FROM Users WHERE UserID = ?', (user_id,))
            user_data = cursor.fetchone()

            # Check current password
            if user_data and check_password_hash(user_data[0], current_password):
                # Update details
                hashed_password = generate_password_hash(new_password) if new_password else user_data[0]
                cursor.execute('UPDATE Users SET UserName=?, UserEmail=?, UserPassword=? WHERE UserID=?',
                            (name, email, hashed_password, user_id))
                flash('Profile updated successfully!', 'success')
            else:
                flash('Current password is incorrect.', 'danger')

        # Always fetch the latest user details to display in the form
        cursor.execute('SELECT UserName, UserEmail FROM Users WHERE UserID = ?', (user_id,))
        user_details = cursor.fetchone()

        # Update session data if the name has changed
        if user_details:
            session['user_name'] = user_details['UserName']
    
    return render_template('manage_profile.html', user_details=user_details)
