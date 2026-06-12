import streamlit as st

st.title("Soil Collection")

soil_button_1 = st.button("Collect Data")
soil_button_2 = st.button("View Data")

if soil_button_1:
    st.switch_page("pages/soil_collection.py")

if soil_button_2:
    st.switch_page("pages/view_data.py")