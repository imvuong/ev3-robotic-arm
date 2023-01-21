#!/usr/bin/env python3
__author__ = 'Nino Guba'

import os
import sys
import logging

import tty
import sys
import select
import termios

import paho.mqtt.client as paho
import msgpack

import evdev
import threading
import time

from evdev import InputDevice, categorize, ecodes
from ev3dev2.led import Leds
from ev3dev2.sound import Sound
from ev3dev2.motor import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D, SpeedPercent, LargeMotor, MediumMotor, MoveTank

import rpyc

# Create a RPyC connection to the remote ev3dev device.
# Use the hostname or IP address of the ev3dev device.
# If this fails, verify your IP connectivty via ``ping X.X.X.X``
conn = rpyc.classic.connect('192.168.4.90') #change this IP address for your slave EV3 brick
#remote_ev3 = conn.modules['ev3dev.ev3']
remote_motor = conn.modules['ev3dev2.motor']
remote_led = conn.modules['ev3dev2.led']

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(message)s')
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger = logging.getLogger(__name__)

## Some helpers ##
def scale(val, src, dst):
    return (float(val - src[0]) / (src[1] - src[0])) * (dst[1] - dst[0]) + dst[0]

def scale_stick(value):
    return scale(value,(0,255),(-1000,1000))

## Initializing ##
# logger.info("Finding wireless controller...")
# devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
# for device in devices:
#    logger.info("{}".format(device.name))

# ps4gamepad = devices[0].fn # PS4 gamepad
#ps4motion = devices[1].fn # PS4 accelerometer
#ps4touchpad = devices[2].fn # PS4 touchpad

# gamepad = evdev.InputDevice(ps4gamepad)

leds = Leds()
remote_leds = remote_led.Leds()
sound = Sound()

waist_motor = LargeMotor(OUTPUT_A)
shoulder_control1 = LargeMotor(OUTPUT_B)
shoulder_control2 = LargeMotor(OUTPUT_C)
shoulder_motor = MoveTank(OUTPUT_B,OUTPUT_C)
elbow_motor = LargeMotor(OUTPUT_D)
roll_motor = remote_motor.MediumMotor(remote_motor.OUTPUT_A)
pitch_motor = remote_motor.MediumMotor(remote_motor.OUTPUT_B)
spin_motor = remote_motor.MediumMotor(remote_motor.OUTPUT_C)
grabber_motor = remote_motor.MediumMotor(remote_motor.OUTPUT_D)

waist_motor.position = 0
shoulder_control1.position = 0
shoulder_control2.position = 0
shoulder_motor.position = 0
elbow_motor.position = 0
roll_motor.position = 0
pitch_motor.position = 0
spin_motor.position = 0
grabber_motor.position = 0

waist_ratio = 7.5
shoulder_ratio = 7.5
elbow_ratio = 5
roll_ratio = 7
pitch_ratio = 5
spin_ratio = 7
grabber_ratio = 24

waist_max = 360
waist_min = -360
shoulder_max = -60 #-75 max without grabber
shoulder_min = 50 #65 min without grabber
elbow_max = -175
elbow_min = 0
roll_max = 180
roll_min = -180
pitch_max = 80
pitch_min = -90
spin_max = -360
spin_min = 360
grabber_max = -68
grabber_min = 0

full_speed = 100
fast_speed = 75
normal_speed = 50
slow_speed = 25

waist_speed = 0
shoulder_speed = 0
elbow_speed = 0
roll_speed = 0
pitch_speed = 0
spin_speed = 0
grabber_speed = 0

forward_speed = 0
forward_side_speed = 0

upward_speed = 0
upward_side_speed = 0

turning_left = False
turning_right = False

roll_left = False
roll_right = False

pitch_up = False
pitch_down = False

spin_left = False
spin_right = False

grabber_open = False
grabber_close = False

running = True

class MotorThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        logger.info("Engine running!")
        os.system('setfont Lat7-Terminus12x6')
        leds.set_color("LEFT", "BLACK")
        leds.set_color("RIGHT", "BLACK")
        remote_leds.set_color("LEFT", "BLACK")
        remote_leds.set_color("RIGHT", "BLACK")
        sound.play_song((('C4', 'e'), ('D4', 'e'), ('E5', 'q')))
        leds.set_color("LEFT", "GREEN")
        leds.set_color("RIGHT", "GREEN")
        remote_leds.set_color("LEFT", "GREEN")
        remote_leds.set_color("RIGHT", "GREEN")

        """
        #Calibrations
        waist_motor.on_to_position(fast_speed,(waist_max/2)*waist_ratio,True,True) #Right
        waist_motor.on_to_position(fast_speed,(waist_min/2)*waist_ratio,True,True) #Left
        waist_motor.on_to_position(fast_speed,0,True,True)

        shoulder_motor.on_for_degrees(normal_speed,normal_speed,shoulder_max*shoulder_ratio,True,True) #Forward
        shoulder_motor.on_for_degrees(normal_speed,normal_speed,-shoulder_max*shoulder_ratio,True,True) 
        shoulder_motor.on_for_degrees(normal_speed,normal_speed,shoulder_min*shoulder_ratio,True,True) #Backward
        shoulder_motor.on_for_degrees(normal_speed,normal_speed,-shoulder_min*shoulder_ratio,True,True)

        elbow_motor.on_to_position(normal_speed,elbow_max*elbow_ratio,True,True) #Up
        elbow_motor.on_to_position(normal_speed,elbow_min*elbow_ratio,True,True) #Down

        roll_motor.on_to_position(normal_speed,(roll_max/2)*roll_ratio,True,True) #Right
        roll_motor.on_to_position(normal_speed,(roll_min/2)*roll_ratio,True,True) #Left
        roll_motor.on_to_position(normal_speed,0,True,True)

        pitch_motor.on_to_position(normal_speed,pitch_max*pitch_ratio,True,True) #Up
        pitch_motor.on_to_position(normal_speed,pitch_min*pitch_ratio,True,True) #Down
        pitch_motor.on_to_position(normal_speed,0,True,True)

        spin_motor.on_to_position(normal_speed,(spin_max/2)*spin_ratio,True,True) #Right
        spin_motor.on_to_position(normal_speed,(spin_min/2)*spin_ratio,True,True) #Left
        spin_motor.on_to_position(normal_speed,0,True,True)

        grabber_motor.on_to_position(normal_speed,grabber_max*grabber_ratio,True,True) #Close
        grabber_motor.on_to_position(normal_speed,grabber_min*grabber_ratio,True,True) #Open

        #Reach
        elbow_motor.on_to_position(normal_speed,-90*elbow_ratio,True,False) #Up
        shoulder_motor.on_for_degrees(normal_speed,normal_speed,shoulder_max*shoulder_ratio,True,True) #Forward
        waist_motor.on_to_position(fast_speed,waist_max*waist_ratio,True,True) #Right
        elbow_motor.on_to_position(normal_speed,elbow_max*elbow_ratio,True,False) #Up
        shoulder_motor.on_for_degrees(normal_speed,normal_speed,75*shoulder_ratio,True,True) #Reset
        elbow_motor.on_to_position(normal_speed,-90*elbow_ratio,True,False) #Down
        shoulder_motor.on_for_degrees(normal_speed,normal_speed,65*shoulder_ratio,True,True) #Backward
        waist_motor.on_to_position(fast_speed,0,True,True) #Center
        elbow_motor.on_to_position(slow_speed,elbow_min*elbow_ratio,True,True) #Reset
        shoulder_motor.on_for_degrees(slow_speed,slow_speed,-65*shoulder_ratio,True,True) #Reset
        """

        while running:
            if shoulder_speed > 0 and shoulder_control1.position > ((shoulder_max*shoulder_ratio)+100):
                shoulder_motor.on( -shoulder_speed,-shoulder_speed )
            elif shoulder_speed < 0 and shoulder_control1.position < ((shoulder_min*shoulder_ratio)-100):
                shoulder_motor.on( shoulder_speed,shoulder_speed )
            else:
                shoulder_motor.stop()

            if elbow_speed > 0:
                elbow_motor.on_to_position(abs(elbow_speed),elbow_max*elbow_ratio,True,False) #Up
            elif elbow_speed < 0:
                elbow_motor.on_to_position(abs(elbow_speed),elbow_min*elbow_ratio,True,False) #Down
            else:
                elbow_motor.stop()

            if waist_speed < 0:
                waist_motor.on_to_position(abs(waist_speed),waist_min*waist_ratio,True,False) #Left
            elif waist_speed > 0:
                waist_motor.on_to_position(abs(waist_speed),waist_max*waist_ratio,True,False) #Right
            else:
                waist_motor.stop()

            if roll_speed > 0:
                roll_motor.on_to_position(abs(roll_speed),roll_min*roll_ratio,True,False) #Left
            elif roll_speed < 0:
                roll_motor.on_to_position(abs(roll_speed),roll_max*roll_ratio,True,False) #Right
            else:
                roll_motor.stop()

            if pitch_speed > 0:
                pitch_motor.on_to_position(abs(pitch_speed),pitch_max*pitch_ratio,True,False) #Up
            elif pitch_speed < 0:
                pitch_motor.on_to_position(abs(pitch_speed),pitch_min*pitch_ratio,True,False) #Down
            else:
                pitch_motor.stop()

            if spin_speed > 0:
                spin_motor.on_to_position(abs(spin_speed),spin_min*spin_ratio,True,False) #Left
            elif spin_speed < 0:
                spin_motor.on_to_position(abs(spin_speed),spin_max*spin_ratio,True,False) #Right
            else:
                spin_motor.stop()

            if grabber_speed > 0:
                # grabber_motor.on_to_position(normal_speed,grabber_max*grabber_ratio,True,True) #Close
                grabber_motor.on_to_position(abs(grabber_speed),grabber_max*grabber_ratio,True,False) #Close
                # grabber_motor.stop()
            elif grabber_speed < 0:
                # grabber_motor.on_to_position(normal_speed,grabber_min*grabber_ratio,True,True) #Open
                grabber_motor.on_to_position(abs(grabber_speed),grabber_min*grabber_ratio,True,False) #Open
                # grabber_motor.stop()
            else:
                grabber_motor.stop()

        waist_motor.stop()
        shoulder_motor.stop()
        elbow_motor.stop()
        roll_motor.stop()
        pitch_motor.stop()
        spin_motor.stop()
        grabber_motor.stop()

motor_thread = MotorThread()
motor_thread.setDaemon(True)
motor_thread.start()

def reset_motors():
    """ reset motor positions to default """
    # logger.info("Resetting motors...")
    waist_motor.reset()
    shoulder_motor.reset()
    elbow_motor.reset()
    roll_motor.reset()
    pitch_motor.reset()
    spin_motor.reset()
    if grabber_motor:
        grabber_motor.reset()

def convert(data):
    if isinstance(data, bytes):  return data.decode()
    if isinstance(data, dict):   return dict(map(convert, data.items()))
    if isinstance(data, tuple):  return tuple(map(convert, data))
    if isinstance(data, list):   return list(map(convert, data))
    return data

def on_message(mosq, obj, msg):
    unpacked = msgpack.unpackb(msg.payload)
    new_data = convert(unpacked)
    print(new_data['position'][0])

def on_publish(mosq, obj, mid):
    pass

def show_menu():
    print("Instruction")
    print("")
    print("a s d f g h j")
    print("z x c v b n m")

client = paho.Client()
client.on_message = on_message
client.on_publish = on_publish

#client.tls_set('root.ca', certfile='c1.crt', keyfile='c1.key')
# client.connect("127.0.0.1", 1883, 60)
client.connect("192.168.4.76", 1883, 60)

# client.subscribe("kids/yolo", 0)
# client.subscribe("adult/#", 0)
client.subscribe("joint_states", 0)

show_menu()
orig_settings = termios.tcgetattr(sys.stdin)
tty.setcbreak(sys.stdin)
x = 0
reset_motors()
UP = "\x1B[9A"  #printing \x1B[2A (ESC [ 2 A) moves the cursor up 2 times, adjust the number as needed
CLR = "\x1B[0K"
print("\n\n\n\n\n\n\n\n\n")  # set up blank lines so cursor moves work
while x != chr(27): # ESC
    while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        x=sys.stdin.read(1)[0]
        # print("You pressed", x)

        if x == '.':
            break
        elif x == 'a':
            waist_speed += 1
        elif x == 'z':
            waist_speed -= 1
        elif x == 's':
            shoulder_speed += 1
        elif x == 'x':
            shoulder_speed -= 1
        elif x == 'd':
            elbow_speed += 1
        elif x == 'c':
            elbow_speed -= 1
        elif x == 'f':
            roll_speed += 1
        elif x == 'v':
            roll_speed -= 1
        elif x == 'g':
            pitch_speed += 1
        elif x == 'b':
            pitch_speed -= 1
        elif x == 'h':
            spin_speed += 1
        elif x == 'n':
            spin_speed -= 1
        elif x == 'j':
            grabber_speed += 1
        elif x == 'm':
            grabber_speed -= 1        
        elif x == 'r':
            reset_motors()

    # print("{}\t\tSpeed\tRotation{}\n".format(UP, CLR), end="")
    # print("Waist:\t\t{:03d}\t{:03d}{}\n".format(waist_speed, waist_motor.position, CLR), end="")
    # print("Shoulder:\t{:03d}\t{:03d}{}\n".format(shoulder_speed, shoulder_motor.position, CLR), end="")
    # print("Elbow:\t\t{:03d}\t{:03d}{}\n".format(elbow_speed, elbow_motor.position, CLR), end="")
    # print("Roll:\t\t{:03d}\t{:03d}{}\n".format(roll_speed, roll_motor.position, CLR), end="")
    # print("Pitch:\t\t{:03d}\t{:03d}{}\n".format(pitch_speed, pitch_motor.position, CLR), end="")
    # print("Spin:\t\t{:03d}\t{:03d}{}\n".format(spin_speed, spin_motor.position, CLR), end="")
    # print("Grabber:\t{:03d}\t{:03d}{}\n".format(grabber_speed, grabber_motor.position, CLR))

    client.loop()

termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)  



# for event in gamepad.read_loop():   #this loops infinitely
#     if event.type == 3:
#         if event.code == 0: #Left stick X-axis
#             forward_speed = scale_stick(event.value)
#         #if event.code == 1: #Left stick Y-axis
#         #    forward_side_speed = scale_stick(event.value)
#         if event.code == 3: #Right stick X-axis
#             upward_speed = -scale_stick(event.value)
#         #if event.code == 4: #Right stick Y-axis
#         #    upward_side_speed = scale_stick(event.value)
#         if forward_speed < 100 and forward_speed > -100:
#             forward_speed = 0
#         if upward_speed < 100 and upward_speed > -100:
#             upward_speed = 0
#         if forward_side_speed < 100 and forward_side_speed > -100:
#             forward_side_speed = 0
#         if upward_side_speed < 100 and upward_side_speed > -100:
#             upward_side_speed = 0

#     if event.type == 1 and event.code == 310 and event.value == 1:  #L1
#         turning_left = True
#     elif event.type == 1 and event.code == 310 and event.value == 0:
#         turning_left = False

#     if event.type == 1 and event.code == 311 and event.value == 1:  #R1
#         turning_right = True
#     elif event.type == 1 and event.code == 311 and event.value == 0:
#         turning_right = False

#     if event.type == 1 and event.code == 308 and event.value == 1:  #Square
#         roll_left = True
#     elif event.type == 1 and event.code == 308 and event.value == 0:
#         roll_left = False

#     if event.type == 1 and event.code == 305 and event.value == 1:  #Circle
#         roll_right = True
#     elif event.type == 1 and event.code == 305 and event.value == 0:
#         roll_right = False

#     if event.type == 1 and event.code == 307 and event.value == 1:  #Triangle
#         pitch_up = True
#     elif event.type == 1 and event.code == 307 and event.value == 0:
#         pitch_up = False

#     if event.type == 1 and event.code == 304 and event.value == 1:  #X
#         pitch_down = True
#     elif event.type == 1 and event.code == 304 and event.value == 0:
#         pitch_down = False

#     if event.type == 1 and event.code == 312 and event.value == 1:  #L2
#         spin_left = True
#     elif event.type == 1 and event.code == 312 and event.value == 0:
#         spin_left = False

#     if event.type == 1 and event.code == 313 and event.value == 1:  #R2
#         spin_right = True
#     elif event.type == 1 and event.code == 313 and event.value == 0:
#         spin_right = False

#     if event.type == 1 and event.code == 318 and event.value == 1:  #R3
#         if grabber_open:
#             grabber_open = False
#             grabber_close = True
#         else:
#             grabber_open = True
#             grabber_close = False

#     # if event.type == 1 and event.code == 314 and event.value == 1:  #Share
#     #     #Demo

#     if event.type == 1 and event.code == 315 and event.value == 1:  #Options
#         #Reset
#         roll_motor.on_to_position(normal_speed,0,True,False)
#         pitch_motor.on_to_position(normal_speed,0,True,False)
#         spin_motor.on_to_position(normal_speed,0,True,False)
#         grabber_motor.on_to_position(normal_speed,0,True,True)
#         elbow_motor.on_to_position(slow_speed,0,True,False)
#         shoulder_control1.on_to_position(slow_speed,0,True,False)
#         shoulder_control2.on_to_position(slow_speed,0,True,False)
#         waist_motor.on_to_position(fast_speed,0,True,True)

#     if event.type == 1 and event.code == 316 and event.value == 1:  #PS
#         logger.info("Engine stopping!")
#         running = False

#         #Reset
#         roll_motor.on_to_position(normal_speed,0,True,False)
#         pitch_motor.on_to_position(normal_speed,0,True,False)
#         spin_motor.on_to_position(normal_speed,0,True,False)
#         grabber_motor.on_to_position(normal_speed,0,True,True)
#         elbow_motor.on_to_position(slow_speed,0,True,False)
#         shoulder_control1.on_to_position(slow_speed,0,True,False)
#         shoulder_control2.on_to_position(slow_speed,0,True,False)
#         waist_motor.on_to_position(fast_speed,0,True,True)

#         sound.play_song((('E5', 'e'), ('C4', 'e')))
#         leds.set_color("LEFT", "BLACK")
#         leds.set_color("RIGHT", "BLACK")
#         remote_leds.set_color("LEFT", "BLACK")
#         remote_leds.set_color("RIGHT", "BLACK")

#         time.sleep(1) # Wait for the motor thread to finish
#         break 
