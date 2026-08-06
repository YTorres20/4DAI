import streamlit as st
import requests 
from key import URL

# =========================================================================
# ACCESS CONTROL & ROLE VERIFICATION
# =========================================================================
user_obj = getattr(st, "user", None) or getattr(st, "experimental_user", None)
is_logged_in = user_obj and getattr(user_obj, "is_logged_in", False)

if not is_logged_in:
  st.warning(
      "🔒 Please sign in with Google from the Home page to access this script"
      " generator."
  )
  st.stop()

# Fetch backend roles
try:
  roles = requests.get(f"{URL}/roles").json()
except Exception:
  roles = {}

user_email = getattr(user_obj, "email", "")
is_admin = user_email in roles.get("admin", [])
is_dev = user_email in roles.get("developer", [])
is_collector = user_email in roles.get("collector", [])

# ENFORCE ACCESS: Restrict script generation to authorized roles
if not (is_admin or is_dev or is_collector):
  st.error(
      f"⛔ Access Denied: Your email (**{user_email}**) is not authorized to"
      " access Google Collab script generation."
  )
  st.stop()

# =========================================================================
# MAIN SCRIPT GENERATOR

st.title("Generate Scripts")

if "lock_1" not in st.session_state:
    st.session_state.lock_1 = False 

category_settings = requests.get(f"{URL}/home").json()
robo_settings = requests.get(f"{URL}/roboflow").json()

if not category_settings and not robo_settings:
    st.write("No RoboFlow settings exists")
    st.stop()

settings = category_settings + robo_settings

selection = st.selectbox("Select RoboFlow settings: ", settings, key="selection_key3", disabled=st.session_state.lock_1)

api_key = ""
workspace = ""
project_id = ""

if selection in category_settings:
    configurations = requests.get(f"{URL}/settings/{selection}").json()
    roboflow_configurations = configurations["roboflow"]

    if not roboflow_configurations:
        st.write("No Robflow configurations are available")
        st.stop()
    else:
        api_key = roboflow_configurations["api_key"]
        workspace = roboflow_configurations["workspace"]
        project_id = roboflow_configurations["project_id"]

elif selection in robo_settings:
    configurations = requests.get(f"{URL}/roboflow/{selection}").json()

    api_key = configurations["api_key"]
    workspace = configurations["workspace"]
    project_id = configurations["project_id"]

st.write(f"API key: {api_key}")
st.write (f"Workspace: {workspace}")
st.write (f"Project ID: {project_id}")

st.divider()
st.subheader("Model Configuration")

model_family = st.selectbox("Model Family", ["yolo26", "yolo11", "yolov8"], disabled=st.session_state.lock_1)
model_size = st.selectbox("Model Size", ["n (nano)", "s (small)", "m (medium)", "l (large)", "x (xlarge)"], disabled=st.session_state.lock_1)
epochs = st.number_input("Epochs", min_value=1, max_value=300, value=50, disabled=st.session_state.lock_1)

size_mapping = {"n (nano)": "n", "s (small)": "s", "m (medium)": "m", "l (large)": "l", "x (xlarge)": "x"}
chosen_size = size_mapping[model_size]
model_filename = f"{model_family}{chosen_size}.pt"

if not st.session_state.lock_1:
    if st.button("Lock Configuration & Generate Script"):
        st.session_state.lock_1 = True 
        st.rerun()

if st.session_state.lock_1:
    st.success("Configuration locked!")
    st.subheader("Google Colab Pro Training Code")
    st.write("Copy and paste this into the first cell of your Google Colab Pro notebook:")

    colab_script = f"""
    # 1. Install Roboflow and Ultralytics
    !pip install -q roboflow ultralytics

    # 2. Download the latest dataset version from your Roboflow project
    from roboflow import Roboflow
    from ultralytics import YOLO

    rf = Roboflow(api_key="{api_key}")
    project = rf.workspace("{workspace}").project("{project_id}")

    versions = project.versions()
    if not versions:
        raise ValueError("No dataset versions found! Please generate a version in your Roboflow dashboard first.")

    latest_v = versions[-1].version.split("/")[-1]
    print(f"Downloading latest dataset version: {{latest_v}}")
    dataset = project.version(int(latest_v)).download("{model_family}")

    # 3. Train using Colab Pro GPU
    model = YOLO("{model_filename}")
    model.train(
        data=f"{{dataset.location}}/data.yaml",
        epochs={epochs},
        imgsz=640,
        batch=16
)
"""
        
    st.code(colab_script, language="python")



