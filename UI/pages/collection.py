from datetime import date
import json
import re
import requests
import streamlit as st
from key import URL

# =========================================================================
# ACCESS CONTROL & ROLE CHECKING
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

user_email = getattr(user_obj, "email", "")

# Define individual role memberships
is_admin = user_email in roles.get("admin", [])
is_dev = user_email in roles.get("developer", [])
is_collector = user_email in roles.get("collector", [])

if not (is_admin or is_dev or is_collector):
  st.error(
      f"⛔ Access Denied: Your email (**{user_email}**) is not authorized to"
      " access collection forms."
  )
  if st.button("🚪 Logout", use_container_width=True):
    st.logout()
  st.stop()

# Ensure category exists in session state
category = getattr(st, "category", "General")
if "category" in st.session_state:
  category = st.session_state.category

st.title(f"📝 {category} Data Collection Workspace")
st.markdown(
    "Fill out the required metadata fields below and capture or upload your"
    " sample imagery."
)
st.divider()

# Fetch configuration prompts
try:
  page = requests.get(f"{URL}/settings/{category}").json()
except Exception:
  page = {"prompts": [], "camera": True, "roboflow": False}

prompts = page.get("prompts", [])

if not prompts:
  st.info(
      "No configuration prompts found for this category. Please check your"
      " backend settings."
  )

# =========================================================================
# SECTION 1: METADATA FORM INPUTS
# =========================================================================
st.subheader("1. Sample Metadata")
values = {}

# Use columns for a cleaner layout if there are multiple fields
for count, prompt in enumerate(prompts):
  selection = prompt["selection"]
  label = prompt["prompt"]
  key_name = f"input_{label}_{count}"

  match selection:
    case "Text Box":
      values[label] = st.text_input(label, key=key_name)

    case "Text Area (multi-line)":
      values[label] = st.text_area(label, key=key_name)

    case "Number Input":
      values[label] = st.number_input(
          label,
          min_value=prompt.get("min", 0.0),
          max_value=prompt.get("max", 1000.0),
          key=key_name,
      )

    case "Dropdown List":
      options = [opt.strip() for opt in prompt.get("options", "").split(",")]
      values[label] = st.selectbox(label, options=options, key=key_name)

    case "Radio Button":
      options = [opt.strip() for opt in prompt.get("options", "").split(",")]
      values[label] = st.radio(label, options=options, key=key_name)

    case "Slider":
      values[label] = st.slider(
          label,
          min_value=prompt.get("min", 0),
          max_value=prompt.get("max", 100),
          key=key_name,
      )

st.divider()

# =========================================================================
# SECTION 2: IMAGE CAPTURE & QUEUE
# =========================================================================
st.subheader("2. Sample Imagery Capture")

if "images" not in st.session_state:
  st.session_state.images = []

camera_col, queue_col = st.columns([1.2, 1])

with camera_col:
  st.markdown("📸 **Live Camera Feed**")
  picture = st.camera_input("Position sample and capture image")

  if picture:
    if st.button("➕ Add Captured Image to Queue", use_container_width=True):
      st.session_state.images.append(picture)
      st.success("Image successfully added to queue!")
      st.rerun()

with queue_col:
  st.markdown(
      f"🖼️ **Captured Queue ({len(st.session_state.images)} images)**"
  )

  if not st.session_state.images:
    st.info("No images captured yet. Take a snapshot to add it to the queue.")
  else:
    for idx, img in enumerate(list(st.session_state.images)):
      q_col1, q_col2 = st.columns([3, 1])
      with q_col1:
        st.image(img, caption=f"Shot #{idx + 1}", use_container_width=True)
      with q_col2:
        st.write("")  # alignment
        if st.button("❌", key=f"remove_img_{idx}", help="Remove this image"):
          st.session_state.images.pop(idx)
          st.rerun()

    if st.button("🗑️ Clear All Images", use_container_width=True):
      st.session_state.images = []
      st.rerun()

st.divider()

# Initialize submission state trackers
if "submitted" not in st.session_state:
  st.session_state.submitted = False
if "robo_submission" not in st.session_state:
  st.session_state.robo_submission = False
if "sample_id" not in st.session_state:
  st.session_state.sample_id = None

# =========================================================================
# SECTION 3: SUBMISSION HANDLER
# =========================================================================
st.subheader("3. Final Submission")

col_sub1, col_sub2 = st.columns([2, 1])
with col_sub1:
  st.markdown(
      "Review your entered metadata and captured images above, then click"
      " **Submit Record** to upload to the server and push to RoboFlow (if"
      " configured)."
  )

with col_sub2:
  submit_btn = st.button(
      "🚀 Submit Record", type="primary", use_container_width=True
  )

if submit_btn:
  today = date.today()

  if len(st.session_state.images) == 0:
    st.error(
        "⚠️ Please add at least one captured image before submitting the form!"
    )
  else:
    with st.spinner("Submitting record and uploading images..."):
      # 1. Post primary sample submission data
      try:
        response = requests.post(
            f"{URL}/collection/submission",
            json={"category": category, "date": str(today), "data": values},
        ).json()
        sample_id = response["sample_id"]
      except Exception as e:
        st.error(f"Failed to create submission record: {e}")
        st.stop()

      robo_success_count = 0
      upload_failed = False

      # 2. Upload each image associated with the sample
      for image in st.session_state.images:
        image.seek(0)
        img_response = requests.post(
            f"{URL}/collection/images/upload",
            files={"file": image},
            data={"sample_id": sample_id, "category": category},
        )

        if img_response.status_code != 200:
          upload_failed = True
          break

        image_id = img_response.json()["image_id"]

        # 3. Handle automatic RoboFlow forwarding if configured
        roboflow_settings = page.get("roboflow")
        if roboflow_settings:
          image.seek(0)
          project_id = roboflow_settings["project_id"]
          roboflow_URL = (
              f"https://api.roboflow.com/dataset/{project_id}/upload"
          )

          image_information = {"sample_id": str(sample_id)}
          for prompt_text, user_answer in values.items():
            clean_key = re.sub(r"[^a-zA-Z0-9\s]", "", prompt_text)
            clean_key = clean_key.strip().replace(" ", "_")
            image_information[clean_key] = str(user_answer)

          params = {"api_key": roboflow_settings["api_key"]}
          payload_data = {
              "name": f"{category}:Image ID:{image_id}",
              "metadata": json.dumps(image_information),
          }
          files = {"file": image}

          try:
            rf_response = requests.post(
                roboflow_URL, params=params, files=files, data=payload_data
            )
            if rf_response.status_code == 200:
              robo_success_count += 1
          except Exception:
            pass

      if upload_failed:
        st.error(
            "❌ One or more images failed to upload to the server repository."
        )
      else:
        st.session_state.submitted = True
        st.session_state.sample_id = sample_id
        if robo_success_count > 0:
          st.session_state.robo_submission = True

        st.success("✅ Submission Successful!")
        st.success(f"**Sample ID Assigned:** `{sample_id}`")
        if st.session_state.robo_submission:
          st.success(
              f"✅ Successfully synced {robo_success_count} image(s) to"
              " RoboFlow!"
          )

        # Clear image queue after successful push
        st.session_state.images = []
        st.balloons()