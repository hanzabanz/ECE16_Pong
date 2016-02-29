__author__ = 'hannah'

import serial

ser = serial.Serial("COM7", 115200)

with open('emg_data_half_sustain.txt', 'w+') as f:
    try:
        while True:
            line = ser.readline()
            f.write(line)
    except KeyboardInterrupt:
        pass