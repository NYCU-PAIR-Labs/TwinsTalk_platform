import pika, sys, os

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.17', port=5672))
    channel = connection.channel()

    channel.queue_declare(queue='Monitor', exclusive=True)
    channel.queue_bind(queue="Monitor", exchange="AccidentDetect", routing_key="AccidentDetect.*.FallDetectorGCN.text")
    channel.queue_bind(queue="Monitor", exchange="AccidentDetect", routing_key="AccidentDetect.*.FallDetectorLSTM.text")

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)

    channel.basic_consume(queue='Monitor', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)