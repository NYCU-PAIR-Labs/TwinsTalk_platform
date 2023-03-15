import pika
import numpy as np
import time

def __callback(ch, method, properties, body):
    print(body)

connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
channel = connection.channel()
channel.queue_declare(queue='SpeechResult', exclusive=True)
channel.queue_bind(queue="SpeechResult", exchange="DeepSpeech", routing_key=f"AccidentDetect.client1.DeepSpeech.text")
channel.basic_consume(queue='SpeechResult', on_message_callback=__callback, auto_ack=True)

while(1):
    with open("./Audio/2830-3980-0043.wav", 'rb') as f:
        data = f.read()
    channel.basic_publish(exchange="DeepSpeech", routing_key="AccidentDetect.client1.NULL.audio", body=data)
    connection.process_data_events(time_limit=None) # blocking operation
    time.sleep(1)


connection.close()