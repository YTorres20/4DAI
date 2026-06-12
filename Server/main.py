from fastapi import FastAPI,UploadFile,File,Form 
from pydantic import BaseModel
from db import vegetable_collections, soil_collections, image_collections
import os 
import uuid

app = FastAPI()

class VegSample (BaseModel):
    vegetable_name : str 
    vegetable_health:str
    date:str 
    notes : str 

class SoilSample(BaseModel):
    soil_type:str
    soil_moisture:str
    date:str
    notes:str 


@app.post("/vegetables")
def create_vegetable(data:VegSample):
    sample_id = str(uuid.uuid4())
    vegetable_collections.insert_one({
        "_id": sample_id,
        "vegetable_name": data.vegetable_name,
        "vegetable_health": data.vegetable_health,
        "date": data.date,
        "notes":data.notes
    })
    return {"sample_id": sample_id}

@app.get("/data/{sample_id}")
def get_sample(sample_id:str):
    sample = vegetable_collections.find_one({
        "_id": sample_id
    })
    if sample is None:
        return {
            "error": "SAMPLE NOT FOUND!"
        }
    return {
        "id": sample["_id"],
        "vegetable_name": sample["vegetable_name"],
        "vegetable_health": sample ["vegetable_health"],
        "date": sample["date"],
        "notes":sample["notes"]

    }
@app.post("/images")
def upload_image(sample_id:str = Form(...), mode: str = Form(...), file:UploadFile = File(...)):
    if mode == "vegetable":
        folder_path = f"images/vegetables/{sample_id}"

    elif mode == "soil":
        folder_path = f"images/soils/{sample_id}"

    os.makedirs(folder_path,exist_ok=True)

    image_id = str(uuid.uuid4())
    file_path = f"{folder_path}/{image_id}.jpg"

    with open(file_path,"wb") as buffer:
        buffer.write(file.file.read())
    
    image_collections.insert_one({
        "_id":image_id,
        "sample_id":sample_id,
        "image_path": file_path
    })
    return {
        "image_id": image_id,
        "image_path": file_path
        
    }


@app.get("/data")
def get_all_data():
    vegetables = vegetable_collections.find()
    soils = soil_collections.find()

    return {
        "vegetables":[{
            "id": vegetable["_id"],
            "vegetable_name": vegetable ["vegetable_name"],
            "vegetable_health" : vegetable ["vegetable_health"],
            "date": vegetable["date"],
            "notes": vegetable ["notes"]
        } for vegetable in vegetables],

        "soils": [{
            "id": soil["_id"],
            "soil_type": soil["soil_type"],
            "soil_moisture": soil["soil_moisture"],
            "date": soil["date"],
            "notes": soil["notes"]

        }for soil in soils]
    }


@app.post("/soil")
def create_soil_sample(data:SoilSample):
    sample_id = str(uuid.uuid4())
    soil_collections.insert_one({
        "_id": sample_id,
        "soil_type": data.soil_type,
        "soil_moisture": data.soil_moisture,
        "date": data.date,
        "notes":data.notes
    })
    return {"sample_id": sample_id}
