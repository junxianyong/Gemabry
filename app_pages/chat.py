from flask import jsonify, redirect, render_template, request, session, url_for
from app_pages.decorators import login_required, login_required_api
from db.db import DBConnection
from utils.datetimehelper import get_current_unix_time
from __main__ import app

# Main Chat User Interface
@app.route('/chat')
@login_required
def chat():
    user_id = session.get('user_id')
    chat_id = request.args.get('chatid', type=int)

    if not is_chat_owner(chat_id) and chat_id is not None:
        return redirect(url_for('index'))

    with DBConnection() as cursor:
        cursor.execute('''SELECT Chats.*, MAX(ChatContents.ChatDateTime) AS MaxDateTime
                    FROM Chats
                    INNER JOIN ChatContents ON Chats.ChatID = ChatContents.ChatID
                    WHERE Chats.UserID = ?
                    GROUP BY Chats.ChatID
                    ORDER BY MaxDateTime DESC''', (user_id,))

        chat_list = cursor.fetchall()

        # Get conversation pairs from chat
        cursor.execute(
            'SELECT * FROM ChatContents WHERE ChatID = ?', (chat_id,))
        conversation_pairs = cursor.fetchall()

        # Get chat model
        cursor.execute('SELECT * FROM Chats WHERE ChatID = ?', (chat_id,))
        chat_detail = cursor.fetchone()

    # Render the chat template, passing the conversations data
    return render_template('chat.html', chat_list=chat_list, chat_detail=chat_detail, conversations=conversation_pairs, selected_chat=chat_id)

# Start a new chat based on promptid
@app.route('/new_chat', methods=['GET'])
@login_required
def new_chat():
    user_id = session['user_id']
    prompt_id = request.args.get('promptid', type=int)

    with DBConnection() as cursor:
        # Get prompt details, copy to chat table
        cursor.execute(
            'SELECT * FROM Prompts WHERE PromptID = ?', (prompt_id,))
        prompt = cursor.fetchone()

        cursor.execute('INSERT INTO Chats (ChatModel, ChatTitle, ChatTemperature, UserID) VALUES (?, ?, ?, ?)',
                       (prompt["PromptModel"], prompt["PromptTitle"], prompt["PromptTemperature"], user_id))

        chat_id = cursor.lastrowid

        # Get conversation pairs from prompt
        cursor.execute(
            'SELECT * FROM PromptContents WHERE PromptID = ?', (prompt_id,))
        conversation_pairs = cursor.fetchall()

        unix_time = get_current_unix_time()

        # Insert conversation pairs into chat table
        for pair in conversation_pairs:
            cursor.execute('INSERT INTO ChatContents (ChatRole, ChatContent, ChatStarter, ChatDateTime, ChatID) VALUES (?, ?, ?, ?, ?)',
                           (pair["PromptRole"], pair["PromptContent"], 1, unix_time, chat_id))

    return redirect(url_for('chat', chatid=chat_id))

@app.route('/update_chat_name', methods=['POST'])
@login_required_api
def update_chat_name():
    data = request.get_json()
    
    if not is_chat_owner(data['chatId']):
        return jsonify({'message': 'Unauthorized access'}), 403

    with DBConnection() as cursor:
        cursor.execute('UPDATE Chats SET ChatTitle = ? WHERE ChatID = ?', (data['newChatName'], data['chatId']))
    
    return jsonify({'message': 'Chat name updated successfully'})


@app.route('/delete_chat', methods=['POST'])
@login_required_api
def delete_chat():
    data = request.get_json()
    
    if not is_chat_owner(data['chatId']):
        return jsonify({'message': 'Unauthorized access'}), 403

    with DBConnection() as cursor:
        cursor.execute('DELETE FROM ChatContents WHERE ChatID = ?', (data['chatId'],))
        cursor.execute('DELETE FROM Chats WHERE ChatID = ?', (data['chatId'],))

    return jsonify({'message': 'Chat deleted successfully'})

# Will delete a single chat message belonging to model, and the user message that is one ID above it
@app.route('/delete_chat_message', methods=['POST'])
@login_required_api
def delete_chat_message():
    data = request.get_json()

    if not is_chat_owner(data['chatId']):
        return jsonify({'message': 'Unauthorized access'}), 403
    
    with DBConnection() as cursor:
        cursor.execute('DELETE FROM ChatContents WHERE ChatContentID = ?', (int(data['chatContentId']) - 1,))
        cursor.execute('DELETE FROM ChatContents WHERE ChatContentID = ?', (data['chatContentId'],))

    return jsonify({'message': 'Chat message deleted successfully'})

def is_chat_owner(chat_id):
    user_id = session.get('user_id')
    with DBConnection() as cursor:
        owner_check = cursor.execute('SELECT UserID FROM Chats WHERE ChatID = ?', (chat_id,)).fetchone()
        if not owner_check or owner_check['UserID'] != user_id:
            return False
    return True