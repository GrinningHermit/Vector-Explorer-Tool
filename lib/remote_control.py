"""

Remote control for Vector
============================

Based on remote_control.py for Vector SDK:
https://developer.anki.com

Created by: Anki

Edited by: GrinningHermit

Code from example file is separated in 2 functionalities:
- viewer / robot camera
- keyboard command handling <-- this is where you are

=====

"""


import json
from flask import Blueprint, request


remote_control = Blueprint('remote_control', __name__)
robot = None
remote_control_vector = None


def remap_to_range(x, x_min, x_max, out_min, out_max):
    """convert x (in x_min..x_max range) to out_min..out_max range"""
    if x < x_min:
        return out_min
    elif x > x_max:
        return out_max
    else:
        ratio = (x - x_min) / (x_max - x_min)
        return out_min + ratio * (out_max - out_min)

class RemoteControlVector:
    def __init__(self, robot):
        self.vector = robot

        self.drive_forwards = 0
        self.drive_back = 0
        self.turn_left = 0
        self.turn_right = 0
        self.lift_up = 0
        self.lift_down = 0
        self.head_up = 0
        self.head_down = 0

        self.go_fast = 0
        self.go_slow = 0

        self.action_queue = []
        self.text_to_say = "Hi I'm Vector"


    def update_drive_state(self, key_code, is_key_down, speed_changed):
        """Update state of driving intent from keyboard, and if anything changed then call update_driving"""
        update_driving = True
        if key_code == ord('W'):
            self.drive_forwards = is_key_down
        elif key_code == ord('S'):
            self.drive_back = is_key_down
        elif key_code == ord('A'):
            self.turn_left = is_key_down
        elif key_code == ord('D'):
            self.turn_right = is_key_down
        else:
            if not speed_changed:
                update_driving = False
        return update_driving


    def update_head_state(self, key_code, is_key_down, speed_changed):
        """Update state of head move intent from keyboard, and if anything changed then call update_head"""
        update_head = True
        if key_code == ord('Q'):
            self.head_up = is_key_down
        elif key_code == ord('E'):
            self.head_down = is_key_down
        else:
            if not speed_changed:
                update_head = False
        return update_head


    def update_lift_state(self, key_code, is_key_down, speed_changed):
        """Update state of lift move intent from keyboard, and if anything changed then call update_lift"""
        update_lift = True
        if key_code == ord('R'):
            self.lift_up = is_key_down
        elif key_code == ord('F'):
            self.lift_down = is_key_down
        else:
            if not speed_changed:
                update_lift = False
        return update_lift
        
        
    def handle_key(self, key_code, is_shift_down, is_alt_down, is_key_down):
        """Called on any key press or release
           Holding a key down may result in repeated handle_key calls with is_key_down==True
        """

        # Update desired speed / fidelity of actions based on shift/alt being held
        was_go_fast = self.go_fast
        was_go_slow = self.go_slow

        self.go_fast = is_shift_down
        self.go_slow = is_alt_down

        speed_changed = (was_go_fast != self.go_fast) or (was_go_slow != self.go_slow)

        update_driving = self.update_drive_state(key_code, is_key_down, speed_changed)

        update_lift = self.update_lift_state(key_code, is_key_down, speed_changed)

        update_head = self.update_head_state(key_code, is_key_down, speed_changed)

        # Update driving, head and lift as appropriate
        if update_driving:
            self.update_mouse_driving()
        if update_head:
            self.update_head()
        if update_lift:
            self.update_lift()


    def pick_speed(self, fast_speed, mid_speed, slow_speed):
        if self.go_fast:
            if not self.go_slow:
                return fast_speed
        elif self.go_slow:
            return slow_speed
        return mid_speed


    def update_lift(self):
        lift_speed = self.pick_speed(8, 4, 2)
        lift_vel = (self.lift_up - self.lift_down) * lift_speed
        self.vector.motors.set_lift_motor(lift_vel)


    def update_head(self):
        # if not self.is_mouse_look_enabled:
            head_speed = self.pick_speed(2, 1, 0.5)
            head_vel = (self.head_up - self.head_down) * head_speed
            self.vector.motors.set_head_motor(head_vel)

    
    def update_mouse_driving(self):
        drive_dir = (self.drive_forwards - self.drive_back)

        turn_dir = (self.turn_right - self.turn_left)
        if drive_dir < 0:
            # It feels more natural to turn the opposite way when reversing
            turn_dir = -turn_dir

        forward_speed = self.pick_speed(150, 75, 50)
        turn_speed = self.pick_speed(100, 50, 30)

        l_wheel_speed = (drive_dir * forward_speed) + (turn_speed * turn_dir)
        r_wheel_speed = (drive_dir * forward_speed) - (turn_speed * turn_dir)

        self.vector.motors.set_wheel_motors(l_wheel_speed, r_wheel_speed, l_wheel_speed * 4, r_wheel_speed * 4)


def handle_key_event(key_request, is_key_down):
    global remote_control_vector
    message = json.loads(key_request.data.decode("utf-8"))
    if remote_control_vector:
        remote_control_vector.handle_key(key_code=(message['keyCode']), is_shift_down=message['hasShift'], is_alt_down=message['hasAlt'], is_key_down=is_key_down)
    return ""

@remote_control.route('/keydown', methods=['POST'])
def handle_keydown():
    """Called from Javascript whenever a key is down (note: can generate repeat calls if held down)"""
    return handle_key_event(request, is_key_down=True)


@remote_control.route('/keyup', methods=['POST'])
def handle_keyup():
    """Called from Javascript whenever a key is released"""
    return handle_key_event(request, is_key_down=False)


@remote_control.route('/setFreeplayEnabled', methods=['POST'])
def handle_setFreeplayEnabled():
    global remote_control_vector
    '''Called from Javascript whenever freeplay mode is toggled on/off'''
    message = json.loads(request.data.decode("utf-8"))
    if remote_control_vector:
        isFreeplayEnabled = message['isFreeplayEnabled']
        if isFreeplayEnabled:
            print('TO DO: free play (enabled)')
            # remote_control_vector.cozmo.start_freeplay_behaviors()
        else:
            print('TO DO: free play (disabled)')
            # remote_control_vector.cozmo.stop_freeplay_behaviors()
    return ""


def activate_controls(_robot):
    global robot
    robot = _robot
    global remote_control_vector
    remote_control_vector = RemoteControlVector(robot)