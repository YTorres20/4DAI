from datetime import datetime
import requests
import streamlit as st
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
# ROLE-SPECIFIC DASHBOARD WIDGETS
# =========================================================================

if is_admin:
  with st.expander("👑 Admin Workspace Analytics", expanded=False):
    col_a, col_b = st.columns(2)
    with col_a:
      st.metric("System Role", "Administrator")
    with col_b:
      st.metric("System Status", "Healthy ✅")

if is_collector and not is_admin and not is_dev:
  st.info(
      "🎯 **Collector View:** You are generating a training script for your"
      " active data collection project. Ensure all field samples are fully"
      " uploaded before starting training."
  )

# =========================================================================
# MAIN SCRIPT GENERATOR

st.title("Generate Scripts")

if "lock_1" not in st.session_state:
  st.session_state.lock_1 = False

try:
  raw_categories = requests.get(f"{URL}/home").json()
except Exception:
  raw_categories = []

try:
  robo_settings = requests.get(f"{URL}/roboflow").json()
except Exception:
  robo_settings = []

# FILTER CATEGORIES: Only show categories that have actual roboflow settings available
valid_categories = []
for cat in raw_categories:
  try:
    cfg = requests.get(f"{URL}/settings/{cat}").json()
    if cfg.get("roboflow"):
      valid_categories.append(cat)
  except Exception:
    continue

if not valid_categories and not robo_settings:
  st.write("No RoboFlow settings exists")
  st.stop()

settings = valid_categories + robo_settings

selection = st.selectbox(
    "Select RoboFlow settings: ",
    settings,
    key="selection_key3",
    disabled=st.session_state.lock_1,
)

api_key = ""
workspace = ""
project_id = ""

if selection in valid_categories:
  try:
    configurations = requests.get(f"{URL}/settings/{selection}").json()
    roboflow_configurations = configurations.get("roboflow", {})
  except Exception:
    roboflow_configurations = {}

  api_key = roboflow_configurations.get("api_key", "")
  workspace = roboflow_configurations.get("workspace", "")
  project_id = roboflow_configurations.get("project_id", "")

elif selection in robo_settings:
  try:
    configurations = requests.get(f"{URL}/roboflow/{selection}").json()
  except Exception:
    configurations = {}

  api_key = configurations.get("api_key", "")
  workspace = configurations.get("workspace", "")
  project_id = configurations.get("project_id", "")

st.write(f"API key: {api_key}")
st.write(f"Workspace: {workspace}")
st.write(f"Project ID: {project_id}")

st.divider()
st.subheader("Model Configuration")

model_family = st.selectbox(
    "Model Family",
    ["yolo26", "yolo11", "yolov8"],
    disabled=st.session_state.lock_1,
)
model_size = st.selectbox(
    "Model Size",
    ["n (nano)", "s (small)", "m (medium)", "l (large)", "x (xlarge)"],
    disabled=st.session_state.lock_1,
)
epochs = st.number_input(
    "Epochs", min_value=1, max_value=300, value=50, disabled=st.session_state.lock_1
)

# Dataset Version Option (Latest vs Specific Version)
version_choice = st.radio(
    "Dataset Version Strategy",
    ["Always Use Latest Version", "Specify Version Number"],
    horizontal=True,
    disabled=st.session_state.lock_1,
)

target_version_code = "versions[-1].version.split('/')[-1]"
if version_choice == "Specify Version Number":
  custom_v_num = st.number_input(
      "Enter Version Number", min_value=1, value=1, disabled=st.session_state.lock_1
  )
  target_version_code = str(custom_v_num)

# Developer Advanced Hyperparameters
img_size = 640
patience_val = 50
learning_rate = 0.01

if is_dev:
  with st.expander("🔬 Developer Advanced Hyperparameters", expanded=False):
    img_size = st.selectbox(
        "Image Size (imgsz)",
        [640, 1024, 1280],
        index=0,
        disabled=st.session_state.lock_1,
    )
    patience_val = st.slider(
        "Early Stopping Patience",
        10,
        100,
        50,
        disabled=st.session_state.lock_1,
    )
    learning_rate = st.number_input(
        "Initial Learning Rate (lr0)",
        value=0.01,
        format="%.4f",
        disabled=st.session_state.lock_1,
    )

size_mapping = {
    "n (nano)": "n",
    "s (small)": "s",
    "m (medium)": "m",
    "l (large)": "l",
    "x (xlarge)": "x",
}
chosen_size = size_mapping[model_size]
model_filename = f"{model_family}{chosen_size}.pt"

if not st.session_state.lock_1:
  if st.button("Lock Configuration & Generate Script", type="primary"):
    if not api_key or not workspace or not project_id:
      st.error(
          "⚠️ Missing critical Roboflow credentials (API Key, Workspace, or"
          " Project ID). Please check your configuration."
      )
    else:
      st.session_state.lock_1 = True
      st.rerun()
else:
  if st.button("Unlock Configuration"):
    st.session_state.lock_1 = False
    st.rerun()

if st.session_state.lock_1:
  st.success("Configuration locked!")
  st.subheader("Google Colab Pro Training Code")
  st.write(
      "Copy and paste this into the first cell of your Google Colab Pro"
      " notebook:"
  )

  # Logic builder for version download line
  if version_choice == "Always Use Latest Version":
    version_script_block = f"""versions = project.versions()
if not versions:
    raise ValueError("No dataset versions found! Please generate a version in your Roboflow dashboard first.")
latest_v = {target_version_code}
print(f"Downloading latest dataset version: {{latest_v}}")
dataset = project.version(int(latest_v)).download("{model_family}")"""
  else:
    version_script_block = f"""target_v = {target_version_code}
print(f"Downloading dataset version: {{target_v}}")
dataset = project.version(int(target_v)).download("{model_family}")"""

  colab_script = f"""# =====================================================================
# Google Colab Pro Training Pipeline
# Generated automatically from RoboFlow Workspace
# =====================================================================

# 1. Install Roboflow and Ultralytics
!pip install -q roboflow ultralytics

# 2. Download dataset version from your Roboflow project
from roboflow import Roboflow
from ultralytics import YOLO

rf = Roboflow(api_key="{api_key}")
project = rf.workspace("{workspace}").project("{project_id}")

{version_script_block}

# 3. Train using Colab Pro GPU
model = YOLO("{model_filename}")
model.train(
    data=f"{{dataset.location}}/data.yaml",
    epochs={epochs},
    imgsz={img_size},
    batch=16,
    patience={patience_val},
    lr0={learning_rate}
)
"""

  st.code(colab_script, language="python")

  st.download_button(
      label="📥 Download Training Script (.py)",
      data=colab_script,
      file_name=f"train_{project_id}_{model_family}.py",
      mime="text/plain",
      use_container_width=True,
  )