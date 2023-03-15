import pika, sys, os, io
import numpy as np
import wave
from deepspeech import Model

class DeepSpeech():
    def __init__(self) -> None:
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange="DeepSpeech", exchange_type="topic", auto_delete=True)
        self.channel.queue_declare(queue='DeepSpeech_input_audio', exclusive=True)
        self.channel.queue_bind(queue="DeepSpeech_input_audio", exchange="DeepSpeech", routing_key=f"*.*.*.audio")

        # load model
        self.model = Model("./Model/deepspeech-0.9.3-models.pbmm")
        self.model.enableExternalScorer("./Model/deepspeech-0.9.3-models.scorer")
        print("Load model successfully")

    def __callback(self, ch, method, properties, body):
        if "DeepSpeech" in method.routing_key:
            pass
        else:
            routing_key_tokens = method.routing_key.split(".")
            app_name = routing_key_tokens[0]
            client_id = routing_key_tokens[1]

            # Write your service from here
            print(f"[Request] Receive message from {app_name}.{client_id}")
            audio_ptr = io.BytesIO(body)
            fin = wave.open(audio_ptr)
            audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)
            fin.close()

            result = self.model.stt(audio)
            print(f"[Reply] Send '{result}' to {app_name}.{client_id}")
            if result:
                self.channel.basic_publish(exchange="DeepSpeech", 
                                            routing_key=f"{app_name}.{client_id}.DeepSpeech.text",
                                            body=result)

    def run(self):
        self.channel.basic_consume(queue='DeepSpeech_input_audio', on_message_callback=self.__callback, auto_ack=True)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

if __name__ == '__main__':
    try:
        detector = DeepSpeech()
        detector.run()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)