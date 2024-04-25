import datetime
from flask import jsonify, request, session
from app_pages.decorators import login_required_api
from db.db import DBConnection
from utils.datetimehelper import get_current_unix_time
from __main__ import app

@app.route('/submit_comment', methods=['POST'])
@login_required_api
def submit_comment():
    if not 'user_id' in session:
        return jsonify({'success': False, 'message': 'User not logged in'})

    data = request.get_json()
    comment_text = data.get('comment')
    prompt_id = data.get('promptId')

    if not comment_text:
        return jsonify({'success': False, 'message': 'Comment cannot be empty'})

    with DBConnection() as cursor:
        cursor.execute("INSERT INTO Comments (promptid, userid, commentcontent, commentdatetime) VALUES (?, ?, ?, ?)", 
                       (prompt_id, session['user_id'], comment_text, get_current_unix_time()))

    return jsonify({'success': True, 'message': 'Comment added successfully'})

@app.route('/get_comments')
def get_comments():
    prompt_id = request.args.get('promptId', type=int)

    with DBConnection() as cursor:
        cursor.execute("""
            SELECT c.*, u.Username 
            FROM Comments c 
            JOIN Users u ON c.userid = u.UserID
            WHERE c.promptid = ?
            ORDER BY c.CommentDateTime DESC
        """, (prompt_id,))
        comments = cursor.fetchall()

    formatted_comments = []

    for comment in comments:
        comment_dict = dict(comment)
        comment_datetime = datetime.datetime.fromtimestamp(comment_dict['CommentDateTime']) 
        comment_dict['CommentDateTime'] = comment_datetime.strftime("%d/%b/%Y %I:%M %p")
        formatted_comments.append(comment_dict)
 
    return jsonify(formatted_comments)