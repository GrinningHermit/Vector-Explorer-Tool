import io
import json
import sys
import time
import logging
import random
from lib import flask_socket_helpers
from lib.animate import animate, init_animate
from lib.viewer import viewer, activate_viewer_if_enabled, create_default_image
from lib.remote_control import remote_control, activate_controls

try:
    from flask import Flask, render_template
except ImportError:
    sys.exit("Cannot import from flask: Do `pip3 install --user flask` to install")

app = Flask(__name__)
app.register_blueprint(animate)
app.register_blueprint(viewer)
app.register_blueprint(remote_control)
async_mode = 'threading'
rndID = random.randrange(1000000000, 9999999999)
animation_list = ''
active_viewer = False
_default_camera_image = create_default_image(640, 360)


try:
    from flask_socketio import SocketIO, emit, disconnect
    socketio = SocketIO(app, async_mode=async_mode)
    flask_socketio_installed = True
except ImportError:
    logging.warning('Cannot import from flask_socketio: Do `pip3 install --user flask-socketio` to install\nProgram runs without flask_socketio, but there will be no event monitoring')
    socketio = None
    flask_socketio_installed = False

try:
    import eventlet
    eventlet_installed = True
except ImportError:
    logging.warning('Cannot import from eventlet: Do `pip3 install --user eventlet` to install\nEvent monitoring works, but performance is decreased')  
    eventlet_installed = False

try:
    import anki_vector
    from anki_vector import util
except ImportError:
    sys.exit("Cannot import anki_vector: Do `pip3 install -e .` in the vector home folder to install")


def start_server():
    if flask_socketio_installed:
        flask_socket_helpers.run_flask(socketio, app)
    else:
        flask_socket_helpers.run_flask(None, app)


@app.route('/')
def index():
    return render_template('index.html', randomID=rndID, animations=animation_list, triggers='', behaviors='', hasSocketIO=flask_socketio_installed,hasPillow=active_viewer)


def run():
    # flask_socket_helpers.run_flask(socketio, app)

    args = util.parse_command_args()

    with anki_vector.Robot(args.serial, enable_camera_feed=True) as robot:
        global animation_list
        global active_viewer

        animation_list = init_animate(robot)
        active_viewer = activate_viewer_if_enabled(robot)
        activate_controls(robot)
        start_server()


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt as e:
        pass
    except anki_vector.exceptions.VectorConnectionException as e:
        sys.exit("A connection error occurred: %s" % e)