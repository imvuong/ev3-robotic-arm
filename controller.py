#!/usr/bin/env python3

import logging
import math
import msgpack
import os
import paho.mqtt.client as paho
import rpyc
import threading
from ev3dev2.motor import LargeMotor, MoveTank
from ev3dev2.motor import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sound import Sound

# Setup logging
logFormatter = logging.Formatter(
    "%(asctime)s.%(msecs)03d [%(threadName)-12.12s] \
    [%(levelname)-5.5s]:  %(message)s", datefmt='%Y%m%d%H%M%S')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logPath = "."
logFilename = "output"
# FileHandler
fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, logFilename))
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)
# ConsoleHandler
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

os.system('setfont Lat7-Terminus12x6')

running = True

robot_pose = []
WAIST = 0
SHOULDER = 1
ELBOW = 2
ROLL = 3
PITCH = 4
SPIN = 5


class MotorThread(threading.Thread):

    WAIST_RATIO = 7.5
    SHOULDER_RATIO = 7.5
    ELBOW_RATIO = 5
    ROLL_RATIO = 7
    PITCH_RATIO = 5
    SPIN_RATIO = 7
    GRABBER_RATIO = 24

    WAIST_MAX = 360
    WAIST_MIN = -360
    SHOULDER_MAX = -60      # -75 max without grabber
    SHOULDER_MIN = 50  # 65 min without grabber
    ELBOW_MAX = -175
    ELBOW_MIN = 0
    ROLL_MAX = 180
    ROLL_MIN = -180
    PITCH_MAX = 80
    PITCH_MIN = -90
    SPIN_MAX = -360
    SPIN_MIN = 360
    GRABBER_MAX = -68
    GRABBER_MIN = 0

    def __init__(self):
        threading.Thread.__init__(self)
        # Create a RPyC connection to the remote ev3dev device.
        # Use the hostname or IP address of the ev3dev device.
        # If this fails, verify your IP connectivty via ``ping X.X.X.X``
        # change this IP address for your slave EV3 brick
        conn = rpyc.classic.connect('192.168.4.90')
        remote_motor = conn.modules['ev3dev2.motor']
        self.sound = Sound()
        self.waist_motor = LargeMotor(OUTPUT_A)
        self.shoulder_control1 = LargeMotor(OUTPUT_B)
        self.shoulder_control2 = LargeMotor(OUTPUT_C)
        self.shoulder_motor = MoveTank(OUTPUT_B, OUTPUT_C)
        self.elbow_motor = LargeMotor(OUTPUT_D)
        self.roll_motor = remote_motor.MediumMotor(remote_motor.OUTPUT_A)
        self.pitch_motor = remote_motor.MediumMotor(remote_motor.OUTPUT_B)
        self.spin_motor = remote_motor.MediumMotor(remote_motor.OUTPUT_C)
        self.grabber_motor = remote_motor.MediumMotor(remote_motor.OUTPUT_D)

    def run(self):
        logger.info("Running!")
        self.sound.play_song((('C4', 'e'), ('D4', 'e'), ('E5', 'q')))
        self.reset()
        waist_speed = 20
        shoulder_speed = 20
        elbow_speed = 20

        while running:
            waist_pos = robot_pose[WAIST] * 180 / math.pi
            shoulder_pos = robot_pose[SHOULDER] * 180 / math.pi
            elbow_pos = robot_pose[ELBOW] * 180 / math.pi
            roll_pos = robot_pose[ROLL] * 180 / math.pi
            pitch_pos = robot_pose[PITCH] * 180 / math.pi
            spin_pos = robot_pose[SPIN] * 180 / math.pi

            # if shoulder_speed > 0 and self.shoulder_control1.position > ((shoulder_max*shoulder_ratio)+100):
            #     self.shoulder_motor.on(-shoulder_speed, -shoulder_speed)
            # elif shoulder_speed < 0 and self.shoulder_control1.position < ((shoulder_min*shoulder_ratio)-100):
            #     self.shoulder_motor.on(shoulder_speed, shoulder_speed)
            # else:
            #     self.shoulder_motor.stop()

            # if elbow_speed > 0:
            #     self.elbow_motor.on_to_position(
            #         abs(elbow_speed), elbow_max*elbow_ratio, True, False)  # Up
            # elif elbow_speed < 0:
            #     elbow_motor.on_to_position(
            #         abs(elbow_speed), elbow_min*elbow_ratio, True, False)  # Down
            # else:
            #     elbow_motor.stop()

            if waist_pos > self.WAIST_MIN and waist_pos < self.WAIST_MAX:
                self.waist_motor.on_to_position(waist_speed, waist_pos * self.WAIST_RATIO, True, False)


            # if roll_speed > 0:
            #     roll_motor.on_to_position(
            #         abs(roll_speed), roll_min*roll_ratio, True, False)  # Left
            # elif roll_speed < 0:
            #     roll_motor.on_to_position(
            #         abs(roll_speed), roll_max*roll_ratio, True, False)  # Right
            # else:
            #     roll_motor.stop()

            # if pitch_speed > 0:
            #     pitch_motor.on_to_position(
            #         abs(pitch_speed), pitch_max*pitch_ratio, True, False)  # Up
            # elif pitch_speed < 0:
            #     pitch_motor.on_to_position(
            #         abs(pitch_speed), pitch_min*pitch_ratio, True, False)  # Down
            # else:
            #     pitch_motor.stop()

            # if spin_speed > 0:
            #     spin_motor.on_to_position(
            #         abs(spin_speed), spin_min*spin_ratio, True, False)  # Left
            # elif spin_speed < 0:
            #     spin_motor.on_to_position(
            #         abs(spin_speed), spin_max*spin_ratio, True, False)  # Right
            # else:
            #     spin_motor.stop()

            # if grabber_speed > 0:
            #     # grabber_motor.on_to_position(normal_speed,grabber_max*grabber_ratio,True,True) #Close
            #     grabber_motor.on_to_position(
            #         abs(grabber_speed), grabber_max*grabber_ratio, True, False)  # Close
            #     # grabber_motor.stop()
            # elif grabber_speed < 0:
            #     # grabber_motor.on_to_position(normal_speed,grabber_min*grabber_ratio,True,True) #Open
            #     grabber_motor.on_to_position(
            #         abs(grabber_speed), grabber_min*grabber_ratio, True, False)  # Open
            #     # grabber_motor.stop()
            # else:
            #     grabber_motor.stop()

        logger.info("Stopping")
        self.stop()

    def reset(self):
        self.waist_motor.position = 0
        self.shoulder_control1.position = 0
        self.shoulder_control2.position = 0
        self.shoulder_motor.position = 0
        self.elbow_motor.position = 0
        self.roll_motor.position = 0
        self.pitch_motor.position = 0
        self.spin_motor.position = 0
        self.grabber_motor.position = 0

    def stop(self):
        self.waist_motor.stop()
        self.shoulder_motor.stop()
        self.elbow_motor.stop()
        self.roll_motor.stop()
        self.pitch_motor.stop()
        self.spin_motor.stop()
        self.grabber_motor.stop()


class MqttClient():

    def __init__(self):
        self.client = paho.Client()
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish

        logger.info("mqtt client init!")
        self.client.connect("192.168.4.76", 1883, 60)
        self.client.subscribe("joint_states", 0)

    def convert(self, data):
        if isinstance(data, bytes):
            return data.decode()
        if isinstance(data, dict):
            return dict(map(self.convert, data.items()))
        if isinstance(data, tuple):
            return tuple(map(self.convert, data))
        if isinstance(data, list):
            return list(map(self.convert, data))
        return data

    def on_message(self, mosq, obj, msg):
        unpacked = msgpack.unpackb(msg.payload)
        new_data = self.convert(unpacked)
        # logger.info(new_data['position'][0])
        robot_pose = new_data['position']

    def on_publish(self, mosq, obj, mid):
        pass

    def loop(self):
        self.client.loop()


mqtt_client = MqttClient()
motor_thread = MotorThread()
motor_thread.setDaemon(True)
motor_thread.start()

while True:
    mqtt_client.loop()
