from fastapi import FastAPI,UploadFile, File, Form 
from fastapi.responses import FileResponse
from pymongo import MongoClient 
import os 
import uuid
import json 

app = FastAPI()

client = MongoClient("mongodb://localhost:27017")
db = client["Collections"]
settings_folder = "settings"
os.makedirs(settings_folder,exist_ok=True)
roboflow_folder = "roboflow_settings"
os.makedirs(roboflow_folder, exist_ok=True)

@app.post("/collection/submission")
def submission(submission:dict):
    category = submission["category"].lower()
    table = db[category]
    sample_id = str(uuid.uuid4())
    
    table.insert_one({
        "_id": sample_id,
        "date" : submission["date"],
        "data": submission["data"]
    })
    return {"sample_id": sample_id}

@app.post("/collection/images/upload")
def upload_image(sample_id: str = Form(...), category:str = Form(...), file:UploadFile = File(...)):
    image_folder = f"images/{category}/{sample_id}"
    os.makedirs(image_folder,exist_ok=True)

    image_id = str(uuid.uuid4())

    image_file = f"{image_folder}/{image_id}.jpg"
    
    with open(image_file,"wb") as infile:
        infile.write(file.file.read())
    
    image_table = db["images"]
    
    image_table.insert_one({
        "_id": image_id,
        "sample_id":sample_id,
        "image_path": image_file

    })
    return {"image_id":image_id, "image_path":image_file}


@app.get("/collection/samples/{selection}")
def get_samples(selection:str):
    table = db[selection.lower()]
   
    cursor = table.find({})
    
    samples = []
    for doc in cursor:
        samples.append({
            "sample_id": doc["_id"],  # 
            "date": doc["date"],
            "data": doc["data"]
        })
    return samples

@app.get("/settings/{category}")
def get_collections_configuration(category:str):
    with open(f"{settings_folder}/{category}.json") as infile:
        settings = json.load(infile)
    return settings 

@app.get("/home")
def home_configuration():
    categories = []

    for file_name in os.listdir(settings_folder):
        categories.append(file_name.removesuffix(".json"))

    return categories

@app.get("/collection/image/{image_id}")
def get_image(image_id:str):
  image_collections = db["images"]
  image = image_collections.find_one({
      "_id": image_id
  })

  if image is None or not os.path.exists(image["image_path"]):
    return {"error": "IMAGE NOT FOUND"}
  
  return FileResponse(path=image["image_path"])

@app.get("/collection/images/{sample_id}")
def get_list_sample_images(sample_id: str):
    image_table = db["images"]
    cursor = image_table.find({"sample_id": sample_id})
    
    images = []
    for doc in cursor:
        images.append({
            "image_id": doc["_id"],  # Maps to your "_id": image_id storage scheme
            "sample_id": doc["sample_id"]
        })
    return images

@app.post("/settings")
def create_page_configuration(page:dict):
    category = page["category"]
    folder_path = "settings/"

    os.makedirs(folder_path,exist_ok=True)
    file_path = f"{folder_path}/{category}.json"

    with open(file_path,"w") as infile:
        json.dump(page,infile,indent=4)

    return {"message": "saved", "file": file_path}

@app.post("/roboflow")
def create_roboflow_home_configuration(roboflow:dict):
    setting_name = roboflow["name"]

    with open(f"{roboflow_folder}/{setting_name}.json", "w") as infile:
        json.dump(roboflow,infile,indent=4)

    return{"message":"saved"}

@app.get("/roboflow")
def get_roboflow_configuration():
    roboflow_settings = []

    for file_name in os.listdir(roboflow_folder):
        roboflow_settings.append(file_name.removesuffix(".json"))

    return roboflow_settings

@app.get("/roboflow/{selection}")
def get_roboflow_configuration(selection:str):
    
    with open(f"{roboflow_folder}/{selection}.json") as infile:
        roboflow_settings = json.load(infile)
    return roboflow_settings