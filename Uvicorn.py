from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson.json_util import dumps
import os
import json

app = FastAPI()

# Allow Flutter and any other clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📦 MongoDB Atlas connection
client = MongoClient("mongodb+srv://egg_user:pass_should_!_be_shared_fr@egg0.tzjyvga.mongodb.net/?appName=Egg0")
db = client["EggDB"]
eggs_collection = db["eggs"]

# 📁 Path for serving egg images
EGG_FOLDER = "/home/group4PI/Documents/eggs"
app.mount("/images", StaticFiles(directory=EGG_FOLDER), name="images")

@app.get("/")
def root():
    return {"message": "🥚 Egg API connected to MongoDB successfully!"}

# 🧩 GET all egg data
@app.get("/eggs")
def get_eggs():
    eggs = list(eggs_collection.find({}, {"_id": 0}))  # remove internal Mongo ID
    return {"eggs": eggs}

# 🆕 POST new egg data (optional for when your detection script runs)
@app.post("/eggs")
def add_egg(egg: dict):
    """
    Example egg object:
    {
        "timestamp": "2025-10-20 15:26:32",
        "label": "AA - Premium",
        "confidence": 0.39,
        "size": "Large",
        "diagonal pixels": 503.04,
        "image_path": "/home/group4PI/Documents/eggs/20251020_152632 AA - Premium Large.jpg"
    }
    """
    eggs_collection.insert_one(egg)
    return {"message": "Egg data saved successfully!"}

# 🧹 DELETE all eggs (for testing only)
@app.delete("/eggs/clear")
def clear_eggs():
    eggs_collection.delete_many({})
    return {"message": "All egg data cleared."}
  