# uvicorn main:app --reload

from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
import uvicorn
import json
from app_controller import AppController
import traceback


api = FastAPI()
controller = AppController()

@api.get("/")
def read_root():
    return {"Hello": "World"}

@api.post("/apps")
async def create_app(file: UploadFile):
    try:
        cfg = json.load(file.file)
        result = controller.create_app(cfg)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    return result

@api.delete("/apps/{app_name}")
async def delete_app(app_name: str):
    try:
        controller.delete_app(app_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "OK"}

if __name__ == '__main__':
    uvicorn.run("main:api", reload=True)