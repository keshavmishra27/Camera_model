
from fastapi import FastAPI
from logic import process_frame

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Face Brightness Controller Running"}

@app.get("/check-faces")
def check_faces():
    result = process_frame()
    return resultfrom logic 

