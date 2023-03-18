import pika
import numpy as np
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--audio", required=True)
args = parser.parse_args()

def __callback(ch, method, properties, body):
    print(body)

connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.17', port=5672))
channel = connection.channel()
channel.queue_declare(queue='SpeechResult', exclusive=True)
channel.queue_bind(queue="SpeechResult", exchange="AccidentDetect", routing_key=f"AccidentDetect.client1.DeepSpeech.text")
channel.basic_consume(queue='SpeechResult', on_message_callback=__callback, auto_ack=True)


with open(f"./Audio/{args.audio}", 'rb') as f:
    data = f.read()
channel.basic_publish(exchange="AccidentDetect", routing_key="AccidentDetect.client1.null.audio", body=data)
connection.process_data_events(time_limit=None) # blocking operation

connection.close()