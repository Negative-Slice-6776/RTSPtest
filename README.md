# RTSPtest
Testing network and device latency for an IP camera with RTSP stream

1 - install python

2 - install following dependencies: numpy, cv2, PIL, ntplib

pip install opencv-python numpy pillow ntplib

3 - open the script and enter your RTSP url on line 16 between the brackets

4 - place an atomic stopwatch app (atomic clock for example) in front of your camera, start the script, press enter and you will get a screenshot and preview



This was written to be executed on macOS, I made some quick fixes to make it run on Windows and Linux as well, but haven’t tested it, so let me know if you have issues
