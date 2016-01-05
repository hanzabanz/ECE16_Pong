import serial
import pika

__author__ = ''
"""
Description of program.
"""

# define constants

# create connection to a server on the local computer
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# create messaging queue
channel.queue_declare(queue='player1')
# change the port number and baud rate accordingly!
ser = serial.Serial('/tty/ACM0/', 9600)

# internal tracking of paddle position
y_pos = 0

while True:  # continuously run
    # read data
    # process data
    # map data to y position
    # update y position

    # publish updated y position
    channel.basic_publish(exchange='', routing_key='player1', body=str(y_pos))

# close messaging connection
connection.close()
