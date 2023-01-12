import pika, sys, os

class Server():
    def __init__(self, name) -> None:
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10'))
        self.channel = self.connection.channel()
        self.name = name
        self.inputs_datatype = ["image", "json"] # user-define input datatypes
        self.outputs_datatype = ["image", "json"] # user-define output datatypes
        self.outputs = [f"{self.name}_output_{datatpye}" for datatpye in self.outputs_datatype]
        self.callbacks = [self.__callback1, self.__callback2] # user-define callbacks

    def set_exchange(self) -> None:
        self.channel.exchange_declare(exchange=self.name, exchange_type="topic", auto_delete=True, arguments={"output":self.outputs})

    def set_queue(self) -> None:
        for datatype in self.inputs_datatype:
            queue_name = f'{self.name}_input_{datatype}'
            self.channel.queue_declare(queue=queue_name, exclusive=True)
            self.channel.queue_bind(exchange=self.name, queue=queue_name, routing_key=f"*.*.*.{datatype}")

    def run(self) -> None:
        self.set_exchange()
        self.set_queue()

        for datatype, callback in zip(self.inputs_datatype, self.callbacks):
            queue_name = f'{self.name}_input_{datatype}'
            self.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

    def __callback1(self, ch, method, properties, body):
        if self.name in method.routing_key:
            print("Skip")
        else:
            routing_key_tokens = method.routing_key.split(".")
            app_name = routing_key_tokens[0]
            client_id = routing_key_tokens[1]

            # Write your service from here
            print(f"[c1] Received {body} with key {method.routing_key}")
            self.channel.basic_publish(exchange=self.name,
                            routing_key=f"{app_name}.{client_id}.{self.name}.image",
                            body=body.decode('utf-8')+f's1c1')
            print("Write s1c1 to client")

    def __callback2(self, ch, method, properties, body):
        if self.name in method.routing_key:
            print("Skip")
        else:
            routing_key_tokens = method.routing_key.split(".")
            app_name = routing_key_tokens[0]
            client_id = routing_key_tokens[1]

            # Write your service from here
            print(" [c2] Received %r" % body)
            self.channel.basic_publish(exchange=self.name,
                            routing_key=f"{app_name}.{client_id}.{self.name}.json",
                            body=body.decode('utf-8')+f's1c2')
            print("Write s1c2 to client")
    

if __name__ == '__main__':
    try:
        server = Server(name="server1")
        server.run()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

