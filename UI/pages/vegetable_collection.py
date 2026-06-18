import streamlit as st 
import requests 
from datetime import date 
from key import URL

folder_path = "images/vegetables"

st.title("Vegetable Collection")

vegetable_name = st.text_input("Vegetable name")

if not vegetable_name:
    st.error("Please enter a vegetable name.")

vegetable_health = st.selectbox("vegetable health",["Healthy", "Not Healthy"])

today = date.today()

notes = st.text_area("Notes")

if "images" not in st.session_state:
    st.session_state.images = []


picture = st.camera_input("Live")

if picture:
    st.image(picture,caption= "Captured image")
    if picture and st.button("Add image"):
        st.session_state.images.append(picture)
        st.success("Image added")

st.write("Images captured so far:")

for image in st.session_state.images:
    st.image(image)

submit = st.button("Submit")



if submit:
    if len(st.session_state.images) == 0:
        st.error("Please add at least one image.")
    else:
        response = requests.post(
            f"{URL}/vegetables",
         json={
            "vegetable_name": vegetable_name,
            "vegetable_health": vegetable_health,
            "date": str(today),
            "notes": notes
            }
        )
    
        sample_id = response.json()["sample_id"]
  

        for i, image in enumerate(st.session_state.images):
            files = {
            "file": (f"image{i}.jpg", image.getvalue(), "image/jpeg")
            }
            data = {
            "sample_id":sample_id,
            "mode": "vegetables"
            }
            img_response = requests.post(
                f"{URL}/images",
                files=files,
                data=data
            )
        st.success(f"{len(st.session_state.images)} images uploaded")
        st.session_state.images = []
        st.rerun()