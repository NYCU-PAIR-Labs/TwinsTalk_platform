import pika
import pandas as pd
import numpy as np
import time
import os

import cv2

connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
channel = connection.channel()
#channel.exchange_declare("FallDetectorGCN", "direct")

start = time.time()
count = 0
for i in sorted(os.listdir("./Video/fall-01-cam0-rgb/")):
    with open(f"./Video/fall-01-cam0-rgb/{i}", "rb") as f:
        data = f.read()
        channel.basic_publish(exchange='FallDetectorGCN',
                    routing_key=f'AccidentDetect.client1.NULL.file',
                    body=data)
        
print("done:", time.time()-start)

connection.close()