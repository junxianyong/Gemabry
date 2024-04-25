from flask import jsonify, request, session
from app_pages.decorators import login_required_api
from db.db import DBConnection
from utils.datetimehelper import get_current_unix_time
from __main__ import app

@app.route('/toggle_star', methods=['POST'])
@login_required_api
def toggle_star():
    data = request.get_json()
    prompt_id = data['promptId']

    unix_time = get_current_unix_time()

    with DBConnection() as cursor:
        cursor.execute("SELECT * FROM Stars WHERE userid=? AND promptid=?", (session['user_id'], prompt_id))
        star_entry = cursor.fetchone()

        if star_entry:
            cursor.execute("DELETE FROM Stars WHERE userid=? AND promptid=?", (session['user_id'], prompt_id)) 
        else:
            cursor.execute("INSERT INTO Stars (userid, promptid, stardatetime) VALUES (?, ?, ?)",
                           (session['user_id'], prompt_id, unix_time))

    return jsonify({'success': True})