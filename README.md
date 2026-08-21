# Dynamic Data Collection Platform
Live Application Access: https://shaded-unlighted-dribble.ngrok-free.dev

## Overview

The Dynamic Data Collection Platform is a web-based application designed to create, manage, and collect custom datasets through dynamically generated forms and image capture.

The system consists of:

- Streamlit frontend for user interaction
- FastAPI backend for data storage and retrieval
- MongoDB database for sample and image metadata
- Optional Roboflow integration for dataset synchronization

Unlike traditional collection systems that are limited to specific data types, this platform allows users to create their own collection categories, define custom prompts, capture multiple images per sample, and optionally synchronize collected data with Roboflow.

## Key Capabilities

- Custom category creation
- Dynamic form generation
- Multiple image capture per sample
- MongoDB data storage
- Image management and downloads
- Date-based filtering
- Roboflow integration
- Category editing and management

## Technologies Used

### Frontend

Streamlit

### Backend

FastAPI  
Uvicorn

### Database

MongoDB

### Networking / Deployment

ngrok (optional remote access)

### Programming Language

Python 3.10+

## Installation References

### MongoDB

MongoDB can be installed using the official MongoDB documentation:

https://www.mongodb.com/docs/manual/installation/

### ngrok

ngrok can be installed and configured using:

https://ngrok.com/docs/getting-started/

## Project Structure

```
project/
│
├── Server/
│   ├── main.py
│   ├── images/
│   │   └── category_name/
│   │       └── sample_id/
│   │
│   └── settings/
│       └── category.json
├── bin/
│
├── UI/
│   ├── home.py
│   ├── key.py
│   └── pages/
│       ├── collection.py
│       ├── developer_lab.py
│       ├── googleCollab.py
│       ├── roboflow.py
│       ├── settings.py
│       └── view_data.py
│
├── requirements.txt
└── README.md
```

## Utility Scripts (`bin/`)

The `bin/` directory contains helper scripts designed to support project portability, codebase updates, and environment migration:

- **`pack.py`**: Bundles project configuration files, settings schemas, and local asset/image directories into a compressed archive. This ensures seamless transfer of state, metadata, and database information whether you are migrating data to a new server or deploying across separate host machines.
- **`unpack.py`**: Extracts and restores previously packed dataset or configuration archives directly into the correct workspace directories on the target environment.

### Deployment & Migration Flexibility

These utility scripts make it straightforward to adapt the application architecture depending on your hosting setup:
- **Single Machine Mode:** Frontend and backend run locally on the same host, sharing access to local storage directories.
- **Distributed Machine Mode:** The FastAPI backend and Streamlit frontend are hosted on separate machines, utilizing `pack.py` and `unpack.py` to transfer configuration states, schemas, and asset bundles cleanly between environments.

> **Note on `UI/key.py` Configuration:** When running in Distributed Machine Mode (where the frontend and backend are on separate machines), you must update `UI/key.py` with the network address or public IP of the new machine hosting the server so the Streamlit UI can successfully communicate with the FastAPI backend.
---
## Features

### Category Management

The Settings page allows users to create and manage custom collection categories.

Users can:

- Create unlimited categories
- Define custom prompts for each category
- Edit existing categories
- Delete prompt fields
- Add new prompt fields to existing categories
- Configure camera settings
- Configure Roboflow integration
- Save category configurations

Category configurations are stored as JSON files on the server.

```
settings/
├── Vegetables.json
├── Soil_Moisture.json
├── Plant_Health.json
└── ...
```

### Dynamic Form Generation

Collection forms are generated automatically from each category's configuration.

Supported prompt types include:

- Text Box
- Text Area (multi-line)
- Number Input
- Dropdown List
- Radio Button
- Slider

Validation is performed to ensure that prompt configurations are properly defined before categories can be saved.

### Data Collection

Users can:

- Select a collection category.
- Complete the category-specific form.
- Capture images directly from their browser.
- Attach multiple images to a single sample.
- Submit metadata and images together.

Each submission automatically receives a unique Sample ID.

### Image Management

Images are organized by category and Sample ID.

```
images/
├── Category_A/
│   └── sample_id/
│       ├── image_1.jpg
│       ├── image_2.jpg
│       └── ...
│
└── Category_B/
    └── sample_id/
```

Each image receives a unique Image ID and is linked to its associated sample.

### Roboflow Integration

The platform includes optional integration with Roboflow.

When enabled for a category, users can configure:

- Roboflow API Key
- Workspace Name
- Project ID

The application validates the provided credentials before saving the configuration.

#### Sample Submission

During sample submission:

- Images are automatically uploaded to Roboflow.
- Metadata is attached to each uploaded image.
- Metadata includes the Sample ID and collected form responses.

This allows datasets collected through the platform to be synchronized directly with Roboflow projects.

### Data Viewing

The View Collections page allows users to browse and review collected data.

Features include:

- Category selection
- Date-range filtering
- Viewing sample information
- Viewing collected form responses
- Viewing all images associated with a sample
- Downloading individual images

Collected records are displayed in expandable sections for easier navigation.

## Link Behaviors & Cloud Authentication

### 1. Roboflow Dataset Ingestion Queue

Images uploaded through the application's API pipeline are ingested into Roboflow's isolated staging and unassigned batch queues.

Direct web links cannot force Roboflow's interface to bypass this holding queue.

Unless a user is logged into the correct Roboflow account that owns the project workspace and navigates past the staging queue, newly uploaded images may not immediately appear in the main dataset view.

### 2. Google Session Authentication & Colab Links

Google's browser security rules prevent external web links from overriding active browser session cookies or automatically forcing a specific target email account.

When users click links to Google Colab or other external Google resources, the browser defaults to whichever Google account is currently active in that browser session.

Team members should ensure that they are signed into the correct research credentials before opening notebooks.

An account-chooser link is provided directly in the application to help users switch profiles quickly.

## Database Structure

MongoDB stores sample information and image metadata across dedicated collections.

### Database Collections

```
Collections
├── images
├── category_1
├── category_2
├── category_3
└── ...
```

### Category Collections

Each category created through the Settings page becomes its own MongoDB collection.

These collections store:

- Form submissions
- Sample information
- Category-specific metadata

### Images Collection

The images collection centrally tracks metadata and references for captured images associated with project samples.

## Installation

### 1. Clone Repository

```
git clone <repository-url>
cd project
```

### 2. Create a Virtual Environment

#### Option A: Python venv

##### macOS / Linux

```
python3 -m venv app
source app/bin/activate
```

##### Windows

```
python -m venv app
app\Scripts\activate
```

#### Option B: Conda

Ubuntu / Linux / macOS / Windows:

```
conda create -n app python=3.10
conda activate app
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

## MongoDB Setup

Install MongoDB and start the MongoDB service.

Verify the installation:

```
mongosh
```

MongoDB runs locally by default at:

```
mongodb://localhost:27017
```

## Running the Backend Server

Navigate to the Server directory:

```
cd Server
```

Start FastAPI with Uvicorn:

```
uvicorn main:app --host 0.0.0.0 --port 8000
```

The backend will be available at:

```
http://127.0.0.1:8000
```

## Optional: Exposing the Backend with ngrok

If the frontend and backend are running on different machines, the backend can be exposed using ngrok:

```
ngrok http 8000
```

Example output:

```
Forwarding https://xxxx.ngrok-free.app -> http://localhost:8000
```

Update the frontend API URL in:

```
# UI/key.py

URL = "https://xxxx.ngrok-free.app"
```

## Running the Streamlit Frontend

Navigate to the UI directory:

```
cd UI
```

Run Streamlit:

```
streamlit run home.py
```

The frontend will be available at:

```
http://localhost:8501
```
## API Endpoints

### Category Configuration

#### Get Available Categories

```
GET /home
```

#### Get Category Configuration

```
GET /settings/{category}
```

#### Create or Update Category Configuration

```
POST /settings
```

### Sample Management

#### Create Sample Submission

```
POST /collection/submission
```

#### Upload Sample Image

```
POST /collection/images/upload
```

#### Retrieve Samples for a Category

```
GET /collection/samples/{category}
```

### Image Management

#### Retrieve Images for a Sample

```
GET /collection/images/{sample_id}
```

#### Retrieve a Specific Image

```
GET /collection/image/{image_id}
```

## Author

Yarely Torres
