"""

Remote control for Vector
============================

Based on remote_control.py for Vector SDK:
https://developer.anki.com

Created by: Anki

Edited by: GrinningHermit

Code from example file is separated in 2 functionalities:
- viewer / robot camera <-- this is where you are
- keyboard command handling

=====

"""


import json
import io
from io import BytesIO
import logging
import math
from flask import request, make_response, send_file, Blueprint, Response
from time import sleep
pil_installed = False
try:
    from PIL import Image, ImageDraw, ImageFont
    pil_installed = True
except ImportError:
    logging.warning("Cannot import from PIL: Do `pip3 install --user Pillow` to install")

viewer = Blueprint('viewer', __name__)

robot = None
vectorEnabled = False
show_state_info = True


def stream_video(streaming_function):
    return Response(streaming_function(), mimetype='multipart/x-mixed-replace; boundary=frame')


def streaming_video():
    """Video streaming generator function"""
    while True:
        if vectorEnabled:
            image = get_annotated_image()

            img_io = io.BytesIO()
            image.save(img_io, 'PNG')
            img_io.seek(0)
            yield (b'--frame\r\n'
                   b'Content-Type: image/png\r\n\r\n' + img_io.getvalue() + b'\r\n')
        else:
            sleep(.1)


def create_default_image(image_width, image_height, do_gradient=False):
    """Create a place-holder PIL image to use until we have a live feed from Vector"""
    image_bytes = bytearray([0x70, 0x70, 0x70]) * image_width * image_height

    if do_gradient:
        i = 0
        for y in range(image_height):
            for x in range(image_width):
                image_bytes[i] = int(255.0 * (x / image_width))   # R
                image_bytes[i + 1] = int(255.0 * (y / image_height))  # G
                image_bytes[i + 2] = 0                                # B
                i += 3

    image = Image.frombytes('RGB', (image_width, image_height), bytes(image_bytes))
    return image


if pil_installed:
    _default_camera_image = create_default_image(640, 360)


def get_annotated_image():
    # TODO: Update to use annotated image (add annotate module)
    global robot
    image = robot.camera.latest_image
    if image is None:
        return _default_camera_image

    return image.annotate_image()


def serve_single_image():
    if vectorEnabled:
        image = get_annotated_image()
        if image:
            return serve_pil_image(image)

    return serve_pil_image(_default_camera_image)

def is_microsoft_browser(req):
    agent = req.user_agent.string
    return 'Edge/' in agent or 'MSIE ' in agent or 'Trident/' in agent


def update_state_info(socketio):
    if show_state_info:
        prox = 'not available'
        try:
            prox = '%.3f mm' % robot.proximity.last_valid_sensor_reading.distance.distance_mm
        except:
            pass
        socketio.emit('state_info', {
            'type': 'event', 
            'position': 'X %.1f Y %.1f Z %.1f' % robot.pose.position.x_y_z, 
            'quaternion': 'q0 %.1f q1 %.1f q2 %.1f q3 %.1f' % robot.pose.rotation.q0_q1_q2_q3, 
            'angle_z': '%.1f\u00b0' % robot.pose.rotation.angle_z.degrees,
            'accel': 'X %.1f Y %.1f Z %.1f' % robot.accel.x_y_z,
            'gyro': 'X %.1f Y %.1f Z %.1f' % robot.gyro.x_y_z,
            'head': '%.2f\u00b0' % math.degrees(robot.head_angle_rad),
            'lift': '%.2f mm/s' % robot.lift_height_mm,
            'l_wheel': '%.3f mm/s' % robot.left_wheel_speed_mmps,
            'r_wheel': '%.3f mm/s' % robot.right_wheel_speed_mmps,
            'proximity': prox
        })


@viewer.route("/vectorImage")
def handle_vectorImage():
    if vectorEnabled and pil_installed:
        if is_microsoft_browser(request):
            return serve_single_image()
        return stream_video(streaming_video)
    return ''


@viewer.route('/show_state_info', methods=['POST'])
def handle_show_state_info():
    message = json.loads(request.data.decode("utf-8"))
    global show_state_info
    show_state_info = message['infoToggle']
    return ""


def make_uncached_response(in_file):
    response = make_response(in_file)
    response.headers['Pragma-Directive'] = 'no-cache'
    response.headers['Cache-Directive'] = 'no-cache'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


def serve_pil_image(pil_img, serve_as_jpeg=False, jpeg_quality=70):
    """Convert PIL image to relevant image file and send it"""
    img_io = BytesIO()

    if serve_as_jpeg:
        pil_img.save(img_io, 'JPEG', quality=jpeg_quality)
        img_io.seek(0)
        return make_uncached_response(send_file(img_io, mimetype='image/jpeg',
                                                add_etags=False))
    pil_img.save(img_io, 'PNG')
    img_io.seek(0)
    return make_uncached_response(send_file(img_io, mimetype='image/png',
                                            add_etags=False))


def activate_viewer_if_enabled(_robot):
    global robot
    global vectorEnabled
    robot = _robot
    if pil_installed:
        # robot.world.image_annotator.add_annotator('robotState', RobotStateDisplay)
        # Turn on image receiving by the camera
        vectorEnabled = True
        robot.camera.init_camera_feed()
        return True
    else:
        return False