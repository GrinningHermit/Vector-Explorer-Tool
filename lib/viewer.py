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

DEBUG_ANNOTATIONS_DISABLED = 0
DEBUG_ANNOTATIONS_ENABLED_VISION = 1
DEBUG_ANNOTATIONS_ENABLED_ALL = 2

robot = None
vectorEnabled = False
show_state_info = True

"""
# Annotator for displaying RobotState (position, etc.) on top of the camera feed
class RobotStateDisplay(cozmo.annotate.Annotator):
    def apply(self, image, scale):
        d = ImageDraw.Draw(image)

        bounds = [10, 5, image.width, image.height]
        bounds_shadow = [10, 6, image.width, image.height]
        font = ImageFont.truetype('static/fonts/LiberationSans-Bold.ttf', 15)
        def print_line(text_line):
            shadow = cozmo.annotate.ImageText(text_line, position=cozmo.annotate.TOP_LEFT, color='#000000', font=font)
            shadow.render(d, bounds_shadow)
            text = cozmo.annotate.ImageText(text_line, position=cozmo.annotate.TOP_LEFT, color='#ffffff', font=font)
            text.render(d, bounds)
            TEXT_HEIGHT = 15
            bounds[1] += TEXT_HEIGHT
            bounds_shadow[1] += TEXT_HEIGHT

        # Display the Pose info for the robot

        pose = robot.pose
        print_line('Pose: Pos = <%.1f, %.1f, %.1f>' % pose.position.x_y_z)
        print_line('Pose: Rot quat = <%.1f, %.1f, %.1f, %.1f>' % pose.rotation.q0_q1_q2_q3)
        print_line('Pose: angle_z = %.1f' % pose.rotation.angle_z.degrees)
        print_line('Pose: origin_id: %s' % pose.origin_id)

        # Display the Accelerometer and Gyro data for the robot

        print_line('Accelmtr: <%.1f, %.1f, %.1f>' % robot.accelerometer.x_y_z)
        print_line('Gyro: <%.1f, %.1f, %.1f>' % robot.gyro.x_y_z)
"""


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
    _display_debug_annotations = DEBUG_ANNOTATIONS_ENABLED_ALL


def get_annotated_image():
    # TODO: Update to use annotated image (add annotate module)
    global robot
    image = robot.camera.latest_image
    if image is None:
        return _default_camera_image

    return image


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


@viewer.route('/setAreDebugAnnotationsEnabled', methods=['POST'])
def handle_setAreDebugAnnotationsEnabled():
    # Called from Javascript whenever debug-annotations mode is toggled
    message = json.loads(request.data.decode("utf-8"))
    global _display_debug_annotations
    _display_debug_annotations = message['areDebugAnnotationsEnabled']
    if _display_debug_annotations == DEBUG_ANNOTATIONS_ENABLED_ALL:
        print('TO DO: annotations on')
        # robot.world.image_annotator.annotation_enabled = True
        # robot.world.image_annotator.enable_annotator('robotState')
    else:
        print('TO DO: annotations off')
        # robot.world.image_annotator.annotation_enabled = False
        # robot.world.image_annotator.disable_annotator('robotState')
    return ""

@viewer.route('/show_state_info', methods=['POST'])
def handle_show_state_info():
    global show_state_info
    show_state_info = not show_state_info
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
        return True
    else:
        return False