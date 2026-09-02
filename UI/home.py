from datetime import date
import requests
import streamlit as st
from key import URL

# Set page config for a wider layout
st.set_page_config(
    page_title="Collections Dashboard", page_icon="📊", layout="wide"
)

st.markdown(
    """
    <style>
        .main {
            background-color: #F8F9FA;
        }
        .stButton button {
            width: 100%;
            background-color: #FFFFFF;
            color: #1F2937;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            font-weight: 500;
            padding: 8px 12px;
            transition: all 0.2s ease-in-out;
        }
        .stButton button:hover {
            background-color: #F3F4F6;
            border-color: #9CA3AF;
            color: #111827;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# =========================================================================
# SERVER OFFLINE & HEALTH CHECK
# =========================================================================
try:
  roles_response = requests.get(f"{URL}/roles", timeout=5)
  if roles_response.status_code == 200:
    roles = roles_response.json()
  else:
    roles = {}
except Exception:
  roles = {}

if not roles:
  st.error("🚨 **System Offline / Server Unreachable**")
  st.warning(
      "We are currently unable to connect to the backend server. All database"
      " collections, workflows, and administrative features are temporarily"
      " locked until connection is restored."
  )
  st.info(
      "Please check your network connection or try again later. If the issue"
      " persists, contact your system administrator."
  )
  st.stop()


@st.dialog("🔒 Authentication Required")
def login_dialog():
  st.warning("Please sign in with Google to access collections and workspaces.")
  if st.button("🔵 Sign in with Google", type="primary", use_container_width=True):
    try:
      st.login()
    except Exception as e:
      st.error(f"Login failed: {e}")
  st.stop()


@st.dialog("⚠️ Access Request Required")
def request_access_dialog(user_email, user_name):
  st.warning(f"Your email (**{user_email}**) is not registered in the system.")
  st.markdown(
      "You need permissions from an administrator to access protected pages"
      " and collections. You can send a request below."
  )

  if "request_sent" not in st.session_state:
    st.session_state.request_sent = False

  if st.session_state.request_sent:
    st.success(
        "✅ Access request sent successfully! An administrator will review it."
    )
    if st.button("🚪 Logout", use_container_width=True):
      st.logout()
    st.stop()

  reason = st.text_area(
      "Reason for request (optional):",
      placeholder="Explain why you need access...",
  )

  if st.button(
      "📩 Send Access Request", type="primary", use_container_width=True
  ):
    payload = {
        "name": user_name,
        "email": user_email,
        "reason": reason,
        "date": str(date.today()),
    }
    try:
      resp = requests.post(f"{URL}/request", json=payload)
      if resp.status_code in [200, 201]:
        st.session_state.request_sent = True
        st.rerun()
      else:
        st.error(f"Failed to submit request. Server error: {resp.status_code}")
    except Exception as e:
      st.error(f"Network error while sending request: {e}")

  if st.button("🚪 Logout", use_container_width=True):
    st.logout()

  st.stop()


def check_user_access():
  """Safely checks login status and matches email against backend /roles."""
  user_obj = getattr(st, "user", None) or getattr(
      st, "experimental_user", None
  )

  if not user_obj or not getattr(user_obj, "is_logged_in", False):
    login_dialog()

  user_email = getattr(user_obj, "email", "")
  user_name = getattr(user_obj, "name", "Unknown User")

  is_admin = user_email in roles.get("admin", [])
  is_dev = user_email in roles.get("developer", [])
  is_collector = user_email in roles.get("collector", [])

  if is_admin:
    return "Admin"
  elif is_dev:
    return "Developer"
  elif is_collector:
    return "Data Collector"
  else:
    request_access_dialog(user_email, user_name)
    return "Guest"


# =========================================================================
# 1. MAIN DASHBOARD CONTENT VIEW
# =========================================================================


def show_home_dashboard():
  st.session_state.category = None

  user_obj = getattr(st, "user", None) or getattr(
      st, "experimental_user", None
  )
  is_logged_in = user_obj and getattr(user_obj, "is_logged_in", False)
  user_name = getattr(user_obj, "user_name", None) or getattr(
      user_obj, "name", "Guest"
  )
  user_email = getattr(user_obj, "email", "")

  # =========================================================================
  # MODERN TOP-RIGHT HEADER & ACCOUNT TOOLBAR
  # =========================================================================
  top_col1, top_col2 = st.columns([7, 1])
  with top_col1:
    st.title("Collections Overview")
    if is_logged_in:
      st.markdown(
          f"<p style='color: #6B7280; margin-top: -10px;'>Welcome back,"
          f" <b>{user_name}</b></p>",
          unsafe_allow_html=True,
      )
    else:
      st.markdown(
          "<p style='color: #6B7280; margin-top: -10px;'>Select a database"
          " collection below to open its specific management form.</p>",
          unsafe_allow_html=True,
      )

  with top_col2:
    with st.container():
      if is_logged_in:
        st.markdown(
            f"<div style='text-align: right; font-size: 0.85rem; color: #374151;"
            f" line-height: 1.2;'><b>{user_name}</b><br><span"
            f" style='color: #6B7280; font-size: 0.75rem;'>{user_email}</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown("""
          <style>
          /* Target only the button with the key 'my_unique_btn' */
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
        if st.button("🚪 Logout", key="top_logout_btn"):
          for key in list(st.session_state.keys()):
            del st.session_state[key]
          st.logout()
      else:
        if st.button("🔵 Sign in with Google", key="top_login_btn", type="primary"):
          try:
            st.login()
          except Exception as e:
            st.error(f"Login failed: {e}")

  st.divider()

  # Quick action buttons row
  col_actions_space, col_actions = st.columns([2, 1])
  with col_actions_space:
    col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)

    with col_a:
      if st.button("📊 View"):
        if not is_logged_in:
          login_dialog()
        else:
          role = check_user_access()
          if role:
            st.switch_page(view_data_page)

    with col_b:
      if st.button("🎯 Robo"):
        if not is_logged_in:
          login_dialog()
        else:
          role = check_user_access()
          if role:
            st.switch_page(roboflow)

    with col_c:
      if st.button("⚙️ Config"):
        if not is_logged_in:
          login_dialog()
        else:
          role = check_user_access()
          if role in ["Admin", "Developer"]:
            st.switch_page(settings_page)
          else:
            st.error("Access Denied: Config is restricted to Admins & Developers.")
    with col_d:
      if st.button("🚀 Google"):
        if not is_logged_in:
          login_dialog()
        else:
          role = check_user_access()
          if role:
            st.switch_page(google_colab)
    with col_e:
      if st.button("🛠️ Developer"):
        if not is_logged_in:
          login_dialog()
        else:
          role = check_user_access()
          if role:
            st.switch_page(developer_lab_page)
    with col_f:
      if st.button("📝 Tutorials"):
        if not is_logged_in:
          login_dialog()
        else:
          role = check_user_access()
          if role:
            st.switch_page(tutorial_page)
        

  try:
    response = requests.get(f"{URL}/home")
    categories = response.json()
  except Exception:
    categories = []

  if not categories:
    st.warning("No categories found or server unreachable.")
    st.stop()

  total_categories = len(categories)
  st.markdown("---")

  filter_col, sort_col = st.columns([3, 1])
  with filter_col:
    search_query = st.text_input(
        "Filter collections...",
        placeholder="Type to search database collections...",
        label_visibility="collapsed",
    )
  with sort_col:
    sort_order = st.selectbox(
        "Sort Order",
        ["Alphabetical (A-Z)", "Reverse (Z-A)"],
        label_visibility="collapsed",
    )

  categories.sort(reverse=(sort_order == "Reverse (Z-A)"))
  filtered_categories = [
      cat for cat in categories if search_query.lower() in cat.lower()
  ]

  m1, m2, m3 = st.columns(3)
  with m1:
    st.metric(label="Total Database Collections", value=total_categories)
  with m2:
    st.metric(label="Backend Status", value="Connected", delta="Online")
  with m3:
    st.metric(
        label="Showing Results",
        value=f"{len(filtered_categories)} of {total_categories}",
    )

  st.write("")
  st.subheader("Available Database Collections")

  if not filtered_categories:
    st.info("No matching collections found.")
    st.stop()

  GRID_COLUMNS = 3
  rows = [
      filtered_categories[i : i + GRID_COLUMNS]
      for i in range(0, len(filtered_categories), GRID_COLUMNS)
  ]

  for row in rows:
    cols = st.columns(GRID_COLUMNS)
    for index, category_name in enumerate(row):
      with cols[index]:
        with st.container(border=True):
          st.markdown(f"#### 🗄️ {category_name}")
          st.markdown(
              f"<p style='color: #4B5563; font-size: 0.85rem; min-height:"
              f" 40px;'>Opens the collection form and management workspace for <b>{category_name}</b>.</p>",
              unsafe_allow_html=True,
          )

          if st.button(
              f"Open {category_name} Collection", key=f"btn_prof_{category_name}"
          ):
            if not is_logged_in:
              login_dialog()
            else:
              role = check_user_access()
              if role and role != "Guest":
                st.session_state.category = category_name
                st.switch_page(collection_page)


# =========================================================================
# 2. APP NAVIGATION ROUTER
# =========================================================================

home_page = st.Page(show_home_dashboard, title="Home", icon="🏠", default=True)
collection_page = st.Page("pages/collection.py", title="Collection Form", visibility="hidden")
view_data_page = st.Page("pages/view_data.py", title="View Collections", icon="📊")
settings_page = st.Page("pages/settings.py", title="Settings Manager", icon="⚙️")
roboflow = st.Page("pages/roboflow.py", title="RoboFlow", icon="🎯")
google_colab = st.Page("pages/googleColab.py", title="Google Collab", icon="🚀")
developer_lab_page = st.Page("pages/developer_lab.py", title="Developer Lab", icon="🛠️")
tutorial_page = st.Page("pages/tutorial.py", title="Tutorials", icon="📝")
feedback_page = st.Page("pages/feedback.py", title="Feedback",icon="✏️")

active_page = st.navigation([
    home_page,
    view_data_page,
    settings_page,
    collection_page,
    roboflow,
    google_colab,
    developer_lab_page,
    tutorial_page,
    feedback_page
])

user_obj = getattr(st, "user", None) or getattr(st, "experimental_user", None)
is_logged_in = user_obj and getattr(user_obj, "is_logged_in", False)

if active_page.title != "Home" and not is_logged_in:
  login_dialog()
active_page.run()