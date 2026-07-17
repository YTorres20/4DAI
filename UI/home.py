import streamlit as st
import requests
from key import URL 

# =========================================================================
# 1. MAIN DASHBOARD CONTENT VIEW
# =========================================================================

def show_home_dashboard():
    st.session_state.category = None
    st.title("Collections")
    st.write("Pick a Collection")

    FIXED_COL = 6 

    categories = requests.get(f"{URL}/home").json()
    if not categories:
       st.write("No Categories")
       st.stop()

    categories.sort()

    columns = st.columns(FIXED_COL)
    count = len(categories)

    for i in range(count):
       with columns[i % FIXED_COL]:
          if st.button(f"{categories[i]}", key=categories[i]):
             st.session_state.category = categories[i]
             st.switch_page(collection_page)

# =========================================================================
# 2. APP NAVIGATION ROUTER
# =========================================================================


# Passes the function directly to break the recursion loop!
home_page = st.Page(show_home_dashboard, title="Home", icon="🏠", default=True)

collection_page = st.Page("pages/collection.py", title="Collection Form", visibility="hidden")
view_data_page = st.Page("pages/view_data.py", title="View Collections", icon="📊")
settings_page = st.Page("pages/settings.py", title="Settings Manager", icon="⚙️")
roboflow = st.Page("pages/roboflow.py", title= "RoboFlow", icon="🎯")
google_collab = st.Page("pages/googleCollab.py", title= "Google Collab",icon="🚀")

# Render sidebar navigation tree
pg = st.navigation([home_page, view_data_page, settings_page,collection_page,roboflow,google_collab])
pg.run()