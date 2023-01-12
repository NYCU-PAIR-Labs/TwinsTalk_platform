import pika, sys, os, time, json
import signal
from multiprocessing import Process
import argparse

class AppQueueConsumer(Process):
    def __init__(self, json_file) -> None:
        Process.__init__(self)
        self.central_connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
        self.central_channel = self.central_connection.channel()
        self.app_connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.17', port=5672))
        self.app_channel = self.app_connection.channel()

        self.input_queue = []
        self.publish_table = {}

        self.parse_config(json_file)

        # Set callback function of input queue
        for input in self.input_queue:
            self.app_channel.basic_consume(queue=input, on_message_callback=self.__input_queue_callback, auto_ack=True)

    def parse_config(self, json_file:str) -> bool:
        with open(json_file) as f:
            cfg = json.load(f)
        
        # create app exchange in app broker
        self.name = cfg["name"]
        print(f"Create Exchange in [{self.name}] broker")
        self.app_channel.exchange_declare(exchange=self.name, exchange_type="topic", auto_delete=True)

        # create queue in app broker to receive client's messages
        for input in cfg["input"]:
            self.input_queue.append(input["queue"])
            self.app_channel.queue_declare(queue=input["queue"], exclusive=True)
            # binding key = <app>.<client>.<server>.<datatype>
            self.app_channel.queue_bind(exchange=self.name, queue=input["queue"], routing_key=f"{self.name}.*.null.{input['datatype']}")
        print("Input queue:", self.input_queue)

        # parse topology
        for link in cfg["topology"]:
            # Create input-server publish table
            if link["source"]["type"] == "input":
                src_queue = link["source"]["queue"]
                self.publish_table[src_queue] = []
                for dst in link["destination"]:
                    self.publish_table[src_queue].append(dst["queue"])
        print("Publish table:", self.publish_table)

    def __input_queue_callback(self, ch, method, properties, body):
        '''
        method: [consumer_tag, delivery_tag, exchange, redelivered, routing_key]
        '''
        # client's message routing key = <app>.<clientID>.<null>.<datatype>
        print(f"Receive {body} with routing key {method.routing_key}")
        for input_queue in self.publish_table.keys():
            queue_datatype = input_queue.split("_")[-1]
            message_datatype = method.routing_key.split(".")[-1]

            if queue_datatype == message_datatype:
                for server_queue in self.publish_table[input_queue]:
                    server_exchange = server_queue.split("_")[0]
                    self.central_channel.basic_publish(exchange=server_exchange, routing_key=method.routing_key, body=body)

    def run(self):
        print("Start App consumer")
        try:
            self.app_channel.start_consuming()
        except KeyboardInterrupt:
            print("Stop App consumer")
            self.app_channel.stop_consuming()
            return

class CentralQueueConsumer(Process):
    def __init__(self, json_file) -> None:
        Process.__init__(self)
        self.central_connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
        self.central_channel = self.central_connection.channel()
        self.app_connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.17', port=5672))
        self.app_channel = self.app_connection.channel()

        self.output_queue = []
        self.exchange_binding_table = {}
        self.queue_binding_table = {}

        self.parse_config(json_file)
        self.set_exchange_binding()
        self.set_output_queue_binding()

        # Set callback function of output queue
        for output in self.output_queue:
            self.central_channel.basic_consume(queue=output, on_message_callback=self.__output_queue_callback, auto_ack=True)

    def parse_config(self, json_file:str) -> bool:
        with open(json_file) as f:
            cfg = json.load(f)

        self.name = cfg["name"]

        # parse output part
        for output in cfg["output"]:
            self.output_queue.append(output["queue"])
            self.central_channel.queue_declare(queue=output["queue"], exclusive=True)
        print("Output queue:", self.output_queue)

        # parse topology
        for link in cfg["topology"]:
            if link["source"]["type"] == "server":
                src_queue = link["source"]["queue"]
                self.exchange_binding_table[src_queue] = []
                self.queue_binding_table[src_queue] = []
                for dst in link["destination"]:
                    # Create server-server exchange binding table
                    if dst["type"] == "server":
                        self.exchange_binding_table[src_queue].append(dst["queue"])

                    # Create server-output queue binding table
                    if dst["type"] == "output":
                        self.queue_binding_table[src_queue].append(dst["queue"])
        print("Exchange table:", self.exchange_binding_table)
        print("Queue table:", self.queue_binding_table)

    def set_exchange_binding(self) -> None:
        for src_queue in self.exchange_binding_table.keys():
            src_exchange = src_queue.split("_")[0]
            for dst_queue in self.exchange_binding_table[src_queue]:
                dst_exchange = dst_queue.split("_")[0]
                datatype = dst_queue.split("_")[-1]
                self.central_channel.exchange_bind(destination=dst_exchange, source=src_exchange, routing_key=f"{self.name}.*.{src_exchange}.{datatype}")

    def set_output_queue_binding(self) -> None:
        for src_queue in self.queue_binding_table.keys():
            src_exchange = src_queue.split("_")[0]
            for dst_queue in self.queue_binding_table[src_queue]:
                datatype = dst_queue.split("_")[-1]
                self.central_channel.queue_bind(exchange=src_exchange, queue=dst_queue, routing_key=f"{self.name}.*.{src_exchange}.{datatype}")

    def __output_queue_callback(self, ch, method, properties, body):
        '''
        method: [consumer_tag, delivery_tag, exchange, redelivered, routing_key]
        '''
        print(f"Receive {body} with routing key {method.routing_key}")
        self.app_channel.basic_publish(exchange=self.name, routing_key=method.routing_key, body=body)

    def run(self):
        print("Start Central consumer")
        try:
            self.central_channel.start_consuming()
        except KeyboardInterrupt:
            print("Stop Central consumer")
            self.central_channel.stop_consuming()
            return

    def __del__(self):
        print("Unbind exchange in this app")
        for src_queue in self.exchange_binding_table.keys():
            src_exchange = src_queue.split("_")[0]
            for dst_queue in self.exchange_binding_table[src_queue]:
                dst_exchange = dst_queue.split("_")[0]
                datatype = dst_queue.split("_")[-1]
                self.central_channel.exchange_unbind(destination=dst_exchange, source=src_exchange, routing_key=f"{self.name}.*.{src_exchange}.{datatype}")

class App():
    def __init__(self, json_file) -> None:
        self.app_consumer = AppQueueConsumer(json_file)
        self.central_consumer = CentralQueueConsumer(json_file)

    def run(self):
        self.app_consumer.start()
        self.central_consumer.start()
        self.app_consumer.join()
        self.central_consumer.join()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", help="The app configuration file path", required=True)
    args = parser.parse_args()
    try:
        app_consumer = AppQueueConsumer(args.cfg)
        central_consumer = CentralQueueConsumer(args.cfg)
        app_consumer.start()
        central_consumer.start()
        print("App consumer PID:", app_consumer.pid)
        print("Central consumer PID:", central_consumer.pid)
        app_consumer.join()
        central_consumer.join()
    except KeyboardInterrupt:
        try:
            print('Stop app')
            os.kill(app_consumer.pid, signal.SIGINT)
            os.kill(central_consumer.pid, signal.SIGINT)
        except:
            sys.exit(0)