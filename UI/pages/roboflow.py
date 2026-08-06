import streamlit as st
import requests 
from key import URL 
from datetime import datetime 
import re 
import json

# =========================================================================
# ACCESS CONTROL & ROLE VERIFICATION
# =========================================================================
user_obj = getattr(st, "user", None) or getattr(st, "experimental_user", None)
is_logged_in = user_obj and getattr(user_obj, "is_logged_in", False)

if not is_logged_in:
  st.warning(
      "🔒 Please sign in with Google from the Home page to access the workspace."
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

# ENFORCE ACCESS: Restrict workspace access to authorized users
if not (is_admin or is_dev or is_collector):
  st.error(
      f"⛔ Access Denied: Your email (**{user_email}**) is not authorized to"
      " access the RoboFlow workspace."
  )
  st.stop()

# =========================================================================
# MAIN ROBOFLOW DASHBOARD
# =========================================================================

st.title("RoboFlow Workspace")

# User Guide Display
with st.expander("📖 How to Use the RoboFlow Workspace", expanded=False):
    st.markdown("""
    Welcome to the **RoboFlow Image Upload Pipeline**. Follow these steps to select and upload your sample data:
    
    1. **Configure Account (Admins Only):** If no RoboFlow settings are available, administrators can expand the **RoboFlow Configuration** section below to securely add API keys, workspaces, and project IDs.
    2. **Select RoboFlow Target:** Choose your target account/project from the dropdown menu and click **Use** to lock in your selection.
    3. **Pick a Category:** Choose a category of data submissions to view the available samples.
    4. **Filter & Inspect:** Use the date range picker to filter sample records, then expand individual sample cards to view captured images.
    5. **Add to Queue:** Click the **Add** button on any image you want to queue for upload. Selected images will appear in the right-hand panel.
    6. **Upload:** Review your queued images, remove any if needed, and click **Upload Selected images to RoboFlow** to batch-upload them along with their clean form metadata.
    """)

if "lock1" not in st.session_state:
    st.session_state.lock1 = False 
if "lock2" not in st.session_state:
    st.session_state.lock2 = True 
if "selected_images" not in st.session_state:
    st.session_state.selected_images = []

# RESTRICT CONFIGURATION PANEL STRICTLY TO ADMINS
if is_admin:
    st.info(
            "💡 **Where to find your Roboflow credentials:**\n\n"
            "1. **API Key:** Go to your Roboflow account settings -> **Roboflow API** section to copy your private key.\n"
            "2. **Workspace:** Found in your account URL or top-left corner of your Roboflow dashboard (slug name).\n"
            "3. **Project ID:** Found inside your specific project URL (e.g., `app.roboflow.com/workspace-name/project-id`)."
        )

    with st.expander("🛠️ RoboFlow Configuration (Admin Only)"):
        api_key = st.text_input("Please Input RoboFlow API Key:", type="password", key="api_key")
        workspace = st.text_input ("Please Input Workspace:", key="workspace")
        project_id = st.text_input("Please Input Project ID:", key="project_id")

        if api_key and workspace and project_id:
            try:
                roboflow_response = requests.get(f"https://api.roboflow.com/{workspace}/{project_id}", params={"api_key":api_key})
            
                if roboflow_response.status_code == 200:
                    name = st.text_input("Please enter name for settings:", key="roboflow_name")
                    
                    if not name.strip():
                        roboflow = False
                    else:
                        roboflow = {"name": name.strip(), "api_key": api_key, "workspace": workspace, "project_id": project_id}
                else:
                    st.error("Invalid Credentials")
                    roboflow = False
            except:
                roboflow = False
        else:
            roboflow = False 

        if roboflow:
            if st.button("Save"):
                response = requests.post(f"{URL}/roboflow", json=roboflow)
                if response.status_code in [200, 201]:
                    st.success("Saved!!!")
                    st.rerun()

st.divider()

try:
    roboflow_settings = requests.get(f"{URL}/roboflow").json()
except Exception:
    roboflow_settings = []

if not roboflow_settings:
    st.write("No roboflow settings exists")
    st.stop()

roboflow_selection = st.selectbox("Select roboflow account/project to upload images", roboflow_settings, disabled=st.session_state.lock1)

if st.button("Use", disabled=st.session_state.lock1):
    st.session_state.lock1 = True 
    st.session_state.lock2 = False 
    st.rerun()
   
try:
    categories = requests.get(f"{URL}/home").json()
except Exception:
    categories = []

if not categories:
    st.write("No categories available")
    st.stop()

category_selection = st.selectbox("Select category to select images from:", categories, disabled=st.session_state.lock2, help="Please select RoboFlow account first")

st.divider()

try:
    samples = requests.get(f"{URL}/collection/samples/{category_selection}").json()
except Exception:
    samples = []

if not samples:
    st.write(f"No submissions found for {category_selection}.")
    st.stop()

st.header("Filter")

today = datetime.today().date()
date_range = st.date_input(
    "Select Date Range:",
    value=(today, today),
    max_value=today
)

cols = st.columns([0.7, 0.3])

with cols[0]:
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

                try:
                    images_list = requests.get(f"{URL}/collection/images/{sample_id}").json()
                except Exception:
                    images_list = []
                    
                st.write("## Captured Images")
                
                columns = st.columns(3)
                for count, image in enumerate(images_list):
                    image_id = image["image_id"]
                    try:
                        actual_image = requests.get(f"{URL}/collection/image/{image_id}")
                    except Exception:
                        continue

                    is_already_selected = any(item["image_id"] == image_id for item in st.session_state.selected_images)
                    lock = is_already_selected or st.session_state.lock2

                    with columns[count % 3]:
                        st.image(actual_image.content, caption=f"Image ID: {image_id}", width="stretch")
                        if st.button("Add", key=f"add_button_{image_id}", disabled=lock, help="Please select RoboFlow account first/already added into selected images"):
                            st.session_state.selected_images.append({
                                "image_id": image_id,
                                "sample": sample,
                            })
                            st.rerun()

with cols[1]:
    st.subheader("Selected Images")

    if not st.session_state.selected_images:
        st.write("No images selected.")
    else:
        for selected_image in list(st.session_state.selected_images):
            img = selected_image["image_id"]
            samp_id = selected_image["sample"].get("sample_id", "unknown")

            selected_cols = st.columns([0.8, 0.2])

            with selected_cols[0]:
                st.write(img)
            
            with selected_cols[1]:
                unique_delete_key = f"delete_{samp_id}_{img}"
                if st.button("Delete", key=unique_delete_key):
                    for index, item in enumerate(st.session_state.selected_images):
                        if item["image_id"] == img and item["sample"].get("sample_id") == samp_id:
                            st.session_state.selected_images.pop(index)
                            break 
                    st.rerun()
        
        st.divider()

        if st.button("Upload Selected images to RoboFlow", type="primary"):
            success_count = 0
            
            for image_info in st.session_state.selected_images:
                img_id = image_info["image_id"]
                try:
                    actual_image = requests.get(f"{URL}/collection/image/{img_id}").content
                except Exception:
                    continue
                
                image_info["actual_image"] = actual_image
                sample_data = image_info["sample"]["data"]

                metadata = {}
                for prompt, answer in sample_data.items():
                    clean_key = re.sub(r'[^a-zA-Z0-9\s]', '', prompt)
                    clean_key = clean_key.strip().replace(" ", "_")
                    metadata[clean_key] = answer

                image_info["cleaned_metadata"] = metadata

            try:
                robo_settings = requests.get(f"{URL}/roboflow/{roboflow_selection}").json()
                selected_api_key = robo_settings["api_key"]
                selected_project_id = robo_settings["project_id"]
            except Exception:
                st.error("Failed to retrieve selected RoboFlow settings.")
                st.stop()

            roboflow_URL = f"https://api.roboflow.com/dataset/{selected_project_id}/upload"
            params = {"api_key": selected_api_key}

            for image in st.session_state.selected_images:
                files = {
                    "file": image["actual_image"]
                }
                
                payload_data = {
                    "name": f"image_id: {image['image_id']}",
                    "metadata": json.dumps(image['cleaned_metadata'])
                }

                try:
                    roboflow_response = requests.post(roboflow_URL, params=params, files=files, data=payload_data)

                    if roboflow_response.status_code == 200:
                        success_count += 1
                        st.success(f"Uploaded {image['image_id']} successfully!")
                    else:
                        st.error(f"Failed to upload {image['image_id']}: {roboflow_response.text}")
                except Exception as e:
                    st.error(f"Upload connection failed for {image['image_id']}: {e}")

            if success_count > 0:
                st.success(f"Successfully uploaded {success_count} images to RoboFlow!")
                st.session_state.selected_images = []
                st.rerun()