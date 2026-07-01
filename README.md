# Soil and Vegetable Monitoring System

## Overview

The Soil and Vegetable Monitoring System is a web-based application designed to collect, store, and manage vegetable and soil sample data. The system provides a Streamlit user interface for data collection and a FastAPI backend (Server) for data storage and retrieval.

The application supports:

* Vegetable data collection
* Soil data collection
* Image uploads for samples
* MongoDB data storage
* Querying and viewing collected data


<img src= "Assets/new_image1.png" height= "500" width= "700">
---

## Technologies Used

### Frontend

* Streamlit

### Backend (Server)

* FastAPI
* Uvicorn

### Database

* MongoDB

### Networking / Deployment 
- ngrok (for remote access)

### Programming Language

* Python 3.10+

---
## Installation References
- MongoDB

Installed using the official MongoDB installation guide:
https://www.mongodb.com/docs/manual/installation/

- ngrok

Installed and configured using:
https://ngrok.com/docs/getting-started/

---

## Project Structure

```text
project/
│
├── Server/
│   ├── main.py
│   ├── images/
│   │   └── category_name/
│   │       └── sample_id/
│   │
│   └── settings/
│       └── category_settings.json
│
├── UI/
│   ├── home.py
│   ├── key.py
│   └── pages/
│       ├── settings.py
│       ├── collection.py
│       └── view_data.py
│
├── requirements.txt
└── README.md
```

---

## Features

### Settings Management

The Settings page allows users to create and manage collection categories.
Users can:

- Create unlimited categories
- Define custom prompts for each category
- Select input types for prompts
- Save category configurations
- Store category settings as JSON files
- Category configurations are stored on the server in:
```
Server/
└── settings/
    └── *.json
```

<img src= "Assets/new_image2.png" height= "500" width= "700">


---
### Dynamic Data Collection
collection forms are automatically generated from the selected category settings.

Supported prompt types include:
- Text Box
- Number Input
- Date Input
- Dropdown Selection
- Text Area
- Additional custom prompt types

Users can:
- Select a category
- omplete category-specific prompts
- Upload sample images
- Submit sample data

---
### Roboflow Integration
The Settings page includes optional integration with Roboflow.

When creating or editing a category, users can choose to enable Roboflow integration. If enabled, the application prompts the user to enter:
- Roboflow API Key
- Workspace Name
- Project ID

These settings are stored within the category's configuration file and can be used by future application features that interact with Roboflow services.



## Image Storage

Images are stored by sample and type:

```text
images/
├── vegetables/
│   └── sample_id/
│
└── soils/
    └── sample_id/
```

Each image is assigned a unique image ID and linked to a `sample_id`.

---
### Data Viewing
The View Data page allows users to browse and filter collected information.

Users can:
- Filter by category
- Filter by collection date
- View sample IDs
- View image IDs
- View collected prompt information
- Browse stored sample records
- Download Images
---

## Installation

### Clone Repository

```bash
git clone <repository-url>
cd project
```

### Create Virtual Environment

Mac/Linux:

```bash
python3 -m venv app
source app/bin/activate
```

Windows:

```bash
python -m venv app
app\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## MongoDB Setup

Install MongoDB and start the service.

Verify it is running:

```bash
mongosh
```

### Database Configuration

MongoDB is configured in:

```python
# Server/db.py

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

db = client["Collections"]

vegetable_collections = db["vegetable"]
soil_collections = db["soil"]
image_collections = db["images"]
```

### Database Name

* Collections

### Collections

* vegetable
* soil
* images

---

## Running the Server (FastAPI)

Navigate to the Server directory:

```bash
cd Server
```

Start the server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Server runs at:

```
http://127.0.0.1:8000
```
---
## Exposing Backend (ngrok)
Because the frontend runs on a different machine, the backend is exposed using ngrok.

Start tunnel:
```bash
ngrok http 8000
```
Example output:
```
Forwarding https://xxxx.ngrok-free.app -> http://localhost:8000

```

Note: The ngrok URL changes whenever the tunnel is restarted. Update `UI/key.py` with the new URL before running the Streamlit application.

---

## UI Configuration
The Streamlit UI connects to the server using:

Update Streamlit configuration:
```python
# UI/key.py

URL = "https://xxxx.ngrok-free.app"
```

---

## Running the Streamlit UI

Navigate to UI directory:

```bash
cd UI
streamlit run home.py
```

UI runs at:

```
http://localhost:8501
```

---

## API Endpoints

### Create Vegetable Sample

```
POST /vegetables
```

### Create Soil Sample

```
POST /soils
```

### Upload Image

```
POST /images
```

Form Data:

* sample_id
* mode (vegetable | soil)
* file

---

### Get All Data

```
GET /data
```

---

## Future Improvements

* Remote camera integration
* Data analytics dashboard
* Automated plant health detection
* Machine learning image classification

---

## Author

Yarely Torres

