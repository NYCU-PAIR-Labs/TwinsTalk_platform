import pika, sys, os
import numpy as np
import cv2
import torch

from PoseEstimateLoader import SPPE_FastPose

class AlphaPose():
    def __init__(self) -> None:
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        # POSE MODEL.
        inp_pose = ["224", "160"]
        inp_pose = (int(inp_pose[0]), int(inp_pose[1]))
        self.pose_model = SPPE_FastPose("resnet50", inp_pose[0], inp_pose[1], device=self.device)

    def detect(self, img):
        # Predict skeleton pose of each bboxs.
        poses = self.pose_model.predict(img, torch.tensor([[0, 0, img.shape[1], img.shape[0]]]), torch.tensor([[1]]))

        if poses:
            return str(poses)
            
        return None

class PoseDetector():
    def __init__(self) -> None:
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange="PoseDetector", exchange_type="topic", auto_delete=True, arguments={"output":["PoseDetector_output_nparray"]})
        self.channel.queue_declare(queue='PoseDetector_input_image', exclusive=True)
        self.channel.queue_bind(queue="PoseDetector_input_image", exchange="PoseDetector", routing_key=f"*.*.*.image")
        self.channel.exchange_bind(destination="PoseDetector", source="YoloDetector", routing_key=f"*.*.YoloDetector.image")

        self.detector = AlphaPose()
        self.count = 0

    def __callback(self, ch, method, properties, body):
        if "PoseDetector" in method.routing_key:
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
                self.channel.basic_publish(exchange="PoseDetector",
                                           routing_key=f"{app_name}.{client_id}.PoseDetector.text",
                                           body=result)


    def run(self):
        self.channel.basic_consume(queue='PoseDetector_input_image', on_message_callback=self.__callback, auto_ack=True)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

if __name__ == '__main__':
    try:
        detector = PoseDetector()
        detector.run()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)