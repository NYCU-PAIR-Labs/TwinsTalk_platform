import pika
import pandas as pd
import numpy as np
import time

connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
channel = connection.channel()
channel.exchange_declare("sensor", "direct")

test_df = pd.read_csv('./SmartFall Testing.csv')

n = 40
number = 1
for i in range(0, len(test_df)-40, 20):
    temp = list()
    temp.append(test_df[' ms_accelerometer_x'][i : i + n])
    temp.append(test_df[' ms_accelerometer_y'][i : i + n])
    temp.append(test_df[' ms_accelerometer_z'][i : i + n])
    sensor_data = np.asarray(temp).reshape(-1, 40, 3)
    sensor_data_bytes = sensor_data.tobytes()

    channel.basic_publish(exchange='FallDetectorLSTM',
                        routing_key=f'AccidentDetect.client{number}.NULL.nparray',
                        body=sensor_data_bytes)

    print(f"Client{number} send {sensor_data[0][0]} to AccidentDetect")
    number += 1
    time.sleep(1)
connection.close()