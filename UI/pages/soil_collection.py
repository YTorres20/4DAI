import streamlit as st 
import requests 
from datetime import date 
from key import URL 

st.title("Soil Collection")

soil_type = st.text_input("Soil type",key="Soil_type")

if not soil_type:
    st.error("Please enter soil type.")

soil_moisture = st.selectbox("Soil moisture",["1","2","3","4","5","6","7","8","9","10"], key="soil_moisture")

today = date.today()

notes = st.text_area("Notes", key= "Notes")

if "images" not in st.session_state:
    st.session_state.images = []

picture = st.camera_input("Live",key="camera")

if picture:
    st.image(picture, caption="Captured image")
    
if picture and st.button("Add image"):
    st.session_state.images.append(picture)
    st.success("Image added")

st.write ("Images captured so far:")

for image in st.session_state.images:
    st.image(image)

submit = st.button("Submit")

if submit:
    if len(st.session_state.images) == 0:
        st.error("Please add at least one image.")
    else:
        response = requests.post(
           f"{URL}/soil",
           json={
               "soil_type": soil_type,
               "soil_moisture": soil_moisture,
               "date": str(today),
               "notes": notes
           })
        sample_id = response.json()["sample_id"]

        for i, image in enumerate(st.session_state.images):
            files = {
                "file": (f"image{i}.jpg", image.getvalue(),"image/jpeg")
            }
            data = {
                "sample_id": sample_id,
                "mode": "soil"
            }
            img_response = requests.post(
                f"{URL}/images",
                files = files,
                data=data
            )
        st.success(f"{len(st.session_state.images)} images uploaded")
        st.session_state.images = []
    
        st.rerun()