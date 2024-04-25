import io
import os
import uuid
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv
from flask import flash, jsonify, redirect, request, session, url_for
from app_pages.chat import is_chat_owner
from app_pages.decorators import login_required_api
from db.db import DBConnection
from utils.datetimehelper import get_current_unix_time

from __main__ import app

# Load environment variables and configure API
load_dotenv()
genai.configure(api_key=os.environ.get('API_KEY'))

# Safety settings for the model (Default to allow as much as possible)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
]

# Default generation config for the model
default_generation_config = {"temperature": 1.0, "top_p": 1, "top_k": 1, "max_output_tokens": 4096}

# Helper Functions
def get_chat_history(chat_id):
    with DBConnection() as cursor:
        cursor.execute("SELECT * FROM ChatContents WHERE ChatID = ?", (chat_id,))
        conversation_pairs = cursor.fetchall()
        return [{"role": pair["ChatRole"], "parts": [{"text": pair["ChatContent"]}]} for pair in conversation_pairs]

def handle_database_operations(chatid, messages, is_model_response):
    unix_time = get_current_unix_time()
    with DBConnection() as cursor:
        for message, role in messages:
            cursor.execute('INSERT INTO ChatContents (ChatRole, ChatContent, ChatStarter, ChatDateTime, ChatID) VALUES (?, ?, ?, ?, ?)',
                           (role, message, is_model_response, unix_time, chatid))

def handle_file_operations(file):
    if not os.path.exists("temp"):
        os.makedirs("temp")
    file_extension = os.path.splitext(file.filename)[1]
    random_filename = str(uuid.uuid4()) + file_extension
    file_path = os.path.join("temp", random_filename)
    file.save(file_path)
    return file_path

def generate_response(chat_id, model_name, config, content):
    history = get_chat_history(chat_id)
    
    # Use normal chat method for all models except pro-vision
    if (model_name != "gemini-pro-vision"):
        try:
            model = genai.GenerativeModel(model_name=model_name, generation_config=config, safety_settings=safety_settings)
            chat = model.start_chat(history=history)
            return chat.send_message(content=content).text
        except Exception as e:
            return str(e)
    else:
        # Iterate through history, combine user roles and messages into a single string
        chat_history = "Chat history: "
        for pair in history:
            chat_history += pair["parts"][0]["text"] + "\n"

        # Add new message to history to send as one single string
        chat_history += content[0]

        try:
            model = genai.GenerativeModel(model_name=model_name, generation_config=config, safety_settings=safety_settings)
            return model.generate_content([chat_history, content[1]]).text
        except Exception as e:
            return str(e)

# API Endpoints
@app.route("/generate_chat_title", methods=["POST"])
@login_required_api
def generate_chat_title():
    if request.method == "POST":
        data = request.get_json()
        chat_id = data['chatId']

        if not is_chat_owner(chat_id):
            return jsonify({'message': 'Unauthorized access'}), 403

        try:
            prompt_content = "A single short concise title based on the concept/content of our entire chat history so far. Do not use markdown."
            response_text = generate_response(chat_id, "gemini-1.5-pro-latest", default_generation_config, content=prompt_content)

            # Clean response, remove (*)
            response_text = response_text.replace("*", "")
            
            return jsonify({"response": response_text})
        except Exception as e:
            return jsonify({"response": str(e)}), 500
    else:
        return jsonify({"status": "Error", "message": "Invalid request"}), 405

# Generate response using gemini-pro 1.0 model (text-based)
@app.route("/generate_pro_text", methods=["POST"])
@login_required_api
def generate_pro_text():
    if request.method == "POST":
        chatid = request.form['chatid']
        message = request.form['message']
        generation_config = {"temperature": float(request.form['temperature']), "top_p": 1, "top_k": 1, "max_output_tokens": 2048}

        if not is_chat_owner(chatid):
            return jsonify({'message': 'Unauthorized access'}), 403
        
        try:
            response_text = generate_response(chatid, "gemini-pro", generation_config, message)
            handle_database_operations(chatid, [(message, "user"), (response_text, "model")], False)
            return jsonify({"response": response_text})
        except Exception as e:
            return jsonify({"response": str(e)}), 500
    else:
        return jsonify({"status": "Error", "message": "Invalid request"}), 405

# Generate response using gemini-pro-vision 1.0 (image-based)
@app.route("/generate_vision_text", methods=["POST"])
@login_required_api
def generate_vision_text():
    if request.method == "POST":
        message = request.form['message']
        image_file = request.files['file']
        chatid = request.form['chatid']
        generation_config = {"temperature": float(request.form['temperature']), "top_p": 1, "top_k": 1, "max_output_tokens": 4096}

        if not is_chat_owner(chatid):
            return jsonify({'message': 'Unauthorized access'}), 403
    
        if not image_file:
            return jsonify({"status": "Error", "message": "No image provided"}), 400
        try:
            image = Image.open(io.BytesIO(image_file.read()))
            response_text = generate_response(chatid, "gemini-pro-vision", generation_config, content=[message, image])
            handle_database_operations(chatid, [("📄 File Sent\n" + message, "user"), (response_text, "model")], False)
            return jsonify({"response": response_text})
        except Exception as e:
            return jsonify({"response": str(e)}), 500
    else:
        return jsonify({"status": "Error", "message": "Invalid request"}), 405

@app.route('/generate_pro_1.5_text', methods=['POST'])
@login_required_api
def generate_pro_1_5_text():
    if request.method == "POST":
        chatid = request.form['chatid']
        message = request.form['message']
        file = request.files.get('file')
        generation_config = {"temperature": float(request.form['temperature']), "top_p": 1, "top_k": 1, "max_output_tokens": 8192}

        if not is_chat_owner(chatid):
            return jsonify({'message': 'Unauthorized access'}), 403
    
        if file:
            file_path = handle_file_operations(file)
            try:
                uploaded_file = genai.upload_file(file_path)
                response_text = generate_response(chatid, "gemini-1.5-pro-latest", generation_config, content=[message, uploaded_file])
                handle_database_operations(chatid, [("📄 File Sent\n" + message, "user"), (response_text, "model")], False)
                genai.delete_file(uploaded_file)  # Clean up file after use
                os.remove(file_path)  # Clean up local file storage
                return jsonify({"response": response_text})
            except Exception as e:
                if os.path.exists(file_path):
                    os.remove(file_path)
                return jsonify({"response": str(e)}), 500
        else:
            try:
                response_text = generate_response(chatid, "gemini-1.5-pro-latest", generation_config, content=message)
                handle_database_operations(chatid, [(message, "user"), (response_text, "model")], False)
                return jsonify({"response": response_text})
            except Exception as e:
                return jsonify({"response": str(e)}), 500
    else:
        return jsonify({"status": "Error", "message": "Invalid request"}), 405

@app.route('/count_token', methods=['POST'])
@login_required_api
def count_token():
    chatid = request.form['chatid']
    if not is_chat_owner(chatid):
            return jsonify({'message': 'Unauthorized access'}), 403

    try:
        history = get_chat_history(chatid)
        model = genai.GenerativeModel('gemini-pro')
        response = model.count_tokens(history)
        return jsonify({"response": response.total_tokens})
    except Exception as e:
        return jsonify({"response": str(e)}), 500