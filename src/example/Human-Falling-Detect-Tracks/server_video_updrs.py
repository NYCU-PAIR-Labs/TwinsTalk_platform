import pika, sys, os, io
import numpy as np

from scipy import signal
from matplotlib import pyplot as plt

class UPDRS():
    def __init__(self) -> None:
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange="UPDRS", exchange_type="topic", auto_delete=True, arguments={"output":["UPDRS_output_image"]})
        self.channel.queue_declare(queue='UPDRS_input_nparray', exclusive=True)
        self.channel.queue_bind(queue="UPDRS_input_nparray", exchange="UPDRS", routing_key=f"*.*.*.nparray")

        # self.channel.exchange_bind(destination="UPDRS", source="Pose", routing_key="*.*.Pose.nparray")

        self.count = 0

    def __callback(self, ch, method, properties, body):
        if "UPDRS" in method.routing_key:
            pass
        else:
            routing_key_tokens = method.routing_key.split(".")
            app_name = routing_key_tokens[0]
            client_id = routing_key_tokens[1]

            # Write your service from here
            print(f"receivce from {client_id}")
            rankles = np.frombuffer(body, dtype=np.float32)
            peaks, _ = signal.find_peaks(rankles, height=1270, prominence=20)
            print("Action count:", len(peaks))
            plt.title(f"stomp_count={len(peaks)}")
            plt.plot(rankles)
            plt.plot(peaks,np.array(rankles)[peaks],"x")
            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)

            self.channel.basic_publish(exchange="UPDRS",
                                           routing_key=f"{app_name}.{client_id}.UPDRS.image",
                                           body=buf.read())


    def run(self):
        self.channel.basic_consume(queue='UPDRS_input_nparray', on_message_callback=self.__callback, auto_ack=True)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

if __name__ == '__main__':
    try:
        detector = UPDRS()
        detector.run()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
