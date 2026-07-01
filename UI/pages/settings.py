import streamlit as st 
from key import URL 
import requests 
import time 

st.title ("Settings")
st.divider()
st.subheader("Add Category")


category_name = st.text_input("Category Name:")

if "prompts" not in st.session_state:
    st.session_state.prompts = []

prompt = st.text_input("Add Prompt:")
selection = st.selectbox(
                    "How should this field be displayed:",
                    ["Text Box", 
                    "Text Area (multi-line)", 
                    "Number Input", 
                    "Dropdown List", 
                    "Radio Button", 
                    "Check Box", 
                    "Slider"])
    
settings = {
            "selection": selection, 
            "prompt": prompt 
            }
    
        
if selection == "Number Input" or selection == "Slider":

    settings["max"]= st.number_input("Enter max value:")
    settings["min"] = st.number_input("Enter min value:")

elif selection == "Dropdown List" or selection == "Radio Button" or selection == "Check Box":
    settings["options"] = st.text_input("Enter options (comma separated):")

if st.button("Add"):
    if not prompt.strip():
        st.error("Please enter a name for the prompt before adding.")
    elif (selection in ["Dropdown List", "Radio Button", "Check Box"]) and not settings.get("options", "").strip():
        st.error(f"Please enter options for the {selection}.")
    else:
        st.session_state.prompts.append(settings)
        st.rerun()

            
st.divider()

kinect = st.radio("Use of Kinect camera:",["True", "False"],key="kinect_camera")

st.divider()

roboflow = st.selectbox("Enable Automatic Roboflow Upload",["False","True"], key="roboflow")

if roboflow == "True":
    api_key = st.text_input("Please Input RoboFlow API Key:", type="password", key="api_key")
    workspace = st.text_input ("Please Input Workspace:", key="workspace")
    project_id = st.text_input("Please Input Project ID:", key="project_id")

    if api_key and workspace and project_id:
        try:
            roboflow_response = requests.get(f"https://api.roboflow.com/{workspace}/{project_id}", params={"api_key":api_key})
        
            if roboflow_response.status_code == 200:
                st.success("Credentials verified successfully!")
                roboflow_settings = {"api_key":api_key, "workspace":workspace, "project_id": project_id}
            else:
                st.error("Invalid Credentials")
                roboflow_settings = "False"
        except:
            st.error("Network Connection Failed.")
            roboflow_settings = "False"
else:
    roboflow_settings = "False"


st.divider()

st.subheader("Current Prompts")

for count, prompt in enumerate(st.session_state.prompts):
    col1, col2 = st.columns([4,1])

    with col1:
        st.write(f"{count+1}. {prompt}")

    with col2:
         if st.button("Delete",key=f"delete_key{count}"):
            st.session_state.prompts.pop(count)

if st.button("Confirm"):
    page = {
       "category" : category_name,
       "prompts":[prompt for prompt in st.session_state.prompts],
       "camera": kinect,
       "roboflow": roboflow_settings

   }

    response = requests.post(
        f"{URL}/settings",
        json=page
    )
   
    st.session_state.prompts = []

    # Display your clean confirmation message
    st.success("The settings have been added and everything is good!")
    
    # Wait 2 seconds so they can read the message before st.rerun clears it
    time.sleep(3)
    st.rerun()
    st.rerun()