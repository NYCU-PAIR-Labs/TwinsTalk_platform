import docker
from validator import TopolgyValidator
import json, os, socket

class AppController():
    def __init__(self) -> None:
        self.docker_client = docker.from_env()
        self.validator = TopolgyValidator()

    def create_app(self, cfg: dict) -> dict[str: str]:
        name = cfg["name"]
        # Check and validate app
        if self.get_container(name):
            raise Exception("The app is already existed.")
        self.validator.validate_cfg(cfg)

        print(f"[Info] Start to create {name} container and {name} broker container")
        app_broker_managerment_port = cfg["app_broker"]["management_port"]
        app_broker_conneciotn_port = cfg["app_broker"]["connection_port"]
        cfg_path = os.getcwd()+"/config/"+name+".json"

        app_broker_container = self.docker_client.containers.run(
            "rabbitmq:management", 
            name=f"{name}_broker", 
            detach=True,
            auto_remove=True, 
            ports={15672: app_broker_managerment_port, 5672: app_broker_conneciotn_port})

        for line in app_broker_container.logs(stream=True):
            log = line.decode()
            if "Server startup complete" in log:
                print("Create app broker successfully.")
                break

        app_container = self.docker_client.containers.run(
            "my-app", 
            name=name, 
            detach=True, 
            auto_remove=True,
            volumes={cfg_path: {'bind': '/usr/src/app/app_cfg.json', 'mode': 'ro'}})

        return {"status": "Build App successfully."}

    # return true if container exist, otherwise return false
    def get_container(self, container_name) -> bool:
        try:
            self.docker_client.containers.get(container_name)
        except docker.errors.NotFound:
            return False
        return True

    def delete_app(self, app_name):
        print(f"Delete {app_name} container and broker.")
        try:
            app_container = self.docker_client.containers.get(app_name)
            app_broker_container = self.docker_client.containers.get(f"{app_name}_broker")
            app_container.kill(signal="SIGINT")
            app_broker_container.stop()
        except docker.errors.NotFound:
            raise Exception(f"[{app_name}] doesn't exist")


if __name__ == "__main__":
    controller = AppController()
    with open("./config/app1.json") as f:
        cfg = json.load(f)

    result = controller.create_app(cfg)
    print(result)
    

# rabbitmq_container = client.containers.run("rabbitmq:management", detach=True, auto_remove=True, ports={15672:15672, 5672:5672})
# rabbitmq_container.stop()

'''
docker run -it --rm -v "$PWD/app1.json":/usr/src/app/app_cfg.json my-app
docker run -d --rm -v "$PWD/app1.json":/usr/src/app/app_cfg.json --name app1 my-app
docker kill -s SIGINT <containerID>

'''