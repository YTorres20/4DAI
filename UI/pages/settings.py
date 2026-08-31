from datetime import datetime
import json
import re
import time
from key import URL
import requests
import streamlit as st

# =========================================================================
# ACCESS CONTROL & ADMIN/DEVELOPER ROLE VERIFICATION
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

# ENFORCE ACCESS: Allow both Admins and Developers to access settings
if not (is_admin or is_dev):
  st.error(
      f"⛔ Access Denied: Your email (**{user_email}**) is not authorized to"
      " view the settings panel."
  )
  st.stop()

# =========================================================================
# ROLE-BASED HEADER NOTICE
# =========================================================================
if is_admin:
  st.success(
      "👑 **Administrator View:** You have full access to category management"
      " and user role administration."
  )
elif is_dev:
  st.info(
      "🔬 **Developer View:** You have access to category management and field"
      " configuration. (User role assignments are restricted to administrators)."
  )

# =========================================================================
# MAIN SETTINGS MANAGER
# =========================================================================

st.title("Settings")
st.divider()
st.subheader("Add New Category")

with st.expander("📖 Instructions: How to Create a Category", expanded=True):
  st.markdown("""
    Welcome to the **Category Creator**. Follow these steps to build a custom data collection form:
    1. **Category Name:** Enter a unique name for your data category (e.g., *Vegetables*, *Fruits*).
    2. **Add Prompt Fields:** Define fields that data collectors will fill out. Choose how each field appears:
       - *Text / Text Area:* For open-ended notes or descriptions.
       - *Number / Slider:* For numerical metrics (requires min/max values).
       - *Dropdown / Radio:* For selectable options (**must be comma-separated**, e.g., `Fresh, Ripe, Spoiled`).
    3. **Queue Fields:** Click **Add** after configuring each field to append it to your list below.
    4. **Configure Hardware & Integration:** Select whether to use a Kinect camera and/or configure automated RoboFlow image uploads.
    5. **Confirm:** Click **Confirm** at the bottom to publish your new category to the platform!
    """)
st.subheader("Add Category")

if "prompts" not in st.session_state:
  st.session_state.prompts = []

if "active_category" not in st.session_state:
  st.session_state.active_category = ""

if "disable" not in st.session_state:
  st.session_state.disable = False

if "roboflow_settings" not in st.session_state:
  st.session_state.roboflow_settings = {}

if "camera_settings" not in st.session_state:
  st.session_state.camera_settings = False

if "new_prompts" not in st.session_state:
  st.session_state.new_prompts = []

if "pushed_buttons" not in st.session_state:
  st.session_state.pushed_buttons = {}

if len(st.session_state.prompts) > 0:
  category_name = st.text_input(
      "Category Name:",
      disabled=True,
      help="Clear current prompts or click confrim to change category",
      value=st.session_state.active_category,
  )
else:
  category_name = st.text_input(
      "Category Name:", value=st.session_state.active_category
  )

if len(st.session_state.prompts) == 0:
  st.session_state.active_category = category_name

prompt = st.text_input("Add Prompt:", key="make_prompt")
selection = st.selectbox(
    "How should this field be displayed:",
    [
        "Text Box",
        "Text Area (multi-line)",
        "Number Input",
        "Dropdown List",
        "Radio Button",
        "Slider",
    ],
    key="make_selection",
)

settings = {"selection": selection, "prompt": prompt}

range_error = False
validation_error = False

if selection == "Number Input" or selection == "Slider":
  max_value = st.number_input("Enter max value:")
  min_value = st.number_input("Enter min value:")

  if max_value <= min_value:
    range_error = True
    st.error("Max value must be strictly greater than the Min value.")

  settings["max"] = max_value
  settings["min"] = min_value

elif (
    selection == "Dropdown List"
    or selection == "Radio Button"
    or selection == "Check Box"
):
  raw_options = st.text_input("Enter options (comma separated):")
  cleaned_options = raw_options.replace(".", ",").strip().rstrip(",").strip()

  if "," in cleaned_options:
    settings["options"] = cleaned_options
  else:
    st.error(
        " Validation Error: You must enter at least two options separated by a"
        " comma."
    )
    validation_error = True


if st.button("Add"):
  if not prompt.strip():
    st.error("Please enter a name for the prompt before adding.")
  elif (selection in ["Dropdown List", "Radio Button"]) and not settings.get(
      "options", ""
  ).strip():
    st.error(f"Please enter options for the {selection}.")
  elif not category_name.strip():
    st.error("Please enter a name for the Category before adding.")
  elif range_error:
    st.error("Cannot save: Please fix the Min/Max range issue first.")
  elif validation_error:
    st.error("Cannot save: Please fix options before adding.")
  else:
    st.session_state.prompts.append(settings)
    st.rerun()


st.divider()

kinect = st.selectbox(
    "Use of Kinect camera:", ["False", "True"], key="kinect_camera"
)

st.divider()
st.info(
    "💡 **Quick Guide: Roboflow in Category Settings vs. The Roboflow"
    " Workspace**\n\n• **Here (Category Settings):** Configures **automatic,"
    " background uploads** for a specific category. Any images captured under"
    " this category are automatically pushed to Roboflow in real-time during"
    " data collection.\n\n• **Roboflow Workspace Page (`roboflow.py`):** Acts as"
    " a **manual curation and batch-upload dashboard**. It allows"
    " administrators and collectors to browse past submissions, filter by"
    " date, select specific images, and batch-upload them with cleaned form"
    " metadata."
)

roboflow = st.selectbox(
    "Enable Automatic Roboflow Upload", ["False", "True"], key="roboflow"
)

if roboflow == "True":
  api_key = st.text_input(
      "Please Input RoboFlow API Key:", type="password", key="api_key"
  )
  workspace = st.text_input("Please Input Workspace:", key="workspace")
  project_id = st.text_input("Please Input Project ID:", key="project_id")

  if api_key and workspace and project_id:
    try:
      roboflow_response = requests.get(
          f"https://api.roboflow.com/{workspace}/{project_id}",
          params={"api_key": api_key},
      )

      if roboflow_response.status_code == 200:
        st.success("Credentials verified successfully!")
        roboflow_settings = {
            "api_key": api_key,
            "workspace": workspace,
            "project_id": project_id,
        }
      else:
        st.error("Invalid Credentials")
        roboflow_settings = False
    except:
      st.error("Network Connection Failed.")
      roboflow_settings = False
else:
  roboflow_settings = False


st.divider()

st.subheader("Current Prompts")

for count, prompt in enumerate(st.session_state.prompts):
  col1, col2 = st.columns([4, 1])

  with col1:
    st.write(f"{count+1}. {prompt}")

  with col2:
    if st.button("Delete", key=f"delete_key{count}"):
      st.session_state.prompts.pop(count)

if st.button("Confirm"):
  clean_category = " ".join(category_name.split())

  try:
    existing_categories = requests.get(f"{URL}/home").json()
  except Exception:
    existing_categories = []

  if not st.session_state.active_category.strip() or not st.session_state.prompts:
    st.error("Submission Denied: Category Name cannot be blank")
    st.error(
        "Submission Denied: You must add at least one prompt field configuring."
    )

  elif clean_category.lower() in [
      category.lower() for category in existing_categories
  ]:
    st.error("Submission Denied: Category already exist")
    st.info(
        "Please use the Edit Category section below if you wish to modify it."
    )

  else:
    page = {
        "category": clean_category,
        "prompts": [prompt for prompt in st.session_state.prompts],
        "camera": kinect,
        "roboflow": roboflow_settings,
    }

    response = requests.post(f"{URL}/settings", json=page)
    if response.status_code in [200, 201]:
      st.session_state.prompts = []
      st.session_state.active_category = ""

      st.success("The settings have been added and everything is good!")
      time.sleep(3)
      st.rerun()
    else:
      st.error(f"Server rejected update. Error code: {response.status_code}")

####################### Edit category ########################

st.divider()
st.subheader("Edit Category")

try:
  existing_categories = requests.get(f"{URL}/home").json()
except Exception:
  existing_categories = []

if not existing_categories:
  st.info("No categories available to edit.")
else:
  selected_category = st.selectbox(
      "Select the category you wish to edit:",
      existing_categories,
      key="edit_category_selector",
  )

  if (
      "edit_target_category" not in st.session_state
      or st.session_state.edit_target_category != selected_category
  ):
    try:
      cat_data = requests.get(f"{URL}/settings/{selected_category}").json()
      st.session_state.edit_target_category = selected_category
      st.session_state.editable_prompts = [
          dict(p) for p in cat_data.get("prompts", [])
      ]
      st.session_state.edit_camera = cat_data.get("camera", "False")
      st.session_state.edit_roboflow = cat_data.get("roboflow", False)
    except Exception:
      st.session_state.editable_prompts = []
      st.session_state.edit_camera = "False"
      st.session_state.edit_roboflow = False

  if "editable_prompts" not in st.session_state:
    st.session_state.editable_prompts = []

  with st.expander(f"Modify Fields for: {selected_category}", expanded=True):
    st.markdown(
        "Make your changes directly below. You can edit field names, modify"
        " options, delete fields, or add new ones."
    )
    st.divider()

    available_displays = [
        "Text Box",
        "Text Area (multi-line)",
        "Number Input",
        "Dropdown List",
        "Radio Button",
        "Slider",
    ]

    prompts_to_delete = []

    for i, p_item in enumerate(st.session_state.editable_prompts):
      st.markdown(f"### Field #{i+1}")

      col_a, col_b = st.columns([3, 1])
      with col_a:
        p_item["prompt"] = st.text_input(
            "Field Label:", value=p_item.get("prompt", ""), key=f"edit_p_name_{i}"
        )
      with col_b:
        current_sel = p_item.get("selection", "Text Box")
        default_idx = (
            available_displays.index(current_sel)
            if current_sel in available_displays
            else 0
        )
        p_item["selection"] = st.selectbox(
            "Display Type:",
            available_displays,
            index=default_idx,
            key=f"edit_p_sel_{i}",
        )

      if p_item["selection"] in ["Number Input", "Slider"]:
        c1, c2 = st.columns(2)
        with c1:
          p_item["min"] = st.number_input(
              "Min Value:",
              value=float(p_item.get("min", 0)),
              key=f"edit_p_min_{i}",
          )
        with c2:
          p_item["max"] = st.number_input(
              "Max Value:",
              value=float(p_item.get("max", 10)),
              key=f"edit_p_max_{i}",
          )
      elif p_item["selection"] in ["Dropdown List", "Radio Button", "Check Box"]:
        raw_opts = p_item.get("options", "")
        p_item["options"] = st.text_input(
            "Options (comma separated):",
            value=raw_opts,
            key=f"edit_p_opts_{i}",
            placeholder="e.g., Option 1, Option 2",
        )

      if st.button("🗑️ Remove This Field", key=f"remove_field_{i}"):
        prompts_to_delete.append(i)

      st.divider()

    if prompts_to_delete:
      for index in sorted(prompts_to_delete, reverse=True):
        st.session_state.editable_prompts.pop(index)
      st.rerun()

    with st.expander("➕ Add Another Field to this Category"):
      new_f_name = st.text_input(
          "New Field Label", key="quick_add_name", placeholder="e.g., Notes"
      )
      new_f_type = st.selectbox(
          "New Field Display Type", available_displays, key="quick_add_type"
      )

      new_f_dict = {"prompt": new_f_name, "selection": new_f_type}

      if new_f_type in ["Number Input", "Slider"]:
        new_f_dict["min"] = st.number_input("Min:", value=0.0, key="qa_min")
        new_f_dict["max"] = st.number_input("Max:", value=10.0, key="qa_max")
      elif new_f_type in ["Dropdown List", "Radio Button", "Check Box"]:
        new_f_dict["options"] = st.text_input(
            "Options (comma separated):",
            key="qa_opts",
            placeholder="Yes, No",
        )

      if st.button("Append Field"):
        if not new_f_name.strip():
          st.error("Field label cannot be empty.")
        else:
          st.session_state.editable_prompts.append(new_f_dict)
          st.success("Field added to queue!")
          st.rerun()

    st.divider()
    st.subheader("Integration & Hardware Settings")

    current_rf = st.session_state.get("edit_roboflow", False)
    rf_toggle = st.selectbox(
        "Enable Automatic Roboflow Upload",
        ["False", "True"],
        index=1 if current_rf else 0,
        key="edit_rf_toggle",
    )

    if rf_toggle == "True":
      default_api = (
          current_rf.get("api_key", "") if isinstance(current_rf, dict) else ""
      )
      default_ws = (
          current_rf.get("workspace", "") if isinstance(current_rf, dict) else ""
      )
      default_proj = (
          current_rf.get("project_id", "")
          if isinstance(current_rf, dict)
          else ""
      )

      rf_api_key = st.text_input(
          "RoboFlow API Key:",
          value=default_api,
          type="password",
          key="edit_rf_api_key",
      )
      rf_workspace = st.text_input(
          "Workspace:", value=default_ws, key="edit_rf_workspace"
      )
      rf_project_id = st.text_input(
          "Project ID:", value=default_proj, key="edit_rf_project_id"
      )

      if rf_api_key and rf_workspace and rf_project_id:
        try:
          rf_response = requests.get(
              f"https://api.roboflow.com/{rf_workspace}/{rf_project_id}",
              params={"api_key": rf_api_key},
          )
          if rf_response.status_code == 200:
            st.success("Roboflow credentials verified successfully!")
            st.session_state.edit_roboflow = {
                "api_key": rf_api_key,
                "workspace": rf_workspace,
                "project_id": rf_project_id,
            }
          else:
            st.error("Invalid Roboflow Credentials")
            st.session_state.edit_roboflow = False
        except Exception:
          st.error("Roboflow Network Connection Failed.")
          st.session_state.edit_roboflow = False
      else:
        st.session_state.edit_roboflow = False
    else:
      st.session_state.edit_roboflow = False

    st.divider()

    camera_val = str(st.session_state.get("edit_camera", "False"))
    st.session_state.edit_camera = st.selectbox(
        "Use of Kinect camera:",
        ["False", "True"],
        index=0 if camera_val == "False" else 1,
        key="edit_cam_select",
    )

    st.divider()
    if st.button("💾 Save All Changes", type="primary"):
      if not st.session_state.editable_prompts:
        st.error(
            "Validation Error: A category must contain at least one field."
        )
      else:
        has_empty_names = any(
            not p.get("prompt", "").strip()
            for p in st.session_state.editable_prompts
        )
        if has_empty_names:
          st.error("All fields must have a valid label name.")
        else:
          update_payload = {
              "category": selected_category,
              "prompts": st.session_state.editable_prompts,
              "camera": st.session_state.edit_camera,
              "roboflow": st.session_state.edit_roboflow,
          }

          response = requests.post(f"{URL}/settings", json=update_payload)

          if response.status_code in [200, 201]:
            st.success("Category successfully updated!")
            if "edit_target_category" in st.session_state:
              del st.session_state.edit_target_category
            time.sleep(2)
            st.rerun()
          else:
            st.error(
                f"Failed to update category. Server error code:"
                f" {response.status_code}"
            )

# =========================================================================
# ADMIN-ONLY ROLE & USER MANAGEMENT SECTION
# =========================================================================
if is_admin:
  st.divider()
  st.title("Request Management")
  try:
    requests_response = requests.get(f"{URL}/requests")
    pending_requests = (
        requests_response.json() if requests_response.status_code == 200 else []
    )
  except Exception:
    pending_requests = []

  if not pending_requests:
    st.info("No pending role requests found.")
  else:
    st.subheader(f"Pending Requests ({len(pending_requests)})")

    for index, req in enumerate(pending_requests):
      req_email = req.get("email", "Unknown Email")
      req_name = req.get("name", "Unknown")
      req_reason = req.get("reason", "No reason provided.")
      req_date = req.get("date", "Unknown")

      with st.expander(f"Request from: {req_email} -> Name: {req_name}"):
        st.write(f"**Email:** {req_email}")
        st.write(f"**Name:** {req_name}")
        st.write(f"**Reason / Notes:** {req_reason}")
        st.write(f"**Date:** {req_date}")

        available_roles = ["admin", "developer", "collector"]
        selected_role = st.selectbox(
            "Assign Role:",
            available_roles,
            key=f"role_select_{index}_{req_email}",
        )

        col1, col2 = st.columns(2)

        with col1:
          if st.button("Approve & Assign", key=f"approve_{index}_{req_email}"):
            payload = {"email": req_email, "role": selected_role}
            res = requests.post(f"{URL}/roles/assign", json=payload)

            if res.status_code in [200, 201]:
              requests.delete(f"{URL}/requests/remove", json={"email": req_email})
              st.success(
                  f"Successfully approved {req_email} for role '{selected_role}'!"
              )
              st.rerun()
            else:
              st.error("Failed to approve request on the backend.")

        with col2:
          if st.button("Dismiss / Reject", key=f"reject_{index}_{req_email}"):
            payload = {"email": req_email}
            res = requests.delete(f"{URL}/requests/remove", json=payload)

            if res.status_code in [200, 201]:
              st.warning(f"Dismissed request for {req_email}.")
              st.rerun()
            else:
              st.error("Failed to dismiss request.")

  st.divider()
  st.title("Edit Roles & User Management")
  st.divider()

  st.subheader("Directly Assign / Invite User Role")
  with st.form("invite_user_form"):
    invite_email = st.text_input("User Email Address:")
    invite_role = st.selectbox(
        "Select Role to Assign:", ["admin", "developer", "collector"]
    )
    submit_invite = st.form_submit_button("Assign Role")

    if submit_invite:
      if not invite_email.strip():
        st.error("Please enter a valid email address.")
      else:
        payload = {"email": invite_email.strip(), "role": invite_role}
        res = requests.post(f"{URL}/roles/assign", json=payload)
        if res.status_code in [200, 201]:
          st.success(
              f"Successfully assigned {invite_email} to role '{invite_role}'!"
          )
          st.rerun()
        else:
          st.error("Failed to assign role on the backend.")

  st.divider()
  st.subheader("Manage Existing User Roles")

  try:
    roles_response = requests.get(f"{URL}/roles")
    roles = roles_response.json() if roles_response.status_code == 200 else {}
  except Exception:
    roles = {}

  if not roles:
    st.info("No roles or assignments found.")
  else:
    for role_name, users in roles.items():
      role_descriptions = {
          "admin": "👑 **Administrator:** Full system access, including category configuration, user role management, request approvals, and workspace analytics.",
          "developer": "🔬 **Developer:** Access to category structure creation, field modifications, and advanced hyperparameter controls for model training scripts.",
          "collector": "🎯 **Collector:** Access to data collection forms, image capture workflows, and the manual Roboflow dataset curation workspace."
      }
      
      st.write(f"### Role: `{role_name}`")
      if role_name in role_descriptions:
        st.info(role_descriptions[role_name])

      if not users:
        st.write("_No users assigned to this role._")
      else:
        for user_email in users:
          col1, col2, col3 = st.columns([2, 1, 1])
          with col1:
            st.write(f"• {user_email}")
          with col2:
            reassign_role = st.selectbox(
                "Change Role",
                ["admin", "developer", "collector"],
                index=["admin", "developer", "collector"].index(role_name)
                if role_name in ["admin", "developer", "collector"]
                else 0,
                key=f"reassign_{role_name}_{user_email}",
                label_visibility="collapsed",
            )
            if st.button(
                "Move", key=f"move_btn_{role_name}_{user_email}"
            ) and reassign_role != role_name:
              res_add = requests.post(
                  f"{URL}/roles/assign",
                  json={"email": user_email, "role": reassign_role},
              )
              res_rem = requests.delete(
                  f"{URL}/roles/remove",
                  json={"email": user_email, "role": role_name},
              )
              if res_add.status_code in [200, 201]:
                st.success(f"Moved {user_email} to {reassign_role}")
                st.rerun()
              else:
                st.error("Failed to update role.")
          with col3:
            if st.button("Remove", key=f"del_{role_name}_{user_email}"):
              payload = {"email": user_email, "role": role_name}
              delete_response = requests.delete(
                  f"{URL}/roles/remove", json=payload
              )

              if delete_response.status_code == 200:
                st.success(f"Removed {user_email} from {role_name}")
                st.rerun()
              else:
                st.error("Failed to remove user.")

  st.divider()
else:
  st.divider()
  st.info(
      "🔒 **Restricted Area:** User role management, invitation tools, and"
      " pending access request approvals are visible and manageable by"
      " **Administrators only**."
  )