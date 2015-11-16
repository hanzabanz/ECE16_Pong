__author__ = 'hannah'

from random import randint
import pika
import time

rand_counter = 0
inputOne = 0

# create connection to a server on the local computer
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# create queue
channel.queue_declare(queue='player2')

while True:
    # if rand_counter == 1000:
    #     inputOne = float(randint(-10, 10))/10
    #     rand_counter = 0
    # rand_counter += 1
    # channel.basic_publish(exchange='', routing_key='player1', body=str(inputOne))
    inputOne = float(randint(-10, 10))/10
    channel.basic_publish(exchange='', routing_key='player2', body=str(inputOne))
    print inputOne
    time.sleep(0.005)

connection.close()