import streamlit as st 
from key import URL
import requests
from datetime import date 
import re 
import json 

category = st.session_state.category 
st.header(f"{category} Collection")

page = requests.get(f"{URL}/settings/{category}").json()

prompts = page["prompts"]

values = {}

for prompt in prompts:
    selection = prompt["selection"]

    match selection:
        case "Text Box":
            values[prompt["prompt"]] = st.text_input(prompt["prompt"])

        case "Text area (multi-line)":
            values[prompt["prompt"]] = st.text_area(prompt["prompt"])
        
        case "Number Input":
            values[prompt["prompt"]] = st.number_input(prompt["prompt"],min_value=prompt["min"], max_value=prompt["max"])
        
        case "Dropdown List":
            options = prompt["options"].split(",")
            values[prompt["prompt"]] = st.selectbox(prompt["prompt"],options=options)

        case "Radio Button":
            options = prompt["options"].split(",")
            values[prompt["prompt"]] = st.radio(prompt["prompt"],options=options)
        
        case "slider":
            values[prompt["prompt"]] = st.slider(prompt["prompt"], max_value=prompt["max"], min_value=prompt["min"])

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
    for prompt in prompts:
        if prompt.get("required") == "True":
            value = values[prompt["prompt"]]

            if isinstance(value, str) and not value.strip():
                st.write(f'{prompt["prompt"]} is required.')
                st.stop()   
        
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

            if not page["roboflow"] == "False":
                # REWIND THE FILE POINTER SO ROBOFLOW CAN READ IT
                image.seek(0)
                roboflow_settings = page["roboflow"]
                project_id = roboflow_settings["project_id"]
                roboflow_URL = f"https://api.roboflow.com/dataset/{project_id}/upload"

                image_information = {"sample_id": sample_id}
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


        st.rerun()           

if st.session_state.submitted:
    st.success("Submission Sucessful!")
    st.success(f"Sample ID: {st.session_state.sample_id}")

if st.session_state.robo_submission:
    st.success("RoboFlow Submission Successful")

