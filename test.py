#!/usr/bin/env python3

import os
import sys
import logging

from ev3dev2.motor import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D, LargeMotor, MoveTank

import rpyc

# Create a RPyC connection to the remote ev3dev device.
# Use the hostname or IP address of the ev3dev device.
# If this fails, verify your IP connectivty via ``ping X.X.X.X``
conn = rpyc.classic.connect('192.168.4.90') #change this IP address for your slave EV3 brick
#remote_ev3 = conn.modules['ev3dev.ev3']
remote_motor = conn.modules['ev3dev2.motor']
remote_led = conn.modules['ev3dev2.led']

# logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s.%(msecs)03d: %(message)s', datefmt='%Y%m%d%H%M%S')
# logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logFormatter = logging.Formatter("%(asctime)s.%(msecs)03d [%(threadName)-12.12s] [%(levelname)-5.5s]:  %(message)s", datefmt='%Y%m%d%H%M%S')
logger = logging.getLogger(__name__)
# logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

logPath = "."
logFilename = "output"
fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, logFilename))
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

waist_motor = LargeMotor(OUTPUT_A)
shoulder_control1 = LargeMotor(OUTPUT_B)
shoulder_control2 = LargeMotor(OUTPUT_C)
shoulder_motor = MoveTank(OUTPUT_B,OUTPUT_C)
elbow_motor = LargeMotor(OUTPUT_D)
roll_motor = remote_motor.MediumMotor(remote_motor.OUTPUT_A)
pitch_motor = remote_motor.MediumMotor(remote_motor.OUTPUT_B)
spin_motor = remote_motor.MediumMotor(remote_motor.OUTPUT_C)
grabber_motor = remote_motor.MediumMotor(remote_motor.OUTPUT_D)

logger.info("Engine running!")
os.system('setfont Lat7-Terminus12x6')

speed = 50
waist_max = 180
waist_min = -180
waist_ratio = 7.5
shoulder_max = 50
shoulder_min = -60
shoulder_ratio = 7.5
elbow_max = 90
elbow_min = -90
elbow_ratio = 5

# waist_motor.position = 0
# logger.info("Waist Position: {}".format(waist_motor.position))
# waist_motor.on_to_position(speed,-180*waist_ratio,True,True)
# logger.info("Waist Position: {}".format(waist_motor.position))

# shoulder_motor.position = 0
# logger.info("Shoulder Position: {}".format(shoulder_motor.position))
# shoulder_motor.on_for_degrees(speed,speed,30*shoulder_ratio,True,True)
# logger.info("Shoulder Position: {}".format(shoulder_motor.position))

# elbow_motor.position = 0
# logger.info("Shoulder Position: {}".format(elbow_motor.position))
# elbow_motor.on_to_position(speed,-90*elbow_ratio,True,True)
# logger.info("Shoulder Position: {}".format(elbow_motor.position))