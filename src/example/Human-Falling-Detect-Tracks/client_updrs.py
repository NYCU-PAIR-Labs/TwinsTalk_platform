import pika
import pandas as pd
import numpy as np
import time
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--output", help="The output type of result", required=True)
args = parser.parse_args()

if args.output == "updrs":
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.17', port=5673))
    channel = connection.channel()
    def __callback(ch, method, properties, body):
        print(method.routing_key)
        with open("./leg_agility.png", "wb") as f:
            f.write(body)

    channel.queue_declare(queue="legAgility_result", exclusive=True)
    channel.queue_bind(exchange="updrsDemo", queue="legAgility_result", routing_key="updrsDemo.client1.legAgility_image")
    channel.basic_consume(queue="legAgility_result", on_message_callback=__callback, auto_ack=True)

    with open("./Video/WholeBody2_right.mp4", "rb") as video:
        data = video.read()
        print("publish")
        channel.basic_publish(exchange="updrsDemo", routing_key="updrsDemo.client1.person_video", body=data)

    connection.process_data_events(time_limit=None) # blocking operation
    print("receive image")

elif args.output == "pose":
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.17', port=5672))
    channel = connection.channel()

    def __callback(ch, method, properties, body):
        print(body)

    channel.queue_declare(queue="pose_result", exclusive=True)
    channel.queue_bind(exchange="poseDemo", queue="pose_result", routing_key="poseDemo.client1.pose_text")
    channel.basic_consume(queue="pose_result", on_message_callback=__callback, auto_ack=True)

    with open("./Video/WholeBody2_right.mp4", "rb") as video:
        data = video.read()
        print("publish")
        channel.basic_publish(exchange="poseDemo", routing_key="poseDemo.client1.person_video", body=data)

    connection.process_data_events(time_limit=None) # blocking operation

