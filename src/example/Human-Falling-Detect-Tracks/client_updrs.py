import pika
import pandas as pd
import numpy as np
import time
import os

connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
channel = connection.channel()

def __callback(ch, method, properties, body):
    print(method.routing_key)
    with open("./leg_agility.png", "wb") as f:
        f.write(body)

channel.queue_declare(queue="legAgility_result", exclusive=True)
channel.queue_bind(exchange="UPDRS", queue="legAgility_result", routing_key="test.client1.*.image")
channel.basic_consume(queue="legAgility_result", on_message_callback=__callback, auto_ack=True)

with open("./Video/WholeBody2_right.mp4", "rb") as video:
    data = video.read()
    print("publish")
    channel.basic_publish(exchange="UPDRS", routing_key="test.client1.null.video", body=data)

connection.process_data_events(time_limit=None) # blocking operation

