from pymongo import MongoClient 

client = MongoClient("mongodb://localhost:27017")

db = client["Collections"]

vegetable_collections = db["vegetable"]
soil_collections = db["soil"]
image_collections = db["images"]

