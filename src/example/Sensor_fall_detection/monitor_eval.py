import pika, sys, os, time

class Monitor():
    def __init__(self) -> None:
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue='Monitor', exclusive=True)
        self.channel.queue_bind(queue="Monitor", exchange="FallDetectorLSTM", routing_key="AccidentDetect.*.*.text")
        # self.channel.queue_bind(queue="Monitor", exchange="FallDetectorGCN", routing_key="AccidentDetect.*.*.text")

        self.start_time = None
        self.end_time = None
        self.count = 0
        self.record = []
        self.test = 0

    def callback(self, ch, method, properties, body):
        message = body.decode()
        # print("[x] Receive", message)
        self.count += 1
        if self.count == 1:
            self.start_time = time.time()
        # 650 = 5 client, each 130 results
        # 66 for 1 sensor client (1992 datas) 
        elif self.count == 660: 
            self.end_time = time.time()-self.start_time
            self.record.append(self.end_time)
            print("Completion time:", self.end_time)
            self.count = 0
            self.test += 1
        if self.test == 5:
            print("Avg:", sum(self.record) / len(self.record)) 

    def run(self):
        self.channel.basic_consume(queue='Monitor', on_message_callback=self.callback, auto_ack=True)
        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()
        

if __name__ == '__main__':
    try:
        monitor = Monitor()
        monitor.run()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)