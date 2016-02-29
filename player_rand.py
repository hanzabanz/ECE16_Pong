__author__ = 'hannah'

from random import randint
import pika
import time
import socket

pos_range = 0.5
pos_offset = 0.5
vel_range = 1
vel_factor = 0.05

rand_counter = 0
inputOne = 0

# create connection to a server on the local computer
# connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
# channel = connection.channel()
#
# # create queue
# channel.queue_declare(queue='player1')

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


inputOne = -pos_range-1

y_pos = 0

counter = 0

while True:
    # ## Following code for input based on position ##
    # inputOne = float(randint(-pos_range, pos_range))
    #
    # # inputOne += 0.001
    # print "%s\t%s" %(inputOne, str(time.time()))
    # channel.basic_publish(exchange='', routing_key='player1', body=str(inputOne))
    # time.sleep(1)

    ## Following code for input based on velocity ##
    # Set internal velocity values by randomizing
    if counter == 5:
        inputOne = float(randint(-vel_range, vel_range)*vel_factor)
        counter = 0

    # Convert velocity values to y axis position
    if counter%5== 0:
        y_pos += (inputOne)
        if y_pos > pos_range:
            y_pos = pos_range
        if y_pos < -pos_range:
            y_pos = -pos_range
        y_pos_final = y_pos + pos_offset

    #channel.basic_publish(exchange='', routing_key='player1', body=str(y_pos))
    y_pos = float(y_pos)
    sock.sendto(str(float(y_pos_final)), (UDP_IP,UDP_PORT))
    time.sleep(0.00001) # MUST HAVE DELAY LARGER THAN 0.005!
    print y_pos_final
    counter += 1


# Following code used to check order and frequency of read-in from main
# counter = -1.0
# while True:
#     inputOne = counter
#     channel.basic_publish(exchange='', routing_key='player1', body=str(inputOne))
#     print "%s\t%s" %(inputOne, str(time.time()))
#     counter += 0.1
#     # time.sleep(0.001)


# connection.close()