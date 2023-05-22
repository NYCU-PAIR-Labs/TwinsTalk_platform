import pika
import numpy as np
import time
import os
from multiprocessing import Process, Event

class Robot():
    def __init__(self) -> None:
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.17', port=5672))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='SpeechResult', exclusive=True)
        self.channel.queue_bind(queue="SpeechResult", exchange="AccidentDetect", routing_key=f"AccidentDetect.*.SpeechRecognition_text")
        self.channel.basic_consume(queue='SpeechResult', on_message_callback=self.__callback, auto_ack=True)

        self.publish_flag = Event()

    def __callback(self, ch, method, properties, body):
        result = body.decode()
        if(result == "go to nursing station" or result == "patrol on the second floor"):
            self.publish_flag.set()
        else:
            print("stop")
            self.publish_flag.clear()

    def publish(self):
        self.publish_connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.17', port=5672))
        self.publish_channel = self.publish_connection.channel()
        while(1):
            self.publish_flag.wait(1)
            if(self.publish_flag.is_set()):
                print("start publish")
                for i in sorted(os.listdir(f"./Human-Falling-Detect-Tracks/Video/fall-01-cam0-rgb/")):
                    with open(f"./Human-Falling-Detect-Tracks/Video/fall-01-cam0-rgb/{i}", "rb") as f:
                        data = f.read()
                        self.publish_channel.basic_publish(exchange='AccidentDetect',
                                    routing_key=f'AccidentDetect.robot1.png_image',
                                body=data)
                    if(not self.publish_flag.is_set()):
                        break
                break
        self.publish_channel.close()

    def run(self):
        self.publish_process = Process(target=self.publish)
        self.publish_process.start()
        self.channel.start_consuming()


if __name__ == "__main__":
    robot = Robot()
    robot.run()