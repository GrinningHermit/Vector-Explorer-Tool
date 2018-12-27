import io
import json
import sys
import time
import datetime
import logging
import random
import queue
from lib.event_monitor import monitor
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

robot = None
async_mode = 'threading'
thread = None
rndID = random.randrange(1000000000, 9999999999)
os_info = ''
animation_list = ''
q = queue.Queue()
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


if flask_socketio_installed:
    socketio = SocketIO(app, async_mode=async_mode)

    # Functions for event monitoring
    def print_queue(qval):
        while qval.qsize() > 0:
            timestamp = '{:%H:%M:%S.%f}'.format(datetime.datetime.now())
            message = qval.get()
            message = message.replace('<','[')
            message = message.replace('>','] ')
            print(timestamp + ' -> ' + message)
            socketio.emit('event_monitor',
                {'data': message, 'type': 'event', 'time': timestamp})


    def update_state_info():
        socketio.emit('state_info', {
            'type': 'event', 
            'position': 'X %.1f Y %.1f Z %.1f' % robot.pose.position.x_y_z, 
            'quaternion': 'angle_z %.1f<br>' % robot.pose.rotation.angle_z.degrees, 
            'angle_z': 'angle_z %.1f<br>' % robot.pose.rotation.angle_z.degrees,
            'accel': 'Accel: <%.1f, %.1f, %.1f' % robot.accel.x_y_z,
            'gyro': 'Gyro: <%.1f, %.1f, %.1f' % robot.gyro.x_y_z,
            'head': 'Lift: height = %.1f' % robot.lift_height_mm,
            'lift': 'lWheel: %.3f mm/s' % robot.left_wheel_speed_mmps,
            'l_wheel': 'lWheel: %.3f mm/s' % robot.left_wheel_speed_mmps,
            'r_wheel': 'rWheel: %.3f mm/s' % robot.right_wheel_speed_mmps,
            'proximity': 'Range: %.3f mm' % robot.proximity.last_valid_sensor_reading.distance.distance_mm
        })


    def background_thread(qval):
        while True:
            if not qval.empty():
                print_queue(qval)
            if not robot == None:
                update_state_info()
            socketio.sleep(.1)


    @socketio.on('connect')
    def test_connect():
        global thread
        if thread is None:
            thread = socketio.start_background_task(background_thread, q)
        emit('event_monitor', {'data': 'SERVER: Websocket connection established.'})
        print('Websocket connection established')


    @socketio.on('disconnect')
    def test_disconnect():
        print('Websocket connection closed')


    @socketio.on('json_key_command')
    def handle_key_command(json):
        print('received json: ' + str(json))


def start_server():
    if flask_socketio_installed:
        flask_socket_helpers.run_flask(socketio, app)
    else:
        flask_socket_helpers.run_flask(None, app)


@app.route('/')
def index():
    return render_template(
        'index.html',
        activeRobot=str(robot), 
        randomID=rndID, 
        animations=animation_list, 
        triggers='', 
        behaviors='', 
        hasSocketIO=flask_socketio_installed,
        hasPillow=active_viewer,
        osInfo=os_info
    )


def run():
    args = util.parse_command_args()
    global robot

    with anki_vector.Robot(args.serial, enable_camera_feed=True, enable_custom_object_detection=True, enable_face_detection=True) as robot:
        global animation_list
        global active_viewer
        global os_info

        os_info = robot.conn.name + ',' + robot.conn.host + ',' + robot.get_version_state().os_version
        animation_list = init_animate(robot) # list of animations
        active_viewer = activate_viewer_if_enabled(robot) # camera and keyboard controls
        monitor(robot, q) # event monitor
        activate_controls(robot) # game controller
        start_server()


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt as e:
        sys.exit("Program aborted: %s" % e)
    except anki_vector.exceptions.VectorNotFoundException as e:
        # Test server mode without active Vector
        start_server()
    except anki_vector.exceptions.VectorConnectionException as e:
        sys.exit("A connection error occurred: %s" % e)