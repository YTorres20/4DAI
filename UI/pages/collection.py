import streamlit as st 
from key import URL
import requests
from datetime import date 
import re 
import json 

# =========================================================================
# ACCESS CONTROL & ROLE CHECKING
# =========================================================================
user_obj = getattr(st, "user", None) or getattr(st, "experimental_user", None)
is_logged_in = user_obj and getattr(user_obj, "is_logged_in", False)

if not is_logged_in:
  st.warning(
      "🔒 Please sign in with Google from the Home page to access this"
      " collection workspace."
  )
  if st.button("⬅️ Return to Home"):
    st.switch_page("UI/home.py")
  st.stop()

# Fetch backend roles
try:
  roles = requests.get(f"{URL}/roles").json()
except Exception:
  roles = {}

user_email = getattr(user_obj, "email", "")

# Define individual role memberships
is_admin = user_email in roles.get("admin", [])
is_dev = user_email in roles.get("developer", [])
is_collector = user_email in roles.get("collector", [])

# ENFORCE ACCESS: Change this condition if you want to restrict to specific roles only
# Right now, it allows Admins, Developers, and Data Collectors.
if not (is_admin or is_dev or is_collector):
  st.error(
      f"⛔ Access Denied: Your email (**{user_email}**) is not authorized to"
      " access collection forms."
  )
  if st.button("🚪 Logout"):
    st.logout()
  st.stop()

category = st.session_state.category 
st.header(f"{category} Collection")

page = requests.get(f"{URL}/settings/{category}").json()

prompts = page["prompts"]

values = {}

for count, prompt in enumerate(prompts):
    selection = prompt["selection"]

    match selection:
        case "Text Box":
            values[prompt["prompt"]] = st.text_input(prompt["prompt"], key=f"input_{prompt['prompt']}{count}")

        case "Text Area (multi-line)":
            values[prompt["prompt"]] = st.text_area(prompt["prompt"], key=f"input_{prompt['prompt']}{count}")
        
        case "Number Input":
            values[prompt["prompt"]] = st.number_input(prompt["prompt"], min_value=prompt["min"], max_value=prompt["max"], key=f"input_{prompt['prompt']}{count}")
        
        case "Dropdown List":
            options = [opt.strip() for opt in prompt["options"].split(",")]
            values[prompt["prompt"]] = st.selectbox(prompt["prompt"], options=options, key=f"input_{prompt['prompt']}{count}")

        case "Radio Button":
            options = [opt.strip() for opt in prompt["options"].split(",")]
            values[prompt["prompt"]] = st.radio(prompt["prompt"], options=options, key=f"input_{prompt['prompt']}{count}")
        
        case "Slider": 
            values[prompt["prompt"]] = st.slider(prompt["prompt"], min_value=prompt["min"], max_value=prompt["max"], key=f"input_{prompt['prompt']}{count}")
        
use_camera = page["camera"]

if "images" not in st.session_state:
    st.session_state.images = []

# kinect camera should be here
picture = st.camera_input("LIVE")

if picture:
    st.image(picture, caption="Captured Image")
    if st.button("Add Image"):
        st.session_state.images.append(picture)
        st.success("Image added")

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "robo_submission" not in st.session_state:
    st.session_state.robo_submission = False 

if st.button("Submit"):
        
    today= date.today()
     

    if len(st.session_state.images) == 0:
        st.error("Please add at least one image!")
    else:
        response = requests.post(f"{URL}/collection/submission",
                                     json={
                                         "category": category,
                                         "date":str(today),
                                         "data": values 
                                        }
                                     ).json()
        
        sample_id = response["sample_id"]
        
        for image in st.session_state.images:
            image.seek(0)
            response = requests.post(f"{URL}/collection/images/upload",
                                     files = {
                                         "file": image
                                     },
                                     data = {
                                         "sample_id": sample_id,
                                         "category": category
                                     }
                                     )
            
            if response.status_code != 200:
                st.error("Image Upload Failed!")
                st.stop()

            image_id = response.json()["image_id"]
            st.session_state.submitted = True 
            st.session_state.sample_id = sample_id

            if not page["roboflow"] == False:
                # REWIND THE FILE POINTER SO ROBOFLOW CAN READ IT
                image.seek(0)
                roboflow_settings = page["roboflow"]
                project_id = roboflow_settings["project_id"]
                roboflow_URL = f"https://api.roboflow.com/dataset/{project_id}/upload"

               
                image_information.update(values)
                params = {
                    "api_key":roboflow_settings["api_key"],
                }  
                image_information = {"sample_id": str(sample_id)}
                
                for prompt_text, user_answer in values.items():
                    #  STRIP ALL SPECIAL CHARACTERS: Keeps only letters, numbers, and spaces
                    clean_key = re.sub(r'[^a-zA-Z0-9\s]', '', prompt_text)
                    # Replace spaces with clean underscores
                    clean_key = clean_key.strip().replace(" ", "_")
                    
                    image_information[clean_key] = str(user_answer)

                payload_data = {
                    "name": f"{category}:Image ID:{image_id}",
                    "metadata": json.dumps(image_information)
                }
                
                files ={
                    "file":image
                }

                roboflow_response = requests.post(roboflow_URL,params=params, files=files,data=payload_data)

                if roboflow_response.status_code == 200:
                    st.session_state.robo_submission = True 

        st.session_state.images = []
        st.rerun()           

if st.session_state.submitted:
    st.success("Submission Sucessful!")
    st.success(f"Sample ID: {st.session_state.sample_id}")

if st.session_state.robo_submission:
    st.success("RoboFlow Submission Successful")

