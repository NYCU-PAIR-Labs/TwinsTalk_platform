import requests, json

class TopolgyValidator():
    def __init__(self, host="140.113.193.10:15672", user="guest", password="guest") -> None:
        self.host = host
        self.user = user
        self.password = password

    def validate_cfg(self, json_file:str) -> bool:
        with open(json_file) as f:
            cfg = json.load(f)

        central_queues = self.get_queues_name()
        server_outputs = self.get_exchange_outputs()
        input_queues = [input_queue["queue"] for input_queue in cfg["input"]]
        output_queues = [output_queue["queue"] for output_queue in cfg["output"]]

        # Validate output part
        for output in cfg["output"]:
            if output["queue"] in central_queues:
                raise Exception(f"[{output}] is already exist in central broker!")

        # Validate topology part 
        for link in cfg["topology"]:
            if link["source"]["type"] != "input" and link["source"]["type"] != "server":
                raise Exception(f"[{link['source']['queue']}] Source can only be input or server")
            # Check input queue is correct
            if link["source"]["type"] == "input":
                src_queue = link["source"]["queue"]
                if src_queue not in input_queues:
                    raise Exception(f"[{src_queue}] doesn't declare in input, please check this queue in input part.")
                
                for dst_queue in link["destination"]:
                    if dst_queue["type"] != "server":
                        raise Exception(f"[{dst_queue['queue']}] Input queue can only route to server_input_queue, please check type.")
                    if dst_queue["queue"] not in central_queues:
                        raise Exception(f"[{dst_queue['queue']}] doesn't exist, please check this queue in central broker.")

            if link["source"]["type"] == "server":
                src_queue = link["source"]["queue"]
                if src_queue not in server_outputs:
                    raise Exception(f"[{src_queue}] doesn't exist in server exchange output.")

                for dst_queue in link["destination"]:
                    if dst_queue["type"] == "server" and dst_queue["queue"] not in central_queues:
                        raise Exception(f"[{dst_queue['queue']}] doesn't exist, please check this queue in central broker.")
                    if dst_queue["type"] == "output" and dst_queue["queue"] not in output_queues:
                        raise Exception(f"[{dst_queue['queue']}] doesn't declare in output, please check this queue in output part.")
                    if dst_queue["type"] != "server" and dst_queue["type"] != "output":
                        raise Exception(f"[{dst_queue['queue']}] Server output can only route to server_input_queue or app_output_queue.")

    def get_exchange_outputs(self) -> list:
        api = "/api/exchanges"
        response = requests.get(f"http://{self.host}{api}", auth=(self.user, self.password))
        exchange_outputs = []
        if response.status_code == 200:
            for exchange in response.json():
                if exchange["arguments"]:
                    exchange_outputs += exchange["arguments"]["output"]
            return exchange_outputs
        else:
            raise Exception("Server status code:", response.status_code)

    def get_queues_name(self) -> list:
        api = "/api/queues"
        response = requests.get(f"http://{self.host}{api}", auth=(self.user, self.password))
        if response.status_code == 200:
            return [queue["name"] for queue in response.json()]
        else:
            raise Exception("Server status code:", response.status_code)


if __name__ == "__main__":
    validator = TopolgyValidator()
    validator.validate_cfg("app1.json")