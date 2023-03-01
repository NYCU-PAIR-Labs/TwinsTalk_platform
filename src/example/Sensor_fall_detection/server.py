import pika, sys, os
import numpy as np
import torch
from torch import nn

class LSTMNet(nn.Module):
    def __init__(self, input_dim, hidden_dim, n_layers, output_dim):
        super(LSTMNet, self).__init__()
        self.hidden_dim = hidden_dim
        self.n_layers = n_layers
        
        self.lstm = nn.LSTM(input_dim, hidden_dim, n_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
        self.relu = nn.ReLU()
        
    def forward(self, x):
        h0, c0 = self.init_hidden(x)
        out, (hn, cn) = self.lstm(x, (h0, c0))
        out = self.fc(self.relu(out[:, -1]))
        return out
    
    def init_hidden(self, x):
        h0 = torch.zeros(self.n_layers, x.size(0), self.hidden_dim)
        c0 = torch.zeros(self.n_layers, x.size(0), self.hidden_dim)
        return [t.cuda() for t in (h0, c0)]

class Fall_detector_LSTM():
    def __init__(self) -> None:
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange="FallDetectorLSTM", exchange_type="topic", auto_delete=True)
        self.channel.queue_declare(queue='FallDetectorLSTM_input_nparray', exclusive=True)
        self.channel.queue_bind(queue="FallDetectorLSTM_input_nparray", exchange="FallDetectorLSTM", routing_key=f"*.*.*.nparray")

        # load model
        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        input_dim = 3
        output_dim = 2
        n_layers = 2
        hidden_dim = 256
        self.model = LSTMNet(input_dim, hidden_dim, output_dim, n_layers).to(self.device)
        self.model.load_state_dict(torch.load('SmartFall_lstm.pth'))
        print("Load model successfully")

    def __callback(self, ch, method, properties, body):
        if "FallDetectorLSTM" in method.routing_key:
            pass
        else:
            routing_key_tokens = method.routing_key.split(".")
            app_name = routing_key_tokens[0]
            client_id = routing_key_tokens[1]

            # Write your service from here
            sensor_data_from_bytes = np.frombuffer(body, dtype=np.float64).reshape(-1,40,3)
            sensor_data_tensor = torch.tensor(sensor_data_from_bytes, dtype=torch.float)

            with torch.no_grad():
                output = self.model(sensor_data_tensor.to(self.device))
                pred = output.max(1, keepdim=True)[1]
                pred = pred.cpu().detach().numpy().flatten()
                print(f'Result: {app_name}.{client_id} {pred}')
                if pred:
                    print(f"Detect {app_name}.{client_id} FALL!")
                    self.channel.basic_publish(exchange="FallDetectorLSTM", 
                                               routing_key=f"{app_name}.{client_id}.FallDetectorLSTM.text",
                                               body=f"Detect {app_name}.{client_id} FALL!")

    def run(self):
        self.channel.basic_consume(queue='FallDetectorLSTM_input_nparray', on_message_callback=self.__callback, auto_ack=True)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

if __name__ == '__main__':
    try:
        detector = Fall_detector_LSTM()
        detector.run()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)