import streamlit as st
import requests
from key import URL
from datetime import datetime
import json 

user_obj = getattr(st, "user", None) or getattr(st, "experimental_user", None)
is_logged_in = user_obj and getattr(user_obj, "is_logged_in", False)

user_email = getattr(user_obj, "email", "")
user_name = getattr(user_obj, "name", "Unknown User")

st.markdown(
            f"<div style='text-align: right; font-size: 0.85rem; color: #374151;"
            f" line-height: 1.2;'><b>{user_name}</b><br><span"
            f" style='color: #6B7280; font-size: 0.75rem;'>{user_email}</span></div>",
            unsafe_allow_html=True,
        )
st.markdown("""
          <style>
          div[data-testid="top_logout_btn"] button {
              color: white ;              /* White text */
              border-radius: 12px ;       /* Rounded corners */
              border: 2px solid #3e8e41 ; /* Dark green border */
              font-size: 18px ;           /* Larger text */
              padding: 10px 24px ;        /* Custom spacing */
          }
          </style>
        """,
        unsafe_allow_html=True,)

cols = st.columns([8,1])
with cols[1]:
  if st.button("🚪 Logout", key="top_logout_btn"):
            for key in list(st.session_state.keys()):
              del st.session_state[key]
            st.logout()

if not is_logged_in:
  st.warning(
      "🔒 Please sign in with Google from the Home page to access the workspace."
  )
  st.stop()

st.title("View Collections")

categories = requests.get(f"{URL}/home").json()

if not categories:
   st.write("No Categories")
   st.stop()

selection = st.selectbox("Select Category:", categories)

st.divider()

samples_response = requests.get(f"{URL}/collection/samples/{selection}")

if samples_response.status_code != 200:
    st.error("Failed to load collection data.")
    st.stop()

samples = samples_response.json()

if not samples:
    st.info(f"No submissions found for {selection}.")
    st.stop()

st.header("Filter")

today = datetime.today().date()
date_range = st.date_input(
    "Select Date Range:",
    value=(today, today),
    max_value=today
)


for sample in samples:
    sample_id = sample["sample_id"]

    try:
        sample_date = datetime.strptime(sample["date"], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        sample_date = None 

    sample_information = sample["data"]

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        if sample_date and not (start_date <= sample_date <= end_date):
            continue  # Skip this sample if outside range

        with st.expander(f"Sample ID: {sample_id}, Date: {sample['date']}"):
            for question, answer in sample_information.items():
                st.write(f"**{question}:** {answer}")

            images_list = requests.get(f"{URL}/collection/images/{sample_id}").json()

                
            st.write("## Captured Images")
            
            columns = st.columns(3)
            for count, image in enumerate(images_list):
                image_id = image["image_id"]
                actual_image = requests.get(f"{URL}/collection/image/{image_id}")


                with columns[count % 3]:
                    st.image(actual_image.content,caption=f"Image ID: {image_id}",width="stretch")

                    st.download_button(
                        label="Download Image",
                        data=actual_image.content,
                        file_name=f"{selection}_{image_id}.jpg",
                        mime="image/jpeg",
                        key=f"btn_{image_id}"
                        )
 