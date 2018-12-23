"""

Event Monitor for Vector
============================

Created by: GrinningHermit

Inspired by Event Monitor for cozmo-tools:
https://github.com/touretzkyds/cozmo-tools
Cozmo-tools created by: David S. Touretzky, Carnegie Mellon University

=====

"""

import re
import threading
import time
import anki_vector
from anki_vector.events import Events
import functools

robot = None
cube = None
q = None # dependency on queue variable for messaging instead of printing to event-content directly
thread_running = False # starting thread for custom events

facial_expressions = [
    '-unknown-',
    'neutral',
    'happiness',
    'surprise',
    'anger',
    'sadness'
]

# Class for detecting robot states
class CheckState (threading.Thread):
    def __init__(self, thread_id, name, _q):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.q = _q
        self.status = {
            # Default value, type (0: direct output, 1: delayed output, 2: touch), message start, message end, *args for exclusive use (do not trigger when these statuses are true)
            'is_picked_up':             [False, 0, 'Picked up', 'No longer picked up'],
            'is_being_held':            [False, 0, 'Being held', 'No longer being held'],
            'is_cliff_detected':        [False, 0, 'Cliff detected', 'Moved away from cliff', 'is_picked_up', 'is_being_held'],
            'is_on_charger':            [False, 0, 'On charger', 'Moved away from charger'],
            'is_charging':              [False, 0, 'Charging', 'No longer charging'],
            'is_button_pressed':        [False, 0, 'Button pressed', 'Button no longer pressed'],
            'is_carrying_block':        [False, 0, 'Carrying block', 'No longer carrying block'],
            'is_falling':               [False, 0, 'Falling', 'No longer falling'],
            'is_docking_to_marker':     [False, 0, 'Docking to marker', 'Stopped docking to marker'],
            'is_in_calm_power_mode':    [False, 0, 'Calm power mode ON', 'Calm power mode OFF'],
            'is_pathing':               [False, 0, 'Following a path', 'Stopped following a path'],
            'is_being_touched':         [False, 2, 'Touched', 'No longer touched'],
        }

    def run(self):

        def check_status():
            for key, settings in self.status.items():
                delay = 10
                not_allowed = []
                allowed = True

                # direct output
                if settings[1] == 0:
                    if len(settings) > 4:
                        # build a list of not allowed status properties
                        for n_a in range(4, len(settings)):
                            not_allowed.append(settings[n_a])
                        # is a unallowed status property True?
                        for name in not_allowed:
                            if getattr(robot.status, name):
                                allowed = False

                    if getattr(robot.status, key) and allowed:
                        if not settings[0]:
                            settings[0] = True
                            msg = settings[2]
                            self.q.put(msg)
                    elif not getattr(robot.status, key):
                        if settings[0]:
                            settings[0] = False                        
                            msg = settings[3]
                            self.q.put(msg)

                # delayed output
                elif settings[1] == 1:
                    if getattr(robot.status, key):
                        delay = 0
                        if not settings[0]:
                            settings[0] = True
                            msg = settings[2]
                            self.q.put(msg)
                    elif settings[0] and delay > 9:
                        settings[0] = False
                        msg = settings[3]
                        self.q.put(msg)
                    elif delay <= 9:
                        delay += 1
                
                # touch
                elif settings[1] == 2:
                    if getattr(robot.touch.last_sensor_reading, key):
                        if not settings[0]:
                            settings[0] = True
                            msg = settings[2]
                            self.q.put(msg)
                    elif not getattr(robot.touch.last_sensor_reading, key):
                        if settings[0]:
                            settings[0] = False                        
                            msg = settings[3]
                            self.q.put(msg)
                
        while thread_running:
            check_status()
            time.sleep(0.1)


def on_object_appearance(robot, event_type, event):
    print(event.obj)
    msg = event_type.upper()[7:] + ' '
    msg += str(event.obj)
    q.put(msg)

def on_object_actions(robot, event_type, event):
    # print(event)
    msg = event_type.upper()[7:] + ' LightCube ' 
    msg += str(event)
    q.put(msg)

def on_cube_connection(robot, event_type, event):
    # print(event)
    msg = event_type
    q.put(msg)

def on_wake_word(robot, event_type, event):
    # print(event)
    msg = event_type
    q.put(msg)

dispatch_table = {
    on_object_appearance                : [Events.object_appeared, Events.object_disappeared],
    on_object_actions                   : [Events.object_moved, Events.object_stopped_moving, Events.object_tapped, Events.object_up_axis_changed],
    # on_cube_connection                  : [Events.cube_connection_lost],
    # on_wake_word                        : [Events.wake_word]
}

excluded_events = []

def start_stop_event_listening(key, state):
    for func, event_list in dispatch_table.items():
        if key == func:
            for event in event_list:
                func_evt = functools.partial(func, robot)
                if state == 'start':
                    robot.events.subscribe(func_evt, event)
                else:
                    robot.events.unsubscribe(func_evt, event)


class StartCubeConnection (threading.Thread):
    global robot
    global cube
    
    def __init__(self, thread_id, name, _q):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.count = 0
        self.q = _q

    def run(self):
        count = self.count
        robot.world.connect_cube()
        if robot.world.connected_light_cube:
            cube = robot.world.connected_light_cube
            msg = f"{cube.descriptive_name}"
            self.q.put(msg)
            start_stop_event_listening(on_object_actions, 'start')
            # start_stop_event_listening(on_cube_connection, 'start')
        elif count < 4:
            count = count + 1
            print('connecting cube failed, restarting: ' + str(count))
            self.count = count
            self.run()


def monitor(_robot, _q):
    if not isinstance(_robot, anki_vector.robot.Robot):
        raise TypeError('First argument must be a Robot instance')
    global robot
    global cube
    global q
    global thread_running
    robot = _robot
    q = _q
    thread_running = True

    thread_is_state_changed = CheckState(1, 'ThreadCheckState', q)
    thread_is_state_changed.start()
    start_stop_event_listening(on_object_appearance, 'start')
    # start_stop_event_listening(on_wake_word, 'start')
    thread_start_cube_connection = StartCubeConnection(2, 'ThreadCubeConnect', q)
    thread_start_cube_connection.start()


def unmonitor(_robot):
    if not isinstance(_robot, anki_vector.robot.Robot):
        raise TypeError('First argument must be a Robot instance')
    global robot
    global thread_running
    robot = _robot
    thread_running = False

    try:
        start_stop_event_listening(on_object_appearance, 'stop')
        start_stop_event_listening(on_object_actions, 'stop')
    except Exception:
        pass


