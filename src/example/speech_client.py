import pika
import numpy as np
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--audio", required=True)
args = parser.parse_args()

connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.17', port=5672))
channel = connection.channel()

with open(f"./Speech-Recognition/Audio/{args.audio}", 'rb') as f:
    data = f.read()
channel.basic_publish(exchange="AccidentDetect", routing_key="AccidentDetect.client1.wav_audio", body=data)

connection.close()