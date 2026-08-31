import streamlit as st 
import requests
from key import URL

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

try:
     roles = requests.get(f"{URL}/roles").json()
except Exception:
     roles = {}

is_admin = user_email in roles.get("admin",[])
is_dev = user_email in roles.get("developer",[])
is_collector = user_email in roles.get("collector",[])

st.title("Tutorials")

if is_admin:
     st.success("👑 **Administrator View:** You have full access to view and add videos.")
elif is_dev:
      st.success("🔬 **Developer View:** You have access to view and add videos.")
else:
      st.info("👀 **Viewer View:** Browse and watch available tutorials below.")

      
if is_dev or is_admin:
     with st.expander("🛠️ Add New Tutorial Video", expanded=False):
          with st.form("Add video form", clear_on_submit=True):
               video_title = st.text_input("Video Title:", placeholder= "e.g., How to submit data")
               video_url = st.text_input("Video URL:",placeholder="https://www.youtube.com/watch?v=...")
               video_description = st.text_area("Description:")
               st.write("Select audience for video:")
               developers = st.checkbox("Allow access to Developers")
               collector = st.checkbox("Allow access to Data Collector")
               guest = st.checkbox("Allow access to Guest")
               submit_btn = st.form_submit_button("Publish Video")

               if submit_btn:
                   if video_title.strip() and video_url.strip():
                       # Package up the payload including your audience rules
                       payload = {
                           "title": video_title,
                           "url": video_url,
                           "description": video_description,
                           "allow_developers": developers,
                           "allow_collector": collector, 
                           "allow_guest": guest,
                           "added_by": user_email
                       }
                       try:
                           res = requests.post(f"{URL}/tutorials", json=payload)
                           if res.status_code in [200, 201]:
                               st.success(f"Successfully published '{video_title}'!")
                               st.rerun()
                           else:
                               st.error("Failed to save video to the backend server.")
                       except Exception as e:
                           st.error(f"Connection error: {e}")
                   else:
                       st.error("Please provide both a title and a URL.")

try:
     tutorials_video = requests.get(f"{URL}/tutorials").json()
except Exception:
     tutorials_video = {}

if not tutorials_video:
     st.write("No videos available.")
     st.stop()

search_query = st.text_input(placeholder="Type Title or keywords related to the video...")


catalog = [cat for cat in tutorials_video if search_query.lower() in cat['title'].lower() or search_query.lower() in cat['description'].lower()] 


GRID_COLUMNS = 3
rows = [catalog[i:i+GRID_COLUMNS]for i in range(0,len(catalog),GRID_COLUMNS)]


def display_video(video:dict):
    with st.container(border=True):
        st.subheader(video.get("title","Untitled"))
        video_url = video.get("url")
        descrip = video.get("description", "No description available")
        added_by = video.get("added_by", "Not available")
        st.write(descrip)
        st.markdown(f"<span style='color: #6B7280; font-size: 0.75rem;'>Added by: {added_by}</span>", unsafe_allow_html=True)

        try:
            st.video(video_url)
        except Exception:
            st.markdown(f"[🔗 Watch Video]({video_url})")

for row in rows:
  cols = st.columns(GRID_COLUMNS)
  for index, video in enumerate(row):
      with cols[index]:
        if is_admin:
              display_video(video)
        elif is_dev and video.get("allow_developers"):
            display_video(video)
            
        elif is_collector and video.get("allow_collector"):
            display_video(video)
              
        elif not is_admin and not is_collector and not is_dev and video.get("allow_guests"):
            display_video(video)
          


      
       
            
            
            
            
     



     


     









    