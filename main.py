import random
import time
from flask import Flask, render_template
from flask_socketio import SocketIO,  emit
from threading import Lock


async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

@app.route('/')
def index():
    return render_template('index.html',
                           sync_mode=socketio.async_mode)


if __name__ == '__main__':
    socketio.run(app, debug=True)

