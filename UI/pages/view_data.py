import streamlit as st
import requests
from key import URL

st.title("View Data")

response = requests.get(
    f"{URL}/data"
)

data = response.json()
vegetables = data["vegetables"]
soils = data["soils"]



for vegetable in vegetables:

    st.subheader(vegetable["vegetable_name"])

    st.write("Health:", vegetable["vegetable_health"])
    st.write("Date:", vegetable["date"])
    st.write("Notes:", vegetable["notes"])

    for image_id in vegetable["images"]:
        img_response = requests.get(f"{URL}/image/{image_id}")
        st.image(img_response.content)

    st.divider()

for soil in soils:

    st.subheader(soil["date"])
    
    st.write ("Soil type:", soil["soil_type"])
    st.write ("Moisture:", soil["soil_moisture"])
    st.write ("Notes:", soil["notes"])

    for image_id in soil["images"]:
        img_response = requests.get(f"{URL}/image/{image_id}")
        st.image(img_response.content)
    
    st.divider()


search = st.text_input("Search vegetable and soil collection date")

for vegetable in vegetables:

    if search.lower() in vegetable["vegetable_name"].lower():

        st.subheader(vegetable["vegetable_name"])

        st.write("Health:", vegetable["vegetable_health"])
        st.write("Date:", vegetable["date"])
        st.write("Notes:", vegetable["notes"])

        for image_id in vegetable["images"]:
            img_response = requests.get(f"{URL}/image/{image_id}")
            st.image(img_response.content)




        st.divider()

for soil in soils:

    if search.lower() in soil["date"].lower():

        st.subheader(soil["date"])

        st.write("Moisture:", soil["soil_moisture"])
        st.write("Date:", soil["date"])
        st.write("Notes:", soil["notes"])

        for image_id in soil["images"]:
            img_response = requests.get(f"{URL}/image/{image_id}")
            st.image(img_response.content)

        st.divider()