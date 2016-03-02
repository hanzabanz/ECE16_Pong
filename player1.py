import serial
import time
import matplotlib.pyplot as plt
import math
import socket

__author__ = 'hannah'
"""
Simple implementation of EMG control.
"""


def shift(seq, num):
    return seq[num:] + [0 for i in range(num)]

# Defining constants
EMG0_LOC = 1
EMG1_LOC = 2
TIME_LOC = 0

TIME_LIMIT = 500
BUFFER_SIZE = 21
AVG_SIZE = 21 # only odd numbers work well

DISPLAY_SIZE = 400
DISPLAY_OFFSET = DISPLAY_SIZE/20

SHAPE_TYPE = 0

# Individual calibration values to be changed every time
HIGH = 350
BASE = 300

UPPER_BOUND = 1
LOWER_BOUND = 0

# UDP settings
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# create queue
ser = serial.Serial('COM7', 115200)

# set to 0 as the baseline (baseline should be normalized in arduino)
raw_emg0_list = [0.0 for i in range(DISPLAY_SIZE)]

emg0_buffer = [0.0 for i in range(AVG_SIZE)]
emg1_buffer = [0.0 for i in range(AVG_SIZE)]

raw_emg0_list = [0.0 for i in range(DISPLAY_SIZE)]
raw_emg1_list = [0.0 for i in range(DISPLAY_SIZE)]

emg0_list = [0.0 for i in range(DISPLAY_SIZE)]
emg1_list = [0.0 for i in range(DISPLAY_SIZE)]
time_list = [0.0 for i in range(DISPLAY_SIZE)]

hpf_emg0_list = [0.0 for i in range(DISPLAY_SIZE)]
hpf_emg1_list = [0.0 for i in range(DISPLAY_SIZE)]

env_emg0_list = [0.0 for i in range(DISPLAY_SIZE)]
env_buf_emg0_list = [0.0 for i in range(AVG_SIZE)]

env_emg1_list = [0.0 for i in range(DISPLAY_SIZE)]
env_buf_emg1_list = [0.0 for i in range(AVG_SIZE)]

emg_counter = 0
buffer_counter = 0
initial = False
secondary = False
hpf_sign = True
list_counter = 0
display_counter = 0
update = 0

init_time = 0

plot_num = 0.0
plot_on = False

# internal tracking of paddle position
y_pos = 0

time.sleep(1)

beg = time.time()
end = time.time() + TIME_LIMIT # end is equal to time in x seconds, x being the int at the end
last_time = 0.0

if plot_on:
    plt.figure()
    plt.ion()
    plt.show()
    lineHandle = plt.plot(time_list, env_emg0_list)

while time.time() < end:
    ser.readline() # downsampling by 2
    data = ser.readline()
    data_split = data.split(' ')
    if len(data_split) != 3:
        continue

    try:
        emg0_buffer[buffer_counter] = int(data_split[EMG0_LOC])
        emg1_buffer[buffer_counter] = int(data_split[EMG1_LOC])
        raw_emg0_list[emg_counter] = int(data_split[EMG0_LOC])
        raw_emg1_list[emg_counter] = int(data_split[EMG1_LOC])

        time_signal = int(data_split[TIME_LOC])
        time_list[emg_counter] = time_signal/1000000.0
        if time_list[emg_counter] < last_time:
            continue
        last_time = time_list[emg_counter]
    except ValueError:
        print "error"
        continue
    if not initial:
        emg0_list[emg_counter] = data_split[EMG0_LOC]
        emg1_list[emg_counter] = data_split[EMG1_LOC]
        # if hpf_sign == False:
        #     hpf_emg0_list[emg_counter] = -int(data_split[EMG0_LOC])
        #     hpf_emg1_list[emg_counter] = -int(data_split[EMG1_LOC])
        #     hpf_sign = True
        # else:
        #     hpf_emg0_list[emg_counter] = int(data_split[EMG0_LOC])
        #     hpf_emg1_list[emg_counter] = int(data_split[EMG1_LOC])
        #     hpf_sign = False

        env_buf_emg0_list[buffer_counter] = int(emg0_list[emg_counter])*int(emg0_list[emg_counter])
        env_emg0_list[emg_counter] = env_buf_emg0_list[emg_counter]
        env_buf_emg1_list[buffer_counter] = int(emg1_list[emg_counter])*int(emg1_list[emg_counter])
        env_emg1_list[emg_counter] = env_buf_emg1_list[emg_counter]

    else:
        emg0_list[emg_counter] = sum(emg0_buffer)/AVG_SIZE
        emg1_list[emg_counter] = sum(emg1_buffer)/AVG_SIZE
        # if hpf_sign == False:
        #     hpf_emg0_list[emg_counter] = -sum(emg0_buffer)/AVG_SIZE
        #     hpf_emg1_list[emg_counter] = -sum(emg1_buffer)/AVG_SIZE
        #     hpf_sign = True
        # else:
        #     hpf_emg0_list[emg_counter] = sum(emg0_buffer)/AVG_SIZE
        #     hpf_emg1_list[emg_counter] = sum(emg1_buffer)/AVG_SIZE
        #     hpf_sign = False

        env_buf_emg0_list[buffer_counter] = int(emg0_list[emg_counter])*int(emg0_list[emg_counter])
        env_buf_emg1_list[buffer_counter] = int(emg1_list[emg_counter])*int(emg1_list[emg_counter])
        if not secondary:
            env_emg0_list[emg_counter] = env_buf_emg0_list[buffer_counter]
            env_emg1_list[emg_counter] = env_buf_emg1_list[buffer_counter]
        else:
            env_emg0_list[emg_counter] = sum(env_buf_emg0_list)/AVG_SIZE
            env_emg1_list[emg_counter] = sum(env_buf_emg1_list)/AVG_SIZE

    env_emg0_list[emg_counter] = math.sqrt(int(env_emg0_list[emg_counter]))
    env_emg1_list[emg_counter] = math.sqrt(int(env_emg1_list[emg_counter]))


    temp0 = 0.0
    temp1 = 0.0
    value0 = env_emg0_list[emg_counter]
    value1 = env_emg1_list[emg_counter]

    # print "%f\t%f" %(value0, value1)

    # read new values, but not every round
    if update == 5:
        # Set internal velocity values
        if value0 > 310:
            # temp0 = 10 - int((324-value0)/1.5)
            temp0 = 0.07
        if value1 > 310:
            # temp1 = -(10 - int((319-value1)/1.5))
            temp1 = -0.07

        # Convert velocity values to y axis position
        if temp0 > 0:
            y_pos += temp0
        if temp1 < 0:
            y_pos += temp1

        if y_pos > UPPER_BOUND:
            y_pos = UPPER_BOUND
        if y_pos < LOWER_BOUND:
            y_pos = LOWER_BOUND

        update = 0
    update += 1

    # print "%f\t%f\t%s" %(temp0, temp1, y_pos)s
    print y_pos
    sock.sendto(str(float(y_pos)), (UDP_IP,UDP_PORT))

    buffer_counter += 1
    emg_counter += 1
    if buffer_counter == AVG_SIZE:
        if initial:
            secondary = True
        initial = True
        buffer_counter = 0

    if plot_on:
        display_counter += 1
        if display_counter == DISPLAY_OFFSET:
            lineHandle[0].set_xdata(time_list)
            lineHandle[0].set_ydata(env_emg1_list)
            plt.xlim(min(time_list), max(time_list))
            plt.ylim(200, 550)
            plt.pause(0.00001)
            display_counter = 0

    # todo: add new arrays to the offsets
    if emg_counter >= DISPLAY_SIZE:
        emg0_list = shift(emg0_list, DISPLAY_OFFSET)
        emg1_list = shift(emg1_list, DISPLAY_OFFSET)
        raw_emg0_list = shift(raw_emg0_list, DISPLAY_OFFSET)
        env_emg0_list = shift(env_emg0_list, DISPLAY_OFFSET)

        emg1_list = shift(emg1_list, DISPLAY_OFFSET)
        emg1_list = shift(emg1_list, DISPLAY_OFFSET)
        raw_emg1_list = shift(raw_emg1_list, DISPLAY_OFFSET)
        env_emg1_list = shift(env_emg1_list, DISPLAY_OFFSET)

        time_list = shift(time_list, DISPLAY_OFFSET)

        emg_counter = DISPLAY_SIZE - DISPLAY_OFFSET
