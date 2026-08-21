from datetime import datetime
import json
import re
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
    4. **Filter & Inspect:** Use the date range picker and search bar to filter sample records, then expand individual sample cards to view captured images.
    5. **Add to Queue:** Click the **Add** button on any image you want to queue for upload. Selected images will appear in the right-hand panel.
    6. **Upload:** Review your queued images, remove any if needed, and click **Upload Selected images to RoboFlow** to batch-upload them along with their clean form metadata.
    """)

if "lock1" not in st.session_state:
  st.session_state.lock1 = False
if "lock2" not in st.session_state:
  st.session_state.lock2 = True
if "selected_images" not in st.session_state:
  st.session_state.selected_images = []
if "upload_history" not in st.session_state:
  st.session_state.upload_history = []

# RESTRICT CONFIGURATION PANEL STRICTLY TO ADMINS
if is_admin or is_dev:
  st.info(
      "💡 **Where to find your Roboflow credentials:**\n\n"
      "1. **API Key:** Go to your Roboflow account settings -> **Roboflow"
      " API** section to copy your private key.\n"
      "2. **Workspace:** Found in your account URL or top-left corner of your"
      " Roboflow dashboard (slug name).\n"
      "3. **Project ID:** Found inside your specific project URL (e.g.,"
      " `app.roboflow.com/workspace-name/project-id`)."
  )

  with st.expander("🛠️ RoboFlow Configuration"):
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
          name = st.text_input(
              "Please enter name for settings:", key="roboflow_name"
          )

          if not name.strip():
            roboflow = False
          else:
            roboflow = {
                "name": name.strip(),
                "api_key": api_key,
                "workspace": workspace,
                "project_id": project_id,
            }
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

col_sel, col_btn = st.columns([3, 1])
with col_sel:
  roboflow_selection = st.selectbox(
      "Select roboflow account/project to upload images",
      roboflow_settings,
      disabled=st.session_state.lock1,
  )

with col_btn:
  st.write("")  # alignment spacing
  if not st.session_state.lock1:
    if st.button("Use", use_container_width=True):
      st.session_state.lock1 = True
      st.session_state.lock2 = False
      st.rerun()
  else:
    if st.button("Change Target", use_container_width=True):
      st.session_state.lock1 = False
      st.session_state.lock2 = True
      st.rerun()

# If a target is locked in, fetch specific settings to enable direct link button
if st.session_state.lock1 and roboflow_selection:
  try:
    active_robo_cfg = requests.get(
        f"{URL}/roboflow/{roboflow_selection}"
    ).json()
    active_ws = active_robo_cfg.get("workspace")
    active_proj = active_robo_cfg.get("project_id")
    if active_ws and active_proj:
      st.markdown(
          f"🔗 **[Open Active Project in Roboflow Dashboard](https://app.roboflow.com/{active_ws}/{active_proj})**"
      )
  except Exception:
    pass

try:
  categories = requests.get(f"{URL}/home").json()
except Exception:
  categories = []

if not categories:
  st.write("No categories available")
  st.stop()

category_selection = st.selectbox(
    "Select category to select images from:",
    categories,
    disabled=st.session_state.lock2,
    help="Please select RoboFlow account first",
)

# Session Upload History & Analytics Expander with CSV Export
with st.expander(
    "📊 Session Upload History & Analytics Dashboard", expanded=False
):
  if not st.session_state.upload_history:
    st.caption("No uploads performed yet during this session.")
  else:
    col_hist, col_chart = st.columns(2)
    with col_hist:
      st.markdown("##### Upload Logs")
      for h in st.session_state.upload_history:
        st.markdown(
            f"- **{h['timestamp']}**: Uploaded **{h['count']}** images to"
            f" target `{h['target']}`"
        )
    with col_chart:
      st.markdown("##### Upload Volume Chart")
      chart_data = {
          h["timestamp"].split()[0]: h["count"]
          for h in st.session_state.upload_history
      }
      st.bar_chart(chart_data)

    st.markdown("---")
    csv_log = "Timestamp,Count,Target\n" + "\n".join([
        f"{h['timestamp']},{h['count']},{h['target']}"
        for h in st.session_state.upload_history
    ])
    st.download_button(
        label="📥 Export Audit Log (CSV)",
        data=csv_log,
        file_name="upload_audit_log.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.divider()

try:
  samples = requests.get(f"{URL}/collection/samples/{category_selection}").json()
except Exception:
  samples = []

if not samples:
  st.write(f"No submissions found for {category_selection}.")
  st.stop()

st.header("Filter & Search")

today = datetime.today().date()
date_range = st.date_input(
    "Select Date Range:", value=(today, today), max_value=today
)

search_query = st.text_input(
    "🔍 Quick Search Submissions:",
    placeholder="Search by keyword, form answer, or Sample ID...",
)

cols = st.columns([0.7, 0.3])

with cols[0]:
  filtered_samples = []

  for sample in samples:
    sample_id = sample["sample_id"]
    try:
      sample_date = datetime.strptime(sample["date"], "%Y-%m-%d").date()
    except (ValueError, TypeError):
      sample_date = None

    sample_information = sample["data"]

    if search_query:
      match_found = (
          search_query.lower() in sample_id.lower()
          or any(
              search_query.lower() in str(val).lower()
              for val in sample_information.values()
          )
      )
      if not match_found:
        continue

    if isinstance(date_range, tuple) and len(date_range) == 2:
      start_date, end_date = date_range
      if sample_date and not (start_date <= sample_date <= end_date):
        continue

    filtered_samples.append(sample)

  if filtered_samples and not st.session_state.lock2:
    batch_col1, batch_col2 = st.columns(2)
    with batch_col1:
      if st.button("📥 Add All Filtered Images to Queue", use_container_width=True):
        added_count = 0
        for sample in filtered_samples:
          s_id = sample["sample_id"]
          try:
            imgs = requests.get(f"{URL}/collection/images/{s_id}").json()
            for img_obj in imgs:
              img_id = img_obj["image_id"]
              already_in = any(
                  item["image_id"] == img_id
                  for item in st.session_state.selected_images
              )
              if not already_in:
                st.session_state.selected_images.append({
                    "image_id": img_id,
                    "sample": sample,
                })
                added_count += 1
          except Exception:
            continue
        if added_count > 0:
          st.success(f"Added {added_count} images to queue!")
          st.rerun()

    with batch_col2:
      if st.button("🗑️ Clear Active Queue", use_container_width=True):
        st.session_state.selected_images = []
        st.rerun()

    st.markdown("---")

  if not filtered_samples:
    st.info("No matching samples found for your filter and search criteria.")
  else:
    for sample in filtered_samples:
      sample_id = sample["sample_id"]
      sample_information = sample["data"]

      with st.expander(f"Sample ID: {sample_id}, Date: {sample['date']}"):
        for question, answer in sample_information.items():
          st.write(f"**{question}:** {answer}")

        # Server-side Sample Deletion for Admins/Developers
        if is_admin or is_dev:
          if st.button(
              "🗑️ Delete Entire Sample from Server",
              key=f"del_sample_{sample_id}",
          ):
            try:
              del_resp = requests.delete(
                  f"{URL}/collection/sample/{sample_id}"
              )
              if del_resp.status_code == 200:
                st.success("Sample successfully deleted from server!")
                st.rerun()
              else:
                st.error("Failed to delete sample.")
            except Exception:
              st.error("Deletion request failed.")

        try:
          images_list = requests.get(
              f"{URL}/collection/images/{sample_id}"
          ).json()
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

          is_already_selected = any(
              item["image_id"] == image_id
              for item in st.session_state.selected_images
          )
          lock = is_already_selected or st.session_state.lock2

          with columns[count % 3]:
            st.image(
                actual_image.content,
                caption=f"Image ID: {image_id}",
                use_container_width=True,
            )
            if st.button(
                "Add",
                key=f"add_button_{image_id}",
                disabled=lock,
                help=(
                    "Please select RoboFlow account first/already added into"
                    " selected images"
                ),
            ):
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
    action_col1, action_col2 = st.columns(2)
    with action_col1:
      if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.selected_images = []
        st.rerun()

    with action_col2:
      export_data = []
      for item in st.session_state.selected_images:
        export_data.append({
            "image_id": item["image_id"],
            "sample_id": item["sample"].get("sample_id"),
            "date": item["sample"].get("date"),
            "data": item["sample"].get("data"),
        })
      st.download_button(
          label="📥 Export",
          data=json.dumps(export_data, indent=2),
          file_name="roboflow_queue.json",
          mime="application/json",
          use_container_width=True,
      )

    st.write("")

    for selected_image in list(st.session_state.selected_images):
      img = selected_image["image_id"]
      samp_id = selected_image["sample"].get("sample_id", "unknown")
      sample_data = selected_image["sample"].get("data", {})

      try:
        thumb_resp = requests.get(f"{URL}/collection/image/{img}")
        thumb_content = (
            thumb_resp.content if thumb_resp.status_code == 200 else None
        )
      except Exception:
        thumb_content = None

      with st.expander(f"ID: {img[:8]}..."):
        if thumb_content:
          st.image(thumb_content, use_container_width=True)

        st.markdown(f"**Full ID:** `{img}`")
        st.markdown(f"**Sample ID:** `{samp_id}`")
        st.caption("Attached Metadata:")
        for q, a in sample_data.items():
          st.markdown(f"- **{q}:** {a}")

        unique_delete_key = f"delete_{samp_id}_{img}"
        if st.button(
            "Remove from Queue",
            key=unique_delete_key,
            use_container_width=True,
        ):
          for index, item in enumerate(st.session_state.selected_images):
            if (
                item["image_id"] == img
                and item["sample"].get("sample_id") == samp_id
            ):
              st.session_state.selected_images.pop(index)
              break
          st.rerun()

    st.divider()

    if st.button("Upload Selected images to RoboFlow", type="primary"):
      success_count = 0

      try:
        robo_settings = requests.get(
            f"{URL}/roboflow/{roboflow_selection}"
        ).json()
        selected_api_key = robo_settings["api_key"]
        selected_project_id = robo_settings["project_id"]
      except Exception:
        st.error("Failed to retrieve selected RoboFlow settings.")
        st.stop()

      roboflow_URL = (
          f"https://api.roboflow.com/dataset/{selected_project_id}/upload"
      )
      params = {"api_key": selected_api_key}

      progress_text = st.empty()
      progress_bar = st.progress(0)
      total_images = len(st.session_state.selected_images)

      for index, image_info in enumerate(st.session_state.selected_images):
        img_id = image_info["image_id"]
        progress_text.text(
            f"Uploading image {index + 1} of {total_images} (ID: {img_id[:8]}...)"
        )

        try:
          actual_image = requests.get(f"{URL}/collection/image/{img_id}").content
        except Exception:
          progress_bar.progress((index + 1) / total_images)
          continue

        sample_data = image_info["sample"]["data"]
        metadata = {}
        for prompt, answer in sample_data.items():
          clean_key = re.sub(r"[^a-zA-Z0-9\s]", "", prompt)
          clean_key = clean_key.strip().replace(" ", "_")
          metadata[clean_key] = answer

        files = {"file": actual_image}
        payload_data = {
            "name": f"image_id: {img_id}",
            "metadata": json.dumps(metadata),
        }

        try:
          roboflow_response = requests.post(
              roboflow_URL, params=params, files=files, data=payload_data
          )
          if roboflow_response.status_code == 200:
            success_count += 1
        except Exception:
          pass

        progress_bar.progress((index + 1) / total_images)

      progress_text.empty()
      progress_bar.empty()

      if success_count > 0:
        st.session_state.upload_history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "count": success_count,
            "target": roboflow_selection,
        })
        st.success(
            f"Successfully uploaded {success_count} of {total_images} images to"
            " RoboFlow!"
        )
        st.info(
            "🔑 **To see your uploaded images, please log in to Roboflow using these credentials:**\n\n"
            "- **Email:** `greatroboticslab2@gmail.com`\n"
            "- **Password:** `Robotics!!22`"
        )
        st.session_state.selected_images = []
        st.rerun()
      else:
        st.error(
            "Upload failed. Please check your network and API credentials."
        )