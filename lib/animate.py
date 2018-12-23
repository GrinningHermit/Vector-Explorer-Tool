"""

Animations for Vector
============================

Supporting file for the Vector Explorer Tool for Vector SDK:

More info at https://developer.anki.com

Created by: GrinningHermit

=====

"""


import json
import time

from flask import Blueprint, request

animate = Blueprint('animate', __name__)

robot = None
return_to_pose = False
animations = ''
triggers = ''
behaviors = ''
action = []
pose = None

@animate.route('/toggle_pose', methods=['POST'])
def toggle_pose():
    global return_to_pose
    # Toggle for returning to pose after finishing animation
    return_to_pose = not return_to_pose
    print('return_to_pose is set to: ' + str(return_to_pose))
    return str(return_to_pose)


@animate.route('/play_animation', methods=['POST'])
def play_animation():
    # Handling of received animation
    global pose
    animation = json.loads(request.data.decode('utf-8'))
    print('Animation \'' + animation + '\' started')
    robot.anim.play_animation(animation)
    print('Animation \'' + animation + '\' ended')

    return 'true'

@animate.route('/stop', methods=['POST'])
def stop():
    global action
    if action is not []:
        robot.stop_freeplay_behaviors()
        print('behavior \'' + action[1] + '\' stopped')
        action = []
        check_pose_return()
    else:
        robot.abort_all_actions()

    return 'false'


def check_pose_return():
    if return_to_pose:
        # robot.go_to_pose(pose)
        print('Vector returning to pose he had before animation started')

def init_animate(_robot):
    global robot
    robot = _robot

    anim_list = ''
    anim_names = []
    all_anim_names = robot.anim.anim_list

    bad_anim_names = [
        "ANIMATION_TEST",
        "soundTestAnim"]

    for anim_name in all_anim_names:
        if anim_name not in bad_anim_names:
            anim_names.append(anim_name)

    for a in anim_names:
        anim_list += a + ','
    anim_list = anim_list[:-1]

    return anim_list

