from datetime import datetime
import requests
import streamlit as st
from key import URL
import json
import os 
# =========================================================================
# ACCESS CONTROL & ROLE VERIFICATION
# =========================================================================
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


# Fetch backend roles
try:
  roles = requests.get(f"{URL}/roles").json()
except Exception:
  roles = {}

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
tabs = st.tabs(["Welcome To Colab","Generate Scipts"])

with tabs[0]:
    st.subheader("📓 Welcome to Colab!")
    folder_path = "pages/ColabFiles"  
    files_to_display = [file.removesuffix(".ipynb") for file in os.listdir(folder_path)]

    in_tabs = st.tabs(files_to_display)

    for index,file in enumerate(files_to_display):
      file_path = f"{folder_path}/{file}.ipynb"
      with in_tabs[index]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                notebook = json.load(f)

            # Loop through and render cells while ignoring base64 garbage strings
            for i, cell in enumerate(notebook.get("cells", [])):
                cell_type = cell.get("cell_type")
                
                if cell_type == "markdown":
                    source_lines = cell.get("source", [])
                    # Filter out lines that look like base64 image data
                    clean_lines = [
                        line for line in source_lines 
                        if "data:image" not in line and "base64" not in line
                    ]
                    text_content = "".join(clean_lines)
                    if text_content.strip():
                        st.markdown(text_content)
                        
                elif cell_type == "code":
                    code_text = "".join(cell.get("source", []))
                    if code_text.strip():
                        st.code(code_text, language="python")
                        
        except FileNotFoundError:
            st.error(f"Could not find the notebook file at `{file_path}`.")

    

with tabs[1]:
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
    
    # Google Account Switcher / Login Helper for Team Members
    st.markdown(
        "🔑 **Using Colab Pro?** Make sure you are signed into the correct"
        " research account before opening notebooks: "
        "[Switch / Login to Google Account](https://accounts.google.com/AccountChooser)"
    )
    
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