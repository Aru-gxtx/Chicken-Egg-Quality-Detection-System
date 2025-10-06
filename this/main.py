from fastapi import FastAPI, UploadFile, Form
from pymongo import MongoClient
import shutil

app = FastAPI()

# Connect MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["egg_database"]
collection = db["eggs"]

@app.post("/egg")
async def upload_egg(image: UploadFile, size: str = Form(...), grade: str = Form(...)):
    # Save image
    with open(f"images/{image.filename}", "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    # Save to DB
    record = {
        "image": image.filename,
        "size": size,
        "grade": grade
    }
    collection.insert_one(record)
    return {"message": "Egg data saved!"}

@app.get("/eggs")
def get_eggs():
    eggs = list(collection.find({}, {"_id": 0}))
    return {"eggs": eggs}
