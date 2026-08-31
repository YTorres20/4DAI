from datetime import datetime
import streamlit as st
import requests
from key import URL

# --- AUTH & USER INFO SETUP ---
user_obj = getattr(st, "user", None) or getattr(st, "experimental_user", None)
is_logged_in = user_obj and getattr(user_obj, "is_logged_in", False)
user_email = getattr(user_obj, "email", "Anonymous")
user_name = getattr(user_obj, "name", "Unknown User")

st.title("💬 System Feedback")
st.write("We would love to hear your thoughts, bug reports, or feature suggestions!")

# --- FEEDBACK FORM ---
with st.form("feedback_form", clear_on_submit=True):
    feedback_category = st.selectbox(
        "Feedback Type:",
        ["General Comment", "Bug Report", "Feature Request", "UI/UX Improvement"]
    )
    
    feedback_message = st.text_area(
        "Your Message:",
        placeholder="Tell us what's working or what we can improve..."
    )
    
    submit_feedback_btn = st.form_submit_button("Submit Feedback")

    if submit_feedback_btn:
        if feedback_message.strip():
            payload = {
                "email": user_email,
                "name": user_name,
                "category": feedback_category,
                "message": feedback_message,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            try:
                res = requests.post(f"{URL}/feedback", json=payload)
                if res.status_code in [200, 201]:
                    st.success("Thank you! Your feedback has been submitted successfully.")
                else:
                    st.error("Failed to submit feedback to the server.")
            except Exception as e:
                st.error(f"Connection error: {e}")
        else:
            st.error("Please write a message before submitting.")


try:
    roles = requests.get(f"{URL}/roles").json()
except Exception:
    roles = {}

is_admin = user_email in roles.get("admin", [])
is_dev = user_email in roles.get("developer", [])

if is_admin or is_dev:
    st.divider()
    st.subheader("👑 Admin and 🔬 Developer Dashboard: User Feedback Log")
    
    try:
        feedback_list = requests.get(f"{URL}/feedback").json()
        if feedback_list:
            for item in reversed(feedback_list): # Show newest first
                with st.container(border=True):
                    # Use columns to position the delete button on the far right
                    col1, col2 = st.columns([9, 1])
                    
                    with col1:
                        st.markdown(f"**Category:** {item.get('category')} | **From:** {item.get('name')} ({item.get('email')})")
                        st.caption(f"Submitted on: {item.get('date')}")
                        st.write(item.get('message'))
                        
                    with col2:
                        # Only allow Admins to delete, or let Devs delete too depending on preference
                        if is_admin:
                            if st.button("🗑️ Delete", key=f"del_fb_{item.get('id')}", help="Delete feedback"):
                                try:
                                    res = requests.delete(f"{URL}/feedback/remove", json={"id": item.get('id')})
                                    if res.status_code == 200:
                                        st.success("Deleted!")
                                        st.rerun()
                                    else:
                                        st.error("Failed.")
                                except Exception as e:
                                    st.error(f"Error: {e}")
        else:
            st.info("No feedback submitted yet.")
    except Exception:
        st.write("Could not load feedback logs.")