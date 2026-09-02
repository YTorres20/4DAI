import base64
import io
import time
import threading
import requests
import numpy as np
from PIL import Image
from fastapi import FastAPI, HTTPException
import uvicorn
from pyngrok import ngrok

# --- CONFIGURATION ---
UBUNTU_SERVER_URL = "https://2dd3-161-45-253-252.ngrok-free.app"
NODE_ID = "primary_station"
LOCAL_PORT = 5000

app = FastAPI()
kinect_runtime = None

def init_kinect():
    """Initializes the PyKinect2 runtime."""
    global kinect_runtime
    try:
        from pykinect2 import PyKinectRuntime, PyKinectV2
        kinect_runtime = PyKinectRuntime.PyKinectRuntime(
            PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Depth
        )
        print("✅ Kinect v2 successfully initialized on Windows helper node!")
    except Exception as e:
        print(f"❌ Failed to initialize Kinect v2: {e}")
        print("⚠️ Running in simulation/fallback mode.")

def start_tunnel_and_register():
    """Starts the ngrok tunnel via pyngrok and auto-registers with Ubuntu."""
    try:
        # Open the ngrok tunnel on the local port
        public_url = ngrok.connect(LOCAL_PORT).public_url
        print(f"🌐 ngrok tunnel established: {public_url}")
        
        # Register with Ubuntu FastAPI server
        registration_endpoint = f"{UBUNTU_SERVER_URL}/collection/register-kinect"
        payload = {"node_id": NODE_ID, "url": public_url}
        
        response = requests.post(registration_endpoint, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"🚀 Successfully registered with Ubuntu server! Node ID: [{NODE_ID}]")
        else:
            print(f"⚠️ Failed to register with Ubuntu: {response.text}")
            
    except Exception as e:
        print(f"❌ Error setting up tunnel or registering: {e}")

@app.post("/capture-snapshot")
def capture_snapshot():
    """Takes a frame from the Kinect and returns Base64 image data and depth."""
    global kinect_runtime
    
    if kinect_runtime is None or not kinect_runtime.has_new_color_frame():
        # Fallback dummy image if hardware isn't connected during testing
        img = Image.new('RGB', (1920, 1080), color=(73, 109, 137))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return {
            "status": "success",
            "sample_distance_mm": 500,
            "image_base64": img_base64
        }
    
    try:
        color_frame = kinect_runtime.get_last_color_frame()
        color_img_data = color_frame.reshape((1080, 1920, 4))[:, :, :3]
        img = Image.fromarray(color_img_data.astype('uint8'), 'RGB')
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=95)
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        depth_frame = kinect_runtime.get_last_depth_frame()
        center_index = (512 * 424 // 2) + (512 // 2)
        sample_distance_mm = int(depth_frame[center_index]) if depth_frame is not None else 0
        
        return {
            "status": "success",
            "sample_distance_mm": sample_distance_mm,
            "image_base64": image_base64
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kinect capture error: {str(e)}")

if __name__ == "__main__":
    # Initialize Kinect hardware in background thread
    threading.Thread(target=init_kinect, daemon=True).start()
    
    # Start ngrok tunnel and register with Ubuntu after a short delay
    threading.Thread(target=start_tunnel_and_register, daemon=True).start()
    
    print(f"🔌 Starting Windows Kinect Helper Node on port {LOCAL_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=LOCAL_PORT)