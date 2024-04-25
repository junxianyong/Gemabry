from flask import Flask
from markupsafe import Markup, escape
import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Import the routes
import app_pages.index
import app_pages.library
import app_pages.comment
import app_pages.star
import app_pages.prompt
import app_pages.chat
import app_pages.login
import app_pages.manage_profile
import app_pages.logout
import app_pages.signup
import app_pages.gemini_api

@app.template_filter('nl2br')
def nl2br(value):
    # First escape all HTML tags potentially in the value
    escaped = escape(value)
    # Then convert newline characters to <br> HTML tags
    result = escaped.replace('\n', Markup('<br>'))
    return result

@app.template_filter('format_unix_timestamp')
def format_datetime(value):
    return datetime.datetime.fromtimestamp(value).strftime('%d/%b/%Y %I:%M %p')

if __name__ == '__main__':
    app.run(debug=True)