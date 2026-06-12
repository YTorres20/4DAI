import streamlit as st 
import requests 

st.title("Vegetable & Moisture Monitoring System")
st.markdown("### Welcome to vegetable and moisture monitoring system")
st.write("""
        Use the side bar to navigate between:
         - Vegetable Collection
         - Soil Collection 
         """)


col1,col2  = st.columns(2)

with col1:
   veg_button = st.button("Vegetable Collection")
   if veg_button:
      st.switch_page("pages/vegetable.py")
with col2:
   soil_button = st.button("Soil Collection")
   if soil_button:
      st.switch_page("pages/soil.py")
   