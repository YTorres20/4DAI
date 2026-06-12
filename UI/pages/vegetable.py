import streamlit as st

st.title("Vegetable Collection")

veg_button_1 = st.button("Collect Data")
veg_button_2 = st.button ("View Data")

if veg_button_1:
    st.switch_page("pages/vegetable_collection.py")

if veg_button_2:
    st.switch_page("pages/view_data.py")