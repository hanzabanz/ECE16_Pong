__author__ = 'hannah'

from random import randint
import pika
import time

range = 5

rand_counter = 0
inputOne = 0

# create connection to a server on the local computer
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# create queue
channel.queue_declare(queue='player1')

inputOne = -range-1

counter = 0

while True:
    # if rand_counter == 1000:
    #     inputOne = float(randint(-10, 10))/10
    #     rand_counter = 0
    # rand_counter += 1
    # channel.basic_publish(exchange='', routing_key='player1', body=str(inputOne))
    # if counter == 10:
    #     inputOne = float(randint(-range, range))
    #     print inputOne
    #     counter = 0

    inputOne = float(randint(-range, range))

    # inputOne += 0.001
    print "%s\t%s" %(inputOne, str(time.time()))
    channel.basic_publish(exchange='', routing_key='player1', body=str(inputOne))
    time.sleep(1)
    counter += 1


# Following code used to check order and frequency of read-in from main
# counter = -1.0
# while True:
#     inputOne = counter
#     channel.basic_publish(exchange='', routing_key='player1', body=str(inputOne))
#     print "%s\t%s" %(inputOne, str(time.time()))
#     counter += 0.1
#     # time.sleep(0.001)


connection.close()