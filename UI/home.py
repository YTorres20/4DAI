import requests
import streamlit as st
from key import URL

# Set page config for a wider layout
st.set_page_config(
    page_title="Collections Dashboard", page_icon="📊", layout="wide"
)

# =========================================================================
# PROFESSIONAL ENTERPRISE CUSTOM CSS STYLING
# =========================================================================
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
# 1. MAIN DASHBOARD CONTENT VIEW
# =========================================================================


def show_home_dashboard():
  st.session_state.category = None

  # Enterprise Header Section with Global Shortcuts (#3)
  col_title, col_actions = st.columns([2, 1])
  with col_title:
    st.title("Collections Overview")
    st.markdown(
        "<p style='color: #6B7280; margin-top: -10px;'>Select a database"
        " collection below to open its specific management form.</p>",
        unsafe_allow_html=True,
    )

  with col_actions:
    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
    # Quick shortcuts to jump straight to core app sections
    col_a, col_b, col_c = st.columns(3)
    with col_a:
      if st.button("📊 View"):
        st.switch_page(view_data_page)
    with col_b:
      if st.button("🎯 Robo"):
        st.switch_page(roboflow)
    with col_c:
      if st.button("⚙️ Config"):
        st.switch_page(settings_page)

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

  # Search and Sorting Toolbar controls (#1)
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

  # Apply Sorting
  categories.sort(reverse=(sort_order == "Reverse (Z-A)"))

  # Filter categories based on search input
  filtered_categories = [
      cat for cat in categories if search_query.lower() in cat.lower()
  ]

  # Dynamic Metrics Row
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

  # Professional 3-Column Grid Layout
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
            st.session_state.category = category_name
            st.switch_page(collection_page)


# =========================================================================
# 2. APP NAVIGATION ROUTER
# =========================================================================

home_page = st.Page(show_home_dashboard, title="Home", icon="🏠", default=True)
collection_page = st.Page(
    "pages/collection.py", title="Collection Form", visibility="hidden"
)
view_data_page = st.Page(
    "pages/view_data.py", title="View Collections", icon="📊"
)
settings_page = st.Page("pages/settings.py", title="Settings Manager", icon="⚙️")
roboflow = st.Page("pages/roboflow.py", title="RoboFlow", icon="🎯")
google_collab = st.Page("pages/googleCollab.py", title="Google Collab", icon="🚀")

pg = st.navigation([
    home_page,
    view_data_page,
    settings_page,
    collection_page,
    roboflow,
    google_collab,
])
pg.run()