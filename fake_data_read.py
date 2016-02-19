__author__ = 'hannah'
import time
import math
import matplotlib
import matplotlib.pyplot as plt

"""
LPF implemented.
HPF implemented.
Env implemented.

EMG0 and EMG1 both implemented.
"""


def shift(seq, num):
    return seq[num:] + [0 for i in range(num)]


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
EMG1_LOC = 1
TIME_LOC = 0

TIME_LIMIT = 100
BUFFER_SIZE = 1
AVG_SIZE = 1 # only odd numbers work well

DISPLAY_SIZE = 1000
DISPLAY_OFFSET = DISPLAY_SIZE/20

SHAPE_TYPE = 0

HIGH = 350
BASE = 300


# to write new file
emg0_file = open("emg_file.txt", "w")
emg1_file = open("emg1_file.txt", "w")
time_file = open("time_file.txt", "w")
# to append, use "a"


# ser = serial.Serial('COM3', 9600)

# set to 0 as the baseline (baseline should be normalized in arduino)
raw_emg0_list = [0 for i in range(DISPLAY_SIZE)]

emg0_buffer = [0 for i in range(AVG_SIZE)]
emg1_buffer = [0 for i in range(AVG_SIZE)]

raw_emg0_list = [0 for i in range(DISPLAY_SIZE)]

emg0_list = [0 for i in range(DISPLAY_SIZE)]
emg1_list = [0 for i in range(DISPLAY_SIZE)]
time_list = [0 for i in range(DISPLAY_SIZE)]

hpf_emg0_list = [0 for i in range(DISPLAY_SIZE)]

env_emg0_list = [0 for i in range(DISPLAY_SIZE)]
env_buf_emg0_list = [0 for i in range(AVG_SIZE)]

emg_counter = 0
buffer_counter = 0
initial = False
secondary = False
hpf_sign = True

display_counter = 0

time.sleep(1)

beg = time.time()
end = time.time() + TIME_LIMIT # end is equal to time in x seconds, x being the int at the end

list_counter = 0
plot_num = 0

matplotlib.use('TkAgg')
# fig = plt.figure()
plt.ion()
plt.show()


with open("fake_emg_data_6", "r") as f:
    while time.time() < end:
        data = f.readline()
        if data == "\n":
            break
        data_split = data.split(' ')
        if len(data_split) < 2 or len(data_split) > 3 or not 11 < len(data) < 17 :
            continue
        try:
            emg0_buffer[buffer_counter] = float(data_split[EMG0_LOC])
            emg1_buffer[buffer_counter] = float(data_split[EMG1_LOC])
            raw_emg0_list[emg_counter] = float(data_split[EMG0_LOC])

            time_signal = float(data_split[TIME_LOC])

            emg0_file.write(str(int(float(data_split[TIME_LOC]))) + " " + str(int(float(data_split[EMG0_LOC])*1023/5)))
            emg0_file.write("\n")
            emg1_file.write(str(int(float(data_split[EMG1_LOC]))))
            time_file.write(str(int(float(data_split[TIME_LOC]))))
        except ValueError:
            continue

        # if not initial:
        #     emg0_list[emg_counter] = data_split[EMG0_LOC]
        #     if hpf_sign == False:
        #         hpf_emg0_list[emg_counter] = -float(data_split[EMG0_LOC])
        #         hpf_sign = True
        #     else:
        #         hpf_emg0_list[emg_counter] = float(data_split[EMG0_LOC])
        #         hpf_sign = False
        #
        #     env_buf_emg0_list[buffer_counter] = float(emg0_list[emg_counter])*float(emg0_list[emg_counter])
        #     env_emg0_list[emg_counter] = env_buf_emg0_list[emg_counter]
        #
        # else:
        #     emg0_list[emg_counter] = sum(emg0_buffer)/AVG_SIZE
        #     if hpf_sign == False:
        #         hpf_emg0_list[emg_counter] = -sum(emg0_buffer)/AVG_SIZE
        #         hpf_sign = True
        #     else:
        #         hpf_emg0_list[emg_counter] = sum(emg0_buffer)/AVG_SIZE
        #         hpf_sign = False
        #
        #     env_buf_emg0_list[buffer_counter] = float(emg0_list[emg_counter])*float(emg0_list[emg_counter])
        #     if not secondary:
        #         env_emg0_list[emg_counter] = env_buf_emg0_list[buffer_counter]
        #     else:
        #         env_emg0_list[emg_counter] = sum(env_buf_emg0_list)/AVG_SIZE
        #
        # env_emg0_list[emg_counter] = math.sqrt(float(env_emg0_list[emg_counter]))
        #
        # print env_emg0_list

        env_emg0_list[emg_counter] = emg0_buffer[buffer_counter]


        buffer_counter += 1
        emg_counter += 1
        if buffer_counter == AVG_SIZE:
            if initial:
                secondary = True
            initial = True
            buffer_counter = 0

        # plt.clf()
        #
        # plt.subplot(4,1,1)
        # plt.title('Raw EMG0')
        # plt.plot(raw_emg0_list)
        # plt.axis([0, DISPLAY_SIZE, 275, 340])
        #
        # plt.subplot(4,1,2)
        # plt.title('LPF EMG0')
        # plt.plot(emg0_list)
        # plt.axis([0, DISPLAY_SIZE, 275, 340])
        #
        # plt.subplot(4,1,3)
        # plt.title('HPF EMG0')
        # plt.plot(hpf_emg0_list)
        # plt.axis([0, DISPLAY_SIZE, -375, 375])
        #
        # plt.subplot(4,1,4)
        # plt.title('HPF EMG0')
        # plt.plot(env_emg0_list)
        # plt.axis([0, DISPLAY_SIZE, 275, 340])

        display_counter += 1
        if display_counter == 100:
            plt.clf()

            plt.title('HPF EMG0')
            plt.plot(env_emg0_list)
            display_counter = 0
            plt.axis([0, DISPLAY_SIZE, 1, 2])
            plt.draw()
            plt.pause(0.01)


        if emg_counter >= DISPLAY_SIZE:
            emg0_list = shift(emg0_list, DISPLAY_OFFSET)
            emg1_list = shift(emg1_list, DISPLAY_OFFSET)
            raw_emg0_list = shift(raw_emg0_list, DISPLAY_OFFSET)
            env_emg0_list = shift(env_emg0_list, DISPLAY_OFFSET)
            emg_counter = DISPLAY_SIZE - DISPLAY_OFFSET

            plot_name = "plot_" + str(plot_num)
            plt.savefig(plot_name)
            plot_num += 1

# plt.savefig('plot')
emg0_file.close()
emg1_file.close()
time_file.close()
