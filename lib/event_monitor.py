"""

Event Monitor for Cozmo
============================

Based on Event Monitor for cozmo-tools:
https://github.com/touretzkyds/cozmo-tools

Created by: David S. Touretzky, Carnegie Mellon University

Edited by: GrinningHermit
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

class CheckState (threading.Thread):
    def __init__(self, thread_id, name, _q):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.q = _q
        self.status = {
            # Default value, type (0: direct output, 1: delayed output, 2: touch, 3: light cube), message start, message end, *args for exclusive use (do not trigger when these statuses are true)
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
            # 'is_moving':                [False, 3, 'Light Cube is moving', 'Light Cube stopped moving'],
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
                
                # light cube
                elif settings[1] == 3 and robot.world.connected_light_cube.is_connected:
                    if getattr(robot.world.connected_light_cube, key):
                        if not settings[0]:
                            settings[0] = True
                            msg = settings[2]
                            self.q.put(msg)
                    elif not getattr(robot.world.connected_light_cube, key):
                        if settings[0]:
                            settings[0] = False                        
                            msg = settings[3]
                            self.q.put(msg)



        while thread_running:
            check_status()
            time.sleep(0.1)

def print_prefix(evt):
    msg = evt + ' '
    return msg


"""
def monitor_generic(evt, **kwargs):
    msg = print_prefix(evt)
    if 'behavior_type_name' in kwargs:
        msg += kwargs['behavior_type_name'] + ' '
    if 'obj' in kwargs:
        msg += print_object(kwargs['obj']) + ' '
    if 'action' in kwargs:
        action = kwargs['action']
        if isinstance(action, cozmo.anim.Animation):
            msg += action.anim_name + ' '
        elif isinstance(action, cozmo.anim.AnimationTrigger):
            msg += action.trigger.name + ' '
    msg += str(set(kwargs.keys()))
    q.put(msg)

def monitor_EvtActionCompleted(evt, action, state, failure_code, failure_reason, **kwargs):
    msg = print_prefix(evt)
    msg += print_object(action) + ' '
    if isinstance(action, cozmo.anim.Animation):
        msg += action.anim_name
    elif isinstance(action, cozmo.anim.AnimationTrigger):
        msg += action.trigger.name
    if failure_code is not None:
        msg += str(failure_code) + failure_reason
    q.put(msg)

def monitor_EvtObjectTapped(evt, *, obj, tap_count, tap_duration, tap_intensity, **kwargs):
    msg = print_prefix(evt)
    msg += print_object(obj)
    msg += ' count=' + str(tap_count) + ' duration=' + str(tap_duration) + ' intensity=' + str(tap_intensity)
    q.put(msg)

def monitor_face(evt, face, **kwargs):
    msg = print_prefix(evt)
    name = face.name if face.name is not '' else '[unknown face]'
    msg += name + ' face_id=' + str(face.face_id)
    q.put(msg)

dispatch_table = {
  cozmo.action.EvtActionStarted        : monitor_generic,
  cozmo.action.EvtActionCompleted      : monitor_EvtActionCompleted,
  cozmo.behavior.EvtBehaviorStarted    : monitor_generic,
  cozmo.behavior.EvtBehaviorStopped    : monitor_generic,
  cozmo.anim.EvtAnimationsLoaded       : monitor_generic,
  cozmo.anim.EvtAnimationCompleted     : monitor_EvtActionCompleted,
  # cozmo.objects.EvtObjectAvailable     : monitor_generic, # deprecated
  cozmo.objects.EvtObjectAppeared      : monitor_generic,
  cozmo.objects.EvtObjectDisappeared   : monitor_generic,
  cozmo.objects.EvtObjectObserved      : monitor_generic,
  cozmo.objects.EvtObjectTapped        : monitor_EvtObjectTapped,
  cozmo.faces.EvtFaceAppeared          : monitor_face,
  cozmo.faces.EvtFaceObserved          : monitor_face,
  cozmo.faces.EvtFaceDisappeared       : monitor_face,
}

excluded_events = {    # Occur too frequently to monitor by default
    cozmo.objects.EvtObjectObserved,
    cozmo.faces.EvtFaceObserved,
}
"""

def on_object_appearance(robot, event_type, event):
    print(event.obj)
    name = type(event.obj).__name__
    msg = ''
    if event_type == 'object_appeared':
        msg += 'APPEARED '
    elif event_type == 'object_disappeared':
        msg += 'DISAPPEARED '

    msg += print_prefix(name)

    if name == 'Face':
        msg += 'face_id: ' + str(event.obj.face_id)
        if not event.obj.name == '':
            msg += 'name: ' + event.obj.name
        else:
            msg += 'name: [unknown]'

    if name == 'LightCube':
        msg += 'object_id: ' + str(event.obj.object_id)

    if name == 'Charger':
        msg += 'object_id: ' + str(event.obj.object_id)

    q.put(msg)

def on_object_actions(robot, event_type, event):
    # name = type(event.obj).__name__
    msg = ''
    if event_type == 'object_moved':
        msg += 'MOVE STARTED '
    elif event_type == 'object_finished_move':
        msg += 'MOVE STOPPED '
        msg += cube.descriptive_name + ' '
        msg += 'object_id: ' + str(event.obj.object_id)
    elif event_type == 'object_tapped':
        msg += 'TAPPED '
    elif event_type == 'object_up_axis_changed':
        msg += 'TURNED '

    if event_type != 'object_finished_move':
        msg += cube.descriptive_name + ' '
        msg += 'object_id: ' + str(event.object_id)

    q.put(msg)


dispatch_table = {
    Events.object_appeared              : on_object_appearance,
    Events.object_disappeared           : on_object_appearance,
    Events.object_moved                 : on_object_actions,
    Events.object_finished_move         : on_object_actions,
    Events.object_tapped                : on_object_actions,
    Events.object_up_axis_changed       : on_object_actions,
    # Events.cube_connection_lost         : on_cube_connection,
    # Events.wake_word                    : on_wake_word
}

excluded_events = []

def start_event_listening():
    for k,v in dispatch_table.items():
        if k not in excluded_events:
            print(k)
            func = functools.partial(v, robot)
            robot.events.subscribe(func, k)

def monitor(_robot, _q, evt_class=None):
    if not isinstance(_robot, anki_vector.robot.Robot):
        raise TypeError('First argument must be a Robot instance')
    if evt_class is not None and not issubclass(evt_class, anki_vector.events.EventHandler):
        raise TypeError('Second argument must be an Event subclass')
    global robot
    global cube
    global q
    global thread_running
    robot = _robot
    q = _q
    thread_running = True

    robot.world.connect_cube()
    if robot.world.connected_light_cube:
        cube = robot.world.connected_light_cube
        msg = f"{cube.descriptive_name}"
        q.put(msg)
        start_event_listening()
    else:
        excluding = [Events.object_moved, Events.object_finished_move, Events.object_tapped, Events.object_up_axis_changed]
        for event in excluding:
            excluded_events.append(event)
        start_event_listening()

    # if evt_class in dispatch_table:
    #     robot.world.add_event_handler(evt_class,dispatch_table[evt_class])
    # elif evt_class is not None:
    #     robot.world.add_event_handler(evt_class,monitor_generic)
    # else:
    #     for k,v in dispatch_table.items():
    #         if k not in excluded_events:
    #             robot.world.add_event_handler(k,v)

    thread_is_state_changed = CheckState(1, 'ThreadCheckState', q)
    thread_is_state_changed.start()


def unmonitor(_robot, evt_class=None):
    if not isinstance(_robot, anki_vector.robot.Robot):
        raise TypeError('First argument must be a Robot instance')
    if evt_class is not None and not issubclass(evt_class, anki_vector.events.EventHandler):
        raise TypeError('Second argument must be an Event subclass')
    global robot
    global thread_running
    robot = _robot
    thread_running = False

    # try:
    #     if evt_class in dispatch_table:
    #         robot.world.remove_event_handler(evt_class,dispatch_table[evt_class])
    #     elif evt_class is not None:
    #         robot.world.remove_event_handler(evt_class,monitor_generic)
    #     else:
    #         for k,v in dispatch_table.items():
    #             robot.world.remove_event_handler(k,v)
    # except Exception:
    #     pass

