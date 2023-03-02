import pika
import pandas as pd
import numpy as np
import time
import os

from multiprocessing import Process

def send_image(folder_idx, clientID):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
    channel = connection.channel()
    for i in sorted(os.listdir(f"./Video/fall-{folder_idx}-cam0-rgb/")):
        with open(f"./Video/fall-{folder_idx}-cam0-rgb/{i}", "rb") as f:
            data = f.read()
            channel.basic_publish(exchange='FallDetectorGCN',
                        routing_key=f'AccidentDetect.{clientID}.NULL.file',
                        body=data)
    print(f"{clientID} done.")
    connection.close()

if __name__ == "__main__":
    c1 = Process(target=send_image, args=("01", "client1"))
    c2 = Process(target=send_image, args=("09", "client2"))
    c1.start()
    c2.start()
    c1.join()
    c2.join()