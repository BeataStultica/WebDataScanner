import random
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO,  emit
from threading import Thread, Event
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from Parser import WebParser

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app, )
thread = Thread()
thread_stop_event = Event()
class DataThread(Thread):
    def __init__(self, client, data):
        self.client = client
        self.data = data
        super(DataThread, self).__init__()
    def dataGenerator(self):
        print("Initialising")
        try:
            #while not thread_stop_event.isSet():
            parser = WebParser(time_w=int(self.data['time']), source_count=int(self.data['source_len']),
                               browser_name=self.data['browser'], text_minimum=int(self.data['text_len']),
                               is_compare=self.data['is_compared'], links=self.data['urls'],
                               query=self.data['keyword'], parse_type=self.data['parse_type'])
            result = parser.search_n()
            socketio.emit('responseMessage', {'data': result}, to=self.client)
            thread_stop_event.set()
                #time.sleep(self.delay)
        except KeyboardInterrupt:
            # kill()
            print("Keyboard  Interrupt")
    def run(self):
        self.dataGenerator()
@socketio.on('connect')
def test_connect():
    print('someone connected to websocket')
    emit('Message', {'data': 'Connected!'})


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
            thread = DataThread(request.sid, message['data']
                                )
            thread.start()
    else:
        print("Unknown command")

@socketio.on_error_default
def default_error_handler(e):
    print('An error occured:')
    print(e)




if __name__ == '__main__':
    # socketio.run(app, debug=False, host='0.0.0.0')
    http_server = WSGIServer(('localhost',5000), app, handler_class=WebSocketHandler)
    http_server.serve_forever()
