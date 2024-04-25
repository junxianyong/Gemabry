from flask import redirect, session, url_for
from __main__ import app

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
