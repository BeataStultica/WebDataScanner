import random
import time
from flask import Flask, render_template, request
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO,  emit, join_room, leave_room
from threading import Thread, Event
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app, )
thread = Thread()
thread_stop_event = Event()
class DataThread(Thread):
    def __init__(self, client):
        self.client = client
        self.delay = 10
        super(DataThread, self).__init__()
    def dataGenerator(self):
        print("Initialising")
        try:
            while not thread_stop_event.isSet():
                socketio.emit('responseMessage', {'temperature': round(random.random()*10, 3)}, to=self.client)
                time.sleep(self.delay)
        except KeyboardInterrupt:
            # kill()
            print("Keyboard  Interrupt")
    def run(self):
        self.dataGenerator()
@socketio.on('connect')
def test_connect():
    print('someone connected to websocket')
    emit('responseMessage', {'data': 'Connected! ayy'})
    # need visibility of the global thread object


@socketio.on('message')
def handle_message(message):
    # print('someone sent to the websocket', message)
    print('Data', message["data"])
    print('Status', message["status"])
    global thread
    global thread_stop_event
    if (message["status"]=="Off"):
        if thread.is_alive():
            thread_stop_event.set()
        else:
            print("Thread not alive")
    elif (message["status"]=="On"):
        if not thread.is_alive():
            thread_stop_event.clear()
            print("Starting Thread")
            thread = DataThread(request.sid)
            thread.start()
    else:
        print("Unknown command")

@socketio.on_error_default  # handles all namespaces without an explicit error handler
def default_error_handler(e):
    print('An error occured:')
    print(e)


@app.route('/')
def index():
    return "Hello"


if __name__ == '__main__':
    # socketio.run(app, debug=False, host='0.0.0.0')
    http_server = WSGIServer(('localhost',5000), app, handler_class=WebSocketHandler)
    http_server.serve_forever()
