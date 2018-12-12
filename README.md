# Vector-Explorer-Tool
Interface exposing functionality of the robot Cozmo from Anki
---
This tool gives control over Vector. You can look through his camera while using keyboard buttons to control him. It also lists and plays all built-in animations.

This is a conversion of the Cozmo Explorer Tool for the newer Anki robot Vector. In its current state it is still very basic and not all functionalities from the Cozmo variant are copied (event monitor, triggers and behaviors are not included). This version is aimed at the alpha release of the Vector SDK and it may change completely over time.

![Cozmo-Explorer-Tool](static/img/vector-explorer-tool-v0.1.jpg)

What does it do exactly?
-
Running the script 'explorer_tool.py' in python will open a web page. It is divided in 3 sections:

1. ROBOT CAMERA AND CONTROL: A constant camera feed is visible. While mousing over this area, controls for Vector are also visible, indicating how to control Vector with the keyboard. It's also possible to make the feed full screen. 

2. ANIMATIONS: A user can click the play button of a listed animation and Vector will execute it. It is also possible to search for a particular animation and buttons are provided to group animations based on their naming convention. 

What do you need to use it?
-
1. Vector himself (http://anki.com/vector)
2. A computer
3. A little knowledge about Python
4. Knowledge of the Vector SDK (https://developer.anki.com/vector/docs)
5. The files in this repository
6. The python module Pillow. (pip3 install --user Pillow, usually already installed when working with the Cozmo SDK)
7. The python module Flask. (pip3 install --user flask)


If you know how to run an example file from the Vector SDK, you should be able to run this script. 

System requirements
-
- Computer with Windows OS, mac OSX or Linux
- Python 3.6.1 or later
- WiFi connection

Installation notes
-
- Running 'vector-explorer-tool.py' will attempt to open a browser window at 127.0.0.1:5000. This is similar to  'remote_control.py' from the Vector SDK examples.

Known issues
-
- Event monitor, triggers and behaviors (features of the Cozmo explorer tool) are disabled due to needed research time and SDK differences compared to the Cozmo SDK.
- IR light is something Vector does not have and needs to be removed in a future release. 
- Free play button needs to be fixed.
- The python module flask-socket-io currently has no function without the event monitor
