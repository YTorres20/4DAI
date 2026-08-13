from datetime import datetime
import json
import sys
import time
from key import URL
import requests
import streamlit as st

# =========================================================================
# PAGE CONFIGURATION & ACCESS CONTROL
# =========================================================================
# Configure browser tab title, icon, and switch layout to wide mode for dashboard usability.
st.set_page_config(page_title="Developer Lab", page_icon="🛠️", layout="wide")

# Retrieve active user object injected by Streamlit's Google Auth middleware.
user_obj = getattr(st, "user", None) or getattr(st, "experimental_user", None)
is_logged_in = user_obj and getattr(user_obj, "is_logged_in", False)

# Enforce authentication: Halt execution if user is not signed in via Google.
if not is_logged_in:
  st.warning(
      "🔒 Please sign in with Google from the Home page to access the"
      " Developer Lab."
  )
  st.stop()

# Fetch authorization roles configuration dictionary from the remote backend server.
try:
  roles = requests.get(f"{URL}/roles").json()
except Exception:
  roles = {}

user_email = getattr(user_obj, "email", "")
is_admin = user_email in roles.get("admin", [])
is_dev = user_email in roles.get("developer", [])

# Enforce authorization: Restrict visibility exclusively to admins and developers.
if not (is_admin or is_dev):
  st.error(
      f"⛔ Access Denied: Your email (**{user_email}**) is not authorized to"
      " view the Developer Lab."
  )
  st.stop()

# =========================================================================
# HEADER & ROLE BADGE
# =========================================================================
st.title("🛠️ Developer Lab & System Dashboard")
st.markdown(
    "Welcome to the dedicated developer workspace. Use this suite of tools to"
    " monitor API health, inspect database schemas, test custom endpoints,"
    " and review active sessions."
)

# Render explicit security and privilege level badge depending on user role.
if is_admin:
  st.success(
      "👑 **Administrator View:** Full developer and administrative privileges"
      " active."
  )
else:
  st.info(
      "🔬 **Developer View:** Active session authorized for system"
      " diagnostics and schema inspection."
  )

st.divider()

# =========================================================================
# TABS FOR THE DEVELOPER TOOLS (4 TABS)
# =========================================================================
# Instantiate a 4-tab interface incorporating health checks, schema inspection, active sessions, and custom testing.
dev_tab1, dev_tab2, dev_tab3, dev_tab4 = st.tabs([
    "🔌 API & Endpoint Health",
    "📦 JSON Schema & Category Inspector",
    "👤 Active Session & System Specs",
    "🧪 Custom API Test Console",
])

# -------------------------------------------------------------------------
# TAB 1: API & Endpoint Health Monitor
# -------------------------------------------------------------------------
with dev_tab1:
  st.subheader("Backend Endpoint Health Monitor")
  st.markdown(
      "Real-time status check for core backend API routes and database"
      " connectivity."
  )

  # Define critical backend REST routes to ping for availability.
  endpoints_to_check = ["/home", "/roles", "/requests"]

  col_h1, col_h2, col_h3 = st.columns(3)
  cols = [col_h1, col_h2, col_h3]

  # Loop through target endpoints, measuring latency and parsing HTTP status codes.
  for idx, ep in enumerate(endpoints_to_check):
    with cols[idx]:
      try:
        start_t = time.time()
        res = requests.get(f"{URL}{ep}", timeout=3)
        latency = round((time.time() - start_t) * 1000, 1)

        if res.status_code == 200:
          st.metric(
              label=f"Endpoint: `{ep}`", value="🟢 ONLINE", delta=f"{latency} ms"
          )
        else:
          st.metric(
              label=f"Endpoint: `{ep}`",
              value=f"⚠️ {res.status_code}",
              delta=f"{latency} ms",
          )
      except Exception:
        # Catch network timeouts or connection drops gracefully.
        st.metric(label=f"Endpoint: `{ep}`", value="🔴 OFFLINE", delta="Timeout")

  # Trigger a manual page script rerun to refresh real-time metrics.
  if st.button("🔄 Refresh Health Status", key="dev_refresh_health"):
    st.rerun()

# -------------------------------------------------------------------------
# TAB 2: JSON Schema & Category Inspector
# -------------------------------------------------------------------------
with dev_tab2:
  st.subheader("Category Schema & Structure Inspector")
  st.markdown(
      "Select any active data collection category to inspect its raw JSON"
      " payload and field rules."
  )

  # Fetch available database categories dynamically from the backend index.
  try:
    cat_list = requests.get(f"{URL}/home").json()
  except Exception:
    cat_list = []

  if not cat_list:
    st.info("No categories found to inspect.")
  else:
    inspect_sel = st.selectbox(
        "Select Category to Inspect:", cat_list, key="dev_schema_sel"
    )
    if inspect_sel:
      try:
        # Fetch and display the exact JSON settings schema for the selected category.
        cat_payload = requests.get(f"{URL}/settings/{inspect_sel}").json()
        st.json(cat_payload)
      except Exception:
        st.error("Failed to retrieve category schema from backend.")

# -------------------------------------------------------------------------
# TAB 3: Active Session, Database Metrics & Runtime Specs
# -------------------------------------------------------------------------
with dev_tab3:
  st.subheader("Active Session, Storage & Runtime Specs")
  st.markdown(
      "Inspect current user authentication metadata, database collection counts,"
      " and server runtime environment details."
  )

  c1, c2 = st.columns(2)
  with c1:
    st.markdown("##### 👤 User Metadata")
    st.write({
        "Email": getattr(user_obj, "email", "N/A"),
        "Name": getattr(user_obj, "name", "N/A"),
        "Is Logged In": is_logged_in,
        "Assigned Role": (
            "Admin"
            if is_admin
            else ("Developer" if is_dev else "Standard")
        ),
    })

    # Clear Cache Explanatory Note & Action Utility
    st.markdown(
        "> 💡 **What clearing the cache does:** Wipes all temporary browser"
        " memory variables in `st.session_state` (resetting form inputs,"
        " dropdown choices, and UI filters back to default) without deleting"
        " backend database records or logging you out."
    )

    if st.button("🗑️ Clear Local Session Cache", key="dev_clear_session"):
      for k in list(st.session_state.keys()):
        if k != "request_sent":
          del st.session_state[k]
      st.success("Session state cache successfully cleared.")
      st.rerun()

  with c2:
    st.markdown("##### 📦 Database Storage & Runtime Info")
    try:
      stats_data = requests.get(f"{URL}/home", timeout=3).json()
      st.metric("Total Active Categories / Tables", len(stats_data))
    except Exception:
      st.warning("Could not fetch database metrics from backend.")

    st.markdown("##### ⚙️ Runtime Environment Specs")
    st.write({
        "Python Version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "Streamlit Version": st.__version__,
        "Active Backend URL": URL,
    })

    st.markdown("##### Active Session Keys")
    st.write(list(st.session_state.keys()))

# -------------------------------------------------------------------------
# TAB 4: Custom API Test Console
# -------------------------------------------------------------------------
with dev_tab4:
  st.subheader("Custom API Request Console")
  st.markdown(
      "Send quick GET requests to any custom backend route and inspect raw JSON"
      " payloads instantly."
  )

  # Fetch active endpoints dynamically from FastAPI backend with fallback validation
  try:
    res = requests.get(f"{URL}/system/routes", timeout=3)
    fetched_data = res.json()
    available_endpoints = (
        fetched_data
        if isinstance(fetched_data, list)
        else ["/home", "/roles", "/requests"]
    )
  except Exception:
    available_endpoints = ["/home", "/roles", "/requests"]

  # Fetch category list dynamically for parameter filling
  try:
    cat_list = requests.get(f"{URL}/home", timeout=3).json()
    if not isinstance(cat_list, list):
      cat_list = []
  except Exception:
    cat_list = []

  # Initialize text input state if not present
  if "dev_custom_route_input" not in st.session_state:
    st.session_state["dev_custom_route_input"] = "/home"


  # Callback to synchronize selectbox choice to the text input box state
  def update_route_input():
    selected = st.session_state.get("dev_endpoint_preset")
    if selected and selected != "(Custom Input)":
      route_to_set = selected
      if ("{category}" in route_to_set or "{selection}" in route_to_set) and cat_list:
        route_to_set = route_to_set.replace("{category}", cat_list[0]).replace(
            "{selection}", cat_list[0]
        )
      st.session_state["dev_custom_route_input"] = route_to_set


  selected_preset = st.selectbox(
      "Quick Select Endpoint (Fetched from Server):",
      ["(Custom Input)"] + available_endpoints,
      key="dev_endpoint_preset",
      on_change=update_route_input,
  )

  # Dynamic parameter sub-selector for parameterized routes
  if selected_preset and (
      "{category}" in selected_preset or "{selection}" in selected_preset
  ):
    st.markdown("---")
    st.markdown("##### ⚙️ Parameter Builder")
    if cat_list:
      chosen_param = st.selectbox(
          "Select value for `{category}` / `{selection}`:",
          cat_list,
          key="dev_dynamic_param_helper",
      )
      if chosen_param:
        st.session_state["dev_custom_route_input"] = (
            selected_preset.replace("{category}", chosen_param).replace(
                "{selection}", chosen_param
            )
        )
    else:
      st.info(
          "No dynamic categories found on server to auto-populate parameters."
      )
    st.markdown("---")

  col_t1, col_t2 = st.columns([3, 1])
  with col_t1:
    custom_route = st.text_input(
        "Endpoint Route (appended to base URL):",
        key="dev_custom_route_input",
    )
  with col_t2:
    st.markdown("<br>", unsafe_allow_html=True)  # Visual alignment spacer
    test_submitted = st.button("🚀 Send Test Request", key="dev_send_test_req")

  if test_submitted:
    target_url = f"{URL}{custom_route}"
    try:
      start_time = time.time()
      response = requests.get(target_url, timeout=5)
      elapsed_ms = round((time.time() - start_time) * 1000, 1)

      col_stat1, col_stat2 = st.columns(2)
      with col_stat1:
        st.metric(
            label="Response Status",
            value=(
                f"🟢 {response.status_code}"
                if response.status_code == 200
                else f"⚠️ {response.status_code}"
            ),
        )
      with col_stat2:
        st.metric(label="Roundtrip Latency", value=f"{elapsed_ms} ms")

      st.markdown("##### Response Payload:")
      try:
        st.json(response.json())
      except Exception:
        st.text(response.text)
    except Exception as err:
      st.error(f"Failed to execute request against `{target_url}`: {err}")