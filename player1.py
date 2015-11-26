__author__ = 'hannah'


"""
Simple filters.

-> Buffer[] is a queue where the new filter is applied each time
"""

import serial
import time
import pika
import matplotlib.pyplot as plt
import math


def squareFilter(bw, weight):
    filter = []
    for num in range(bw):
        filter.append(weight)
    return filter

def highPass(bw, weight):
    filter = [-1, 8, -1]
    return filter


# Defining constants
EMG0_LOC = 1
EMG1_LOC = 3
TIME_LOC = 5

TIME_LIMIT = 350
BUFFER_SIZE = 4
AVG_SIZE = 5

DISPLAY_SIZE = 300

SHAPE_TYPE = 0

HIGH = 350
BASE = 300


# create connection to a server on the local computer
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# create queue
channel.queue_declare(queue='player1')


# to write new file
emg0_file = open("emg_file.txt", "w")
emg1_file = open("emg1_file.txt", "w")
time_file = open("time_file.txt", "w")
# to append, use "a"


ser = serial.Serial('COM3', 9600)

# set to 0 as the baseline (baseline should be normalized in arduino)
emg0_buffer = [0 for i in range(BUFFER_SIZE)]
emg1_buffer = [0 for i in range(BUFFER_SIZE)]

# emg0_list = [0 for i in range(DISPLAY_SIZE)]
# emg1_list = [0 for i in range(DISPLAY_SIZE)]
# time_list = [i for i in range(DISPLAY_SIZE)]

emg0_list = []
emg1_list = []
time_list = []

emg_counter = 0

time.sleep(1)

beg = time.time()
end = time.time() + TIME_LIMIT # end is equal to time in x seconds, x being the int at the end

counter = 0
list_counter = 0
output = 0
direction = 0
delay = 0
base_counter = 0


while time.time() < end:
    data = ser.readline()
    data_split = data.split('\t')
    if len(data_split) < 3:
        print "length"
        continue

    try:
        emg0_buffer[emg_counter] = int(data_split[EMG0_LOC])
        emg1_buffer[emg_counter] = int(data_split[EMG1_LOC])
        time_signal = int(data_split[TIME_LOC])

        emg0_file.write(str(data_split[EMG0_LOC]))
        emg0_file.write('\n')
        emg1_file.write(str(data_split[EMG1_LOC]))
        emg1_file.write('\n')
        time_file.write(str(data_split[TIME_LOC]))
    except ValueError:
        continue


    emg_counter += 1
    if emg_counter == BUFFER_SIZE:
        emg_counter = 0
        ## RESET X AXIS ##
    #     emg0_list = [0 for i in range(BUFFER_SIZE)]
    #     emg1_list = [0 for i in range(BUFFER_SIZE)]

    temp0_list = [0,0,0]
    temp1_list = [0,0,0]

    # IMPLEMENT SHAPE SMOOTHING
    for i in range(BUFFER_SIZE-2):
        filter = squareFilter(BUFFER_SIZE, 1)
        temp0_list[i] = (emg0_buffer[i] + emg0_buffer[i+1] + emg0_buffer[i+2])/3
        temp1_list[i] = (emg0_buffer[i] + emg0_buffer[i+1] + emg0_buffer[i+2])/3

    og_counter = len(emg0_list)-1

    if temp0_list[0] > 10:
        emg0_list.append(temp0_list[0])
        emg1_list.append(0)
        list_counter += 1
    if temp0_list[1] > 10:
        emg0_list.append(temp0_list[1])
        emg1_list.append(0)
        list_counter += 1
    if temp0_list[2] > 10:
        emg0_list.append(temp0_list[2])
        emg1_list.append(0)
        list_counter += 1

    if delay == 5:
        if(290 < emg0_list[og_counter] < 310):
            base_counter += 1
            if(base_counter == 10):
                output = 0
                base_counter = 0
        if(310 < emg0_list[og_counter] < 410):
            temp = emg0_list[og_counter]
            temp -= 310
            temp /= 10
            if direction == 0:
                output = temp
                direction = 1
            elif direction == 1:
                output = 0
                direction = 0

            if output < 0:
                output = 0
            elif output > 10:
                output = 10

            base_counter = 0

        channel.basic_publish(exchange='', routing_key='player1', body=str(output))
        delay = 0
    delay += 1

    plt.clf()

    # plot emg
    plt.subplot(2,1,1)
    plt.title('EMG 0')
    plt.axis([0,200, -100,600])
    plt.plot(emg0_list)

    # plot sync
    plt.subplot(2,1,2)
    plt.title('EMG 1')
    plt.plot(emg1_list)

    plt.draw()

    # if emg0_list[list_counter+1] < 300:
    #     if temp > 1:

    # time_list.append(time_signal)

    if list_counter >= DISPLAY_SIZE:
        emg0_list = []
        emg1_list = []
        list_counter = 0

connection.close()
emg0_file.close()
emg1_file.close()
time_file.close()
