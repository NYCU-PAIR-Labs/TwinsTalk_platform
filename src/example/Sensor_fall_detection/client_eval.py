import pika
import pandas as pd
import numpy as np
import time

connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
channel = connection.channel()

test_df = pd.read_csv('./SmartFall Testing.csv')

n = 40
client_datas = []

for i in range(360, 40200, 20):
    temp = list()
    temp.append(test_df[' ms_accelerometer_x'][i : i + n])
    temp.append(test_df[' ms_accelerometer_y'][i : i + n])
    temp.append(test_df[' ms_accelerometer_z'][i : i + n])
    sensor_data = np.asarray(temp).reshape(-1, 40, 3)
    sensor_data_bytes = sensor_data.tobytes()
    client_datas.append(sensor_data_bytes)

for count in range(5):
    print("test:", count+1)
    start_time = time.time()
    number = 0
    while(number < 10):
        for i, data in enumerate(client_datas, start=1):
            channel.basic_publish(exchange='FallDetectorLSTM',
                                routing_key=f'AccidentDetect.client{i}.NULL.nparray',
                                body=data)
        number += 1
        time.sleep(1)
        
    print("Complete time:", time.time() - start_time)
    time.sleep(5)
    

connection.close()