import pika, sys, os
import numpy as np
import cv2
import torch

from DetectorLoader import TinyYOLOv3_onecls


class Yolo():
    def __init__(self) -> None:
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        # DETECTION MODEL.
        inp_dets = 384
        self.detect_model = TinyYOLOv3_onecls(inp_dets, device=self.device)

    def detect(self, img):
        # Detect humans bbox in the frame with detector model.
        detected = self.detect_model.detect(img, need_resize=True, expand_bb=10)

        croped_images = []
        if detected is not None:
            for bbox in detected:
                croped = img[int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])]
                print(croped.shape)
                success, encoded_image = cv2.imencode('.png', croped)
                return encoded_image.tobytes()
            
        return None

class YoloDetector():
    def __init__(self) -> None:
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange="YoloDetector", exchange_type="topic", auto_delete=True, arguments={"output":["YoloDetector_output_image"]})
        self.channel.queue_declare(queue='YoloDetector_input_image', exclusive=True)
        self.channel.queue_bind(queue="YoloDetector_input_image", exchange="YoloDetector", routing_key=f"*.*.*.image")

        self.detector = Yolo()

    def __callback(self, ch, method, properties, body):
        if "YoloDetector" in method.routing_key:
            pass
        else:
            routing_key_tokens = method.routing_key.split(".")
            app_name = routing_key_tokens[0]
            client_id = routing_key_tokens[1]

            # Write your service from here
            img_bytes = np.frombuffer(body, dtype=np.uint8)
            img = cv2.imdecode(img_bytes, 1)

            result = self.detector.detect(img)
            if result is not None:
                self.channel.basic_publish(exchange="YoloDetector",
                                           routing_key=f"{app_name}.{client_id}.YoloDetector.image",
                                           body=result)


    def run(self):
        self.channel.basic_consume(queue='YoloDetector_input_image', on_message_callback=self.__callback, auto_ack=True)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

if __name__ == '__main__':
    try:
        detector = YoloDetector()
        detector.run()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)