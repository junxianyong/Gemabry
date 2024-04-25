import datetime
import json
import os
import random
import string
from PIL import Image, ImageDraw
from flask import jsonify, redirect, render_template, request, session, url_for
from app_pages.decorators import login_required, login_required_api 
from db.db import DBConnection
from __main__ import app

def generate_random_gradient():
    color1, color2 = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    img = Image.new('RGB', (500, 500))
    draw = ImageDraw.Draw(img)
    for y in range(500):
        r = int(color1[0] * (1 - y / 500) + color2[0] * (y / 500))
        g = int(color1[1] * (1 - y / 500) + color2[1] * (y / 500))
        b = int(color1[2] * (1 - y / 500) + color2[2] * (y / 500))
        draw.line([(0, y), (499, y)], fill=(r, g, b))
    return img

def save_image(file):
    if file and file.filename:
        image = Image.open(file)
        image = image.convert('RGB')
    else:
        image = generate_random_gradient()

    filename = f"{random_filename()}.jpg"
    file_path = os.path.join('static', 'icons', filename)
    image.save(file_path, 'JPEG', quality=85)
    return filename

def random_filename():
    now = datetime.datetime.now().strftime("%d%m%Y-%H%M")
    random_str = ''.join(random.choices(string.ascii_lowercase, k=6))
    return f"{random_str}-{now}"


@app.route('/prompt')
def prompt():
    prompt_id = request.args.get('promptid', type=int)
    user_id = session.get('user_id')

    with DBConnection() as cursor:
        cursor.execute(
            'SELECT * FROM Prompts WHERE PromptID = ?', (prompt_id,))
        prompt = cursor.fetchone()
        cursor.execute(
            'SELECT * FROM PromptContents WHERE PromptID = ?', (prompt_id,))
        prompt_content = cursor.fetchall()
        cursor.execute(
            'SELECT * FROM Stars WHERE PromptID = ? AND UserID = ?', (prompt_id,user_id)
        )
        if cursor.fetchone():
            is_starred = True
        else:
            is_starred = False

    return render_template('prompt.html', prompt=prompt, prompt_content=prompt_content, is_starred=is_starred)

@app.route('/add_prompt', methods=['GET', 'POST'])
@login_required
def add_prompt():
    if request.method == 'GET':
        return render_template('add_prompt.html')

    file = request.files.get('promptIcon')
    filename = save_image(file)
    form_data = request.form

    with DBConnection() as cursor:
        cursor.execute('INSERT INTO Prompts (PromptTitle, PromptDescription, PromptInstruction, PromptTemperature, PromptModel, UserID, PromptImage) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (form_data['promptTitle'], form_data['promptDescription'], form_data['promptInstruction'], float(form_data['promptTemperature']), form_data['promptModel'], session['user_id'], filename))

        prompt_id = cursor.lastrowid

        conversation_pairs = json.loads(form_data['conversation'])

        for pair in conversation_pairs:
            cursor.execute('INSERT INTO PromptContents (PromptRole, PromptContent, PromptID) VALUES (?, ?, ?)',
                        ('user', pair['userText'], prompt_id))
            cursor.execute('INSERT INTO PromptContents (PromptRole, PromptContent, PromptID) VALUES (?, ?, ?)',
                        ('model', pair['modelResponse'], prompt_id))
            
        return redirect(url_for('library'))

@app.route('/update_prompt', methods=['GET'])
@login_required
def edit_prompt():
    prompt_id = request.args.get('promptid', type=int)

    if not is_authorized_to_access(prompt_id):
        return redirect(url_for('index'))

    with DBConnection() as cursor:
        cursor.execute('SELECT * FROM Prompts WHERE PromptID = ?', (prompt_id,))
        prompt = cursor.fetchone()

        cursor.execute(
            'SELECT * FROM PromptContents WHERE PromptID = ?', (prompt_id,))
        conversation_pairs = cursor.fetchall()

    return render_template('update_prompt.html', prompt=prompt, conversation_pairs=conversation_pairs)

@app.route('/update_prompt', methods=['POST'])
@login_required_api
def update_prompt():
    form_data = request.form
    file = request.files.get('promptIcon')
    prompt_id = form_data['promptId']
    conversation_pairs = json.loads(form_data['conversation'])

    if not is_authorized_to_access(prompt_id):
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
    
    with DBConnection() as cursor:
        old_image = cursor.execute('SELECT PromptImage FROM Prompts WHERE PromptID = ?', (prompt_id,)).fetchone()

        if file:
            if old_image:
                os.remove(os.path.join('static', 'icons', old_image['PromptImage']))
            filename = save_image(file)
        else:
            filename = old_image['PromptImage']

        cursor.execute('UPDATE Prompts SET PromptTitle = ?, PromptDescription = ?, PromptInstruction = ?, PromptTemperature = ?, PromptModel = ?, PromptImage = ? WHERE PromptID = ?',
                   (form_data['promptTitle'], form_data['promptDescription'], form_data['promptInstruction'], float(form_data['promptTemperature']), form_data['promptModel'], filename, prompt_id))
    
        # Delete existing prompt contents and replace
        cursor.execute('DELETE FROM PromptContents WHERE PromptID = ?', (prompt_id,))

        for pair in conversation_pairs:
            cursor.execute('INSERT INTO PromptContents (PromptRole, PromptContent, PromptID) VALUES (?, ?, ?)',
                        ('user', pair['userText'], prompt_id))
            cursor.execute('INSERT INTO PromptContents (PromptRole, PromptContent, PromptID) VALUES (?, ?, ?)',
                        ('model', pair['modelResponse'], prompt_id))

    return redirect(url_for('library'))


@app.route('/delete_prompt', methods=['POST'])
@login_required_api
def delete_prompt():
    prompt_id = request.get_json()['promptId']

    if not is_authorized_to_access(prompt_id):
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    with DBConnection() as cursor:
        image = cursor.execute('SELECT PromptImage FROM Prompts WHERE PromptID = ?', (prompt_id,)).fetchone()
        
        if image:
            os.remove(os.path.join('static', 'icons', image['PromptImage']))

        cursor.execute('DELETE FROM PromptContents WHERE PromptID = ?', (prompt_id,))
        cursor.execute('DELETE FROM Prompts WHERE PromptID = ?', (prompt_id,))

    return jsonify({'message': 'Prompt deleted successfully'})

def is_authorized_to_access(prompt_id):
    user_id = session.get('user_id')  # Get user_id from session
    with DBConnection() as cursor:
        owner_check = cursor.execute('SELECT UserID FROM Prompts WHERE PromptID = ?', (prompt_id,)).fetchone()
        if not owner_check or owner_check['UserID'] != user_id:
            return False
    return True