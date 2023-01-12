import pika
import time

connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.17', port=5672))
channel = connection.channel()

channel.basic_publish(exchange='app1',
                    routing_key='app1.client1.null.image',
                    body='123')

print(f"Send message to app1")
connection.close()