var haveEvents = "ongamepadconnected" in window;
var controllers = {};
var buttons = [];

var mappingReference = [
  //  [keyCode, active true/false] - controller btn name - mapping
  [0, 0], // A
  [0, 0], // B
  [0, 0], // X
  [0, 0], // Y
  [16, 0], // Left button         => ALT (move slower)
  [16, 0], // Right button        => ALT (move slower)
  [18, 0], // Left trigger        => SHIFT (move faster)
  [18, 0], // Right trigger       => SHIFT (move faster)
  [80, 0], // Back/select         => start/stop freeplay
  [80, 0], // Start/forward       => start/stop freeplay
  [0, 0], // Left stick pressed
  [0, 0], // right stick pressed
  [0, 0], // Left cluster top
  [0, 0], // Left cluster bottom
  [0, 0], // Left cluster left
  [0, 0], // Left cluster right
  [0, 0] // Center
];

var stickReference = [
  [65, 0], // A left
  [68, 0], // D right
  [87, 0], // W forward
  [83, 0], // S back
  [82, 0], // R arm up
  [70, 0], // F arm down
  [81, 0], // Q head up
  [69, 0]  // E head down
];

function connecthandler(e) {
  addgamepad(e.gamepad);
}

function addgamepad(gamepad) {
  controllers[gamepad.i] = gamepad;

  for (var i = 0; i < gamepad.buttons.length; i++) {
    buttons.push(0);
  }

  requestAnimationFrame(updateStatus);
}

function disconnecthandler(e) {
  removegamepad(e.gamepad);
}

function removegamepad(gamepad) {
  delete controllers[gamepad.i];
}

function updateStatus() {
  if (!haveEvents) {
    scangamepads();
  }

  var i = 0;
  var j;
  var hasShift = 0;
  var hasAlt = 0;
  var hasCtrl = 0;

  for (j in controllers) {
    var controller = controllers[j];

    for (i = 0; i < controller.buttons.length; i++) {
      var val = controller.buttons[i];
      var pressed = val == 1.0;
      pressed = val.pressed;
      val = val.value;
      keyCode = mappingReference[i][0];

      if (pressed) {
        if (keyCode == 16) {
          hasAlt = 1;
        }
        if (keyCode == 18) {
          hasShift = 1;
        }
        if (keyCode != 16 && keyCode != 18) {
          // only process if not a combo button
          console.log(keyCode + " " + hasAlt + " " + hasShift);
          postHttpRequest("keydown", { keyCode, hasShift, hasCtrl, hasAlt });
        }
      }
    }

    for (i = 0; i < controller.axes.length; i++) {
      if (controller.axes[i] != 0) {
        keyCode = stickReferenceEvaluator(i, controller.axes[i]);
        // console.log('axis ' + i + ': ' + controller.axes[i]);
        // console.log(keyCode + " " + hasAlt + " " + hasShift);
        postHttpRequest("keydown", { keyCode, hasShift, hasCtrl, hasAlt });
      } else if (controller.axes[i] == 0) {
        var k = (i + 1) * 2;
        for (j = k - 2; j < k; j++) {
          if (stickReference[j][1] == 1) {
            keyCode = stickReference[j][0];
            stickReference[j][1] = 0;
            // console.log("keyup " + keyCode);
            postHttpRequest("keyup", { keyCode, hasShift, hasCtrl, hasAlt });
          }
        }
      }
    }
  }

  requestAnimationFrame(updateStatus);
}

function scangamepads() {
  var gamepads = navigator.getGamepads
    ? navigator.getGamepads()
    : navigator.webkitGetGamepads
    ? navigator.webkitGetGamepads()
    : [];
  for (var i = 0; i < gamepads.length; i++) {
    if (gamepads[i]) {
      if (gamepads[i].i in controllers) {
        controllers[gamepads[i].i] = gamepads[i];
      } else {
        addgamepad(gamepads[i]);
      }
    }
  }
}

function buttonReference(num) {
  keyCode = mappingReference[num][0];

  return keyCode;
}

function buttonSetActive(num) {
  mappingReference[num][1] = 1;
}

function buttonSetInactive(num) {
  mappingReference[num][1] = 0;
}

function stickReferenceEvaluator(num, axisValue) {
  // num              axisValue              mapping
  // 0   Left stick   left -1 > right 1   => Turn left/right
  // 1   Left stick   top -1 > bottom 1   => Move forward/backward
  // 2   Right stick  left -1 > right 1   => Fork up/down
  // 3   Right stick  top -1 > bottom 1   => Head up/down

  var keyCode = 0;
  var i;

  if (axisValue < 0 && num == 0) {
    i = 0;
  }
  if (axisValue > 0 && num == 0) {
    i = 1;
  }
  if (axisValue < 0 && num == 1) {
    i = 2;
  }
  if (axisValue > 0 && num == 1) {
    i = 3;
  }
  if (axisValue < 0 && num == 2) {
    i = 4;
  }
  if (axisValue > 0 && num == 2) {
    i = 5;
  }
  if (axisValue < 0 && num == 3) {
    i = 6;
  }
  if (axisValue > 0 && num == 3) {
    i = 7;
  }

  keyCode = stickReference[i][0];
  stickReference[i][1] = 1;

  return keyCode;
}

window.addEventListener("gamepadconnected", connecthandler);
window.addEventListener("gamepaddisconnected", disconnecthandler);

if (!haveEvents) {
  setInterval(scangamepads, 60);
}
