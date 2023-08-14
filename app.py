from flask import Flask, request
from views import views, new_message, on_connect, on_disconnect
from flask_socketio import SocketIO



app = Flask(__name__)
app.register_blueprint(views, url_prefix="/")
app.config['SECRET_KEY'] = 'Projeto-ECO'
socketio = SocketIO(app)


@socketio.on("connect")
def connect(auth):
    place = request.referrer.split("/")[-2]
    if "chat" in place:
        on_connect(auth, place)
    elif place == "profile":
        place += "/" + request.referrer.split("/")[-1]
        on_connect(auth, place)
        place = place.split("/")[-1]



@socketio.on("message")
def message(data):
    new_message(data)



@socketio.on("disconnect")
def disconnect():
    place = request.referrer.split("/")[-2]
    if place == "profile":
        place += "/" + request.referrer.split("/")[-1]
    on_disconnect(place)


if __name__ == "__main__":
    socketio.run(app, debug=True, host = "192.168.1.64", port = 6070)


# Links
# http://financialtipeco.online:6070/
# http://www.financialtipeco.online:6070/
