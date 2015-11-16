__author__ = 'hannah'

import pika

global output
output = 0.0

connection = pika.BlockingConnection(pika.ConnectionParameters(
               'localhost'))
channel = connection.channel()

channel.queue_declare(queue='player1')

def callback(ch, methods, properties, body):
    channel.stop_consuming()
    global output
    output = float(body)

while True:
    channel.basic_consume(callback, queue='player1', no_ack=True)
    channel.start_consuming()
    print output

connection.close()
