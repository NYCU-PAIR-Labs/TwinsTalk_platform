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
            channel.basic_publish(exchange='YoloDetector',
                        routing_key=f'AccidentDetect.{clientID}.null.image',
                        body=data)
    print(f"{clientID} done.")
    connection.close()

if __name__ == "__main__":
    processes = []
    start_time = time.time()
    for i in range(1,2):
        p = Process(target=send_image, args=("01", f"client{i}"))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    print(time.time() - start_time)