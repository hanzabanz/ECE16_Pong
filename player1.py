import serial
import time
import pika
import matplotlib.pyplot as plt
import math

__author__ = 'hannah'
"""
Simple implementation of EMG control.
"""


def shift(seq, num):
    return seq[num:] + [0 for i in range(num)]

# Defining constants
EMG0_LOC = 1
EMG1_LOC = 3
TIME_LOC = 5

TIME_LIMIT = 500
BUFFER_SIZE = 4
AVG_SIZE = 5 # only odd numbers work well

DISPLAY_SIZE = 200
DISPLAY_OFFSET = DISPLAY_SIZE/20

SHAPE_TYPE = 0

# Individual calibration values to be changed every time
HIGH = 350
BASE = 300

UPPER_BOUND = 20
LOWER_BOUND = -20


# to write new file
emg0_file = open("emg_file.txt", "w")
emg1_file = open("emg1_file.txt", "w")
time_file = open("time_file.txt", "w")
# to append, use "a"


# create connection to a server on the local computer
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# create queue
channel.queue_declare(queue='player1')
ser = serial.Serial('COM6', 9600)

# set to 0 as the baseline (baseline should be normalized in arduino)
raw_emg0_list = [0 for i in range(DISPLAY_SIZE)]

emg0_buffer = [0 for i in range(AVG_SIZE)]
emg1_buffer = [0 for i in range(AVG_SIZE)]

raw_emg0_list = [0 for i in range(DISPLAY_SIZE)]
raw_emg1_list = [0 for i in range(DISPLAY_SIZE)]

emg0_list = [0 for i in range(DISPLAY_SIZE)]
emg1_list = [0 for i in range(DISPLAY_SIZE)]
time_list = [0 for i in range(DISPLAY_SIZE)]

hpf_emg0_list = [0 for i in range(DISPLAY_SIZE)]
hpf_emg1_list = [0 for i in range(DISPLAY_SIZE)]

env_emg0_list = [0 for i in range(DISPLAY_SIZE)]
env_buf_emg0_list = [0 for i in range(AVG_SIZE)]

env_emg1_list = [0 for i in range(DISPLAY_SIZE)]
env_buf_emg1_list = [0 for i in range(AVG_SIZE)]

emg_counter = 0
buffer_counter = 0
initial = False
secondary = False
hpf_sign = True
list_counter = 0
display_counter = 0

init_time = 0

plot_num = 0

# internal tracking of paddle position
y_pos = 0

time.sleep(1)

beg = time.time()
end = time.time() + TIME_LIMIT # end is equal to time in x seconds, x being the int at the end

plt.figure()
plt.ion()
plt.show()


while time.time() < end:
    data = ser.readline()
    data_split = data.split('\t')
    if len(data_split) < 5:
        continue

    try:
        emg0_buffer[buffer_counter] = int(data_split[EMG0_LOC])
        emg1_buffer[buffer_counter] = int(data_split[EMG1_LOC])
        raw_emg0_list[emg_counter] = int(data_split[EMG0_LOC])
        raw_emg1_list[emg_counter] = int(data_split[EMG1_LOC])

        time_signal = int(data_split[TIME_LOC])

        emg0_file.write(str(data_split[EMG0_LOC]))
        emg0_file.write('\n')
        emg1_file.write(str(data_split[EMG1_LOC]))
        emg1_file.write('\n')
        time_file.write(str(data_split[TIME_LOC]))
    except ValueError:
        print "error"
        continue

    if not initial:
        emg0_list[emg_counter] = data_split[EMG0_LOC]
        emg1_list[emg_counter] = data_split[EMG1_LOC]
        if hpf_sign == False:
            hpf_emg0_list[emg_counter] = -int(data_split[EMG0_LOC])
            hpf_emg1_list[emg_counter] = -int(data_split[EMG1_LOC])
            hpf_sign = True
        else:
            hpf_emg0_list[emg_counter] = int(data_split[EMG0_LOC])
            hpf_emg1_list[emg_counter] = int(data_split[EMG1_LOC])
            hpf_sign = False

        env_buf_emg0_list[buffer_counter] = int(emg0_list[emg_counter])*int(emg0_list[emg_counter])
        env_emg0_list[emg_counter] = env_buf_emg0_list[emg_counter]
        env_buf_emg1_list[buffer_counter] = int(emg1_list[emg_counter])*int(emg1_list[emg_counter])
        env_emg1_list[emg_counter] = env_buf_emg1_list[emg_counter]

    else:
        emg0_list[emg_counter] = sum(emg0_buffer)/AVG_SIZE
        emg1_list[emg_counter] = sum(emg1_buffer)/AVG_SIZE
        if hpf_sign == False:
            hpf_emg0_list[emg_counter] = -sum(emg0_buffer)/AVG_SIZE
            hpf_emg1_list[emg_counter] = -sum(emg1_buffer)/AVG_SIZE
            hpf_sign = True
        else:
            hpf_emg0_list[emg_counter] = sum(emg0_buffer)/AVG_SIZE
            hpf_emg1_list[emg_counter] = sum(emg1_buffer)/AVG_SIZE
            hpf_sign = False

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


    temp0 = 0
    temp1 = 0
    value0 = env_emg0_list[emg_counter]
    value1 = env_emg1_list[emg_counter]

    print "%f\t%f" %(value0, value1)

    # Set internal velocity values
    if value0 > 308 or value0 < 297:
        # temp0 = 10 - int((324-value0)/1.5)
        temp0 = 2
    if value1 > 306 or value1 < 295:
        # temp1 = -(10 - int((319-value1)/1.5))
        temp1 = -2

    # Convert velocity values to y axis position
    if temp0 > 0:
        y_pos += temp0
    if temp1 < 0:
        y_pos += temp1

    if y_pos > UPPER_BOUND:
        y_pos == UPPER_BOUND
    if y_pos < LOWER_BOUND:
        y_pos == LOWER_BOUND


    # if temp0 != 0:
    #     output = str(temp0)

    print "%f\t%f\t%s" %(temp0, temp1, y_pos)

    # output = str(temp0 + temp1)
    channel.basic_publish(exchange='', routing_key='player1', body=str(y_pos))

    buffer_counter += 1
    emg_counter += 1
    if buffer_counter == AVG_SIZE:
        if initial:
            secondary = True
        initial = True
        buffer_counter = 0


    plt.clf()

    plt.subplot(4,1,1)
    plt.title('Raw EMG0')
    plt.plot(raw_emg0_list)
    plt.axis([0, DISPLAY_SIZE, 275, 340])

    plt.subplot(4,1,2)
    plt.title('LPF EMG0')
    plt.plot(emg0_list)
    plt.axis([0, DISPLAY_SIZE, 275, 340])

    plt.subplot(4,1,3)
    plt.title('HPF EMG0')
    plt.plot(hpf_emg0_list)
    plt.axis([0, DISPLAY_SIZE, -375, 375])

    plt.subplot(4,1,4)
    plt.title('HPF EMG0')
    plt.plot(env_emg0_list)
    plt.axis([0, DISPLAY_SIZE, 275, 340])

    display_counter += 1
    if display_counter == 5:
        plt.clf()

        plt.subplot(2,1,1)
        plt.title('HPF EMG0')
        plt.plot(env_emg0_list)
        plt.axis([0, DISPLAY_SIZE, 275, 340])

        plt.subplot(2,1,2)
        plt.title('HPF EMG1')
        plt.plot(env_emg1_list)
        plt.axis([0, DISPLAY_SIZE, 275, 340])
        display_counter = 0
        plt.draw()

        plt.pause(0.0001)

    plt.draw()

    plt.pause(0.0001)

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

        emg_counter = DISPLAY_SIZE - DISPLAY_OFFSET

        # plot_name = "plot_" + str(plot_num)
        # plt.savefig(plot_name)
        # plot_num += 1

connection.close()
plt.savefig('plot')
emg0_file.close()
emg1_file.close()
time_file.close()
