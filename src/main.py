# uvicorn main:app --reload

from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
import uvicorn
import json
from app_controller import AppController


api = FastAPI()
controller = AppController()

@api.get("/")
def read_root():
    return {"Hello": "World"}

@api.post("/app")
def create_app(file: UploadFile):
    try:
        cfg = json.load(file.file)
        result = controller.create_app(cfg)
        with open("./config/result.json", "w") as f:
            json_object = json.dumps(cfg, indent=4)
            f.write(json_object)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    return result

if __name__ == '__main__':
    uvicorn.run("main:api", reload=True)