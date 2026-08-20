from datetime import datetime
import json
import os
import uuid
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse
from pymongo import MongoClient

# =========================================================================
# APPLICATION SETUP & CONFIGURATION
# =========================================================================
app = FastAPI()

# MongoDB connection and database initialization
client = MongoClient("mongodb://localhost:27017")
db = client["Collections"]

# Local storage directories
settings_folder = "settings"
os.makedirs(settings_folder, exist_ok=True)
roboflow_folder = "roboflow_settings"
os.makedirs(roboflow_folder, exist_ok=True)


# =========================================================================
# DATA COLLECTION & SUBMISSION ENDPOINTS
# =========================================================================


@app.post("/collection/submission")
def submission(submission: dict):
  """Submits a new data sample entry into the specified category collection."""
  category = submission["category"].lower()
  table = db[category]
  sample_id = str(uuid.uuid4())

  table.insert_one(
      {
          "_id": sample_id,
          "date": submission["date"],
          "data": submission["data"],
      }
  )
  return {"sample_id": sample_id}


@app.post("/collection/images/upload")
def upload_image(
    sample_id: str = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...),
):
  """Uploads and stores an image linked to a specific collection sample."""
  image_folder = f"images/{category}/{sample_id}"
  os.makedirs(image_folder, exist_ok=True)

  image_id = str(uuid.uuid4())
  image_file = f"{image_folder}/{image_id}.jpg"

  with open(image_file, "wb") as infile:
    infile.write(file.file.read())

  image_table = db["images"]
  image_table.insert_one(
      {"_id": image_id, "sample_id": sample_id, "image_path": image_file}
  )
  return {"image_id": image_id, "image_path": image_file}


@app.get("/collection/samples/{selection}")
def get_samples(selection: str):
  """Retrieves all stored sample records for a given category."""
  table = db[selection.lower()]
  cursor = table.find({})

  samples = []
  for doc in cursor:
    samples.append(
        {"sample_id": doc["_id"], "date": doc["date"], "data": doc["data"]}
    )
  return samples


@app.get("/collection/image/{image_id}")
def get_image(image_id: str):
  """Fetches and streams a stored image file by its ID."""
  image_collections = db["images"]
  image = image_collections.find_one({"_id": image_id})

  if image is None or not os.path.exists(image["image_path"]):
    return {"error": "IMAGE NOT FOUND"}

  return FileResponse(path=image["image_path"])


@app.get("/collection/images/{sample_id}")
def get_list_sample_images(sample_id: str):
  """Retrieves a list of image metadata associated with a sample ID."""
  image_table = db["images"]
  cursor = image_table.find({"sample_id": sample_id})

  images = []
  for doc in cursor:
    images.append({"image_id": doc["_id"], "sample_id": doc["sample_id"]})
  return images


# =========================================================================
# CATEGORY & SETTINGS CONFIGURATION ENDPOINTS
# =========================================================================


@app.get("/settings/{category}")
def get_collections_configuration(category: str):
  """Loads form prompts and field specifications for a given category."""
  with open(f"{settings_folder}/{category}.json") as infile:
    settings = json.load(infile)
  return settings


@app.get("/home")
def home_configuration():
  """Lists all available category names configured in the system."""
  categories = []
  for file_name in os.listdir(settings_folder):
    categories.append(file_name.removesuffix(".json"))
  return categories


@app.post("/settings")
def create_page_configuration(page: dict):
  """Saves or updates category form configurations and logs the action."""
  category = page["category"]
  folder_path = "settings/"

  os.makedirs(folder_path, exist_ok=True)
  file_path = f"{folder_path}/{category}.json"

  with open(file_path, "w") as infile:
    json.dump(page, infile, indent=4)

  return {"message": "saved", "file": file_path}


# =========================================================================
# ROBOFLOW INTEGRATION CONFIGURATION ENDPOINTS
# =========================================================================


@app.post("/roboflow")
def create_roboflow_home_configuration(roboflow: dict):
  """Saves Roboflow workspace integration settings."""
  setting_name = roboflow["name"]

  with open(f"{roboflow_folder}/{setting_name}.json", "w") as infile:
    json.dump(roboflow, infile, indent=4)

  return {"message": "saved"}


@app.get("/roboflow")
def get_roboflow_configuration():
  """Lists all saved Roboflow configuration profiles."""
  roboflow_settings = []
  for file_name in os.listdir(roboflow_folder):
    roboflow_settings.append(file_name.removesuffix(".json"))
  return roboflow_settings


@app.get("/roboflow/{selection}")
def get_roboflow_configuration(selection: str):
  """Loads details for a specific Roboflow configuration profile."""
  with open(f"{roboflow_folder}/{selection}.json") as infile:
    roboflow_settings = json.load(infile)
  return roboflow_settings


# =========================================================================
# USER ROLES & ACCESS REQUEST MANAGEMENT ENDPOINTS
# =========================================================================


@app.get("/roles")
def get_roles():
  """Retrieves all user role assignments from storage."""
  with open("roles.json") as infile:
    roles = json.load(infile)
  return roles


@app.post("/request")
def request(request: dict):
  """Submits a new access/role request and logs the event."""
  with open("requests.json", "a+") as infile:
    infile.seek(0)
    try:
      request_data = json.load(infile)
    except json.JSONDecodeError:
      request_data = []

  if not request_data:
    request_data = []

  request_data.append(request)
  with open("requests.json", "w") as infile:
    json.dump(request_data, infile, indent=4)

  return {"message": "saved"}


@app.get("/requests")
def get_requests():
  """Retrieves all pending access requests."""
  with open("requests.json", "a+") as infile:
    infile.seek(0)
    requests = json.load(infile)
  return requests


@app.post("/roles/assign")
def assign_roles(new_person: dict):
  """Assigns a user to a specific system role and logs the update."""
  with open("roles.json", "r") as infile:
    roles_data = json.load(infile)

  new_email = new_person["email"]
  new_role = new_person["role"]

  if new_email not in roles_data[new_role]:
    roles_data[new_role].append(new_email)

  with open("roles.json", "w") as infile:
    json.dump(roles_data, infile, indent=4)

  return {"status": "success"}


@app.delete("/requests/remove")
def remove_request(payload: dict):
  """Dismisses or removes a pending access request."""
  target_email = payload.get("email")

  with open("requests.json", "r") as infile:
    requests_list = json.load(infile)

  requests_list = [
      request for request in requests_list if request["email"] != target_email
  ]

  with open("requests.json", "w") as infile:
    json.dump(requests_list, infile, indent=4)

  return {"status": "success"}


@app.delete("/roles/remove")
def remove_role_assignment(payload: dict):
  """Removes a user from a specific role assignment."""
  target_email = payload.get("email")
  target_role = payload.get("role")

  with open("roles.json", "r") as infile:
    roles_data = json.load(infile)

  if target_role in roles_data and target_email in roles_data[target_role]:
    roles_data[target_role].remove(target_email)

    with open("roles.json", "w") as infile:
      json.dump(roles_data, infile, indent=4)

    return {"status": "success"}

  return {"status": "error", "message": "Role or email not found"}


# =========================================================================
# SYSTEM UTILITY ENDPOINTS
# =========================================================================


@app.get("/system/routes")
def get_all_routes():
  """Returns a sorted list of all active API routes registered on the server."""
  routes = []
  for route in app.routes:
    if hasattr(route, "path") and route.path not in [
        "/openapi.json",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
    ]:
      routes.append(route.path)
  return sorted(list(set(routes)))