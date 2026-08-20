import os
import shutil
import pandas as pd
from pymongo import MongoClient

### Packing up important files
items_to_move = [
    "images",
    "settings",
    "roboflow_settings",
    "requests.json",
    "roles.json"
]
for item in items_to_move:
    source_path = os.path.join("../Server", item)
    dest_path = "./"

    try:
        shutil.move(source_path, dest_path)
        print(f"Successfully moved: {item}")
    except FileNotFoundError:
        print(f"Skipped: '{item}' could not be found in '../Server'.")
    except PermissionError:
        print(f"Error: Permissions denied for '{item}' (it might be in use).")
    except Exception as e:
        print(f"An unexpected error occurred with '{item}': {e}")

try:
    os.makedirs("../../streamlit_bin", exist_ok=True)
    shutil.move("../UI/.streamlit", "../../streamlit_bin")
    print("Successfully moved: .streamlit")
except FileNotFoundError:
        print(f"Skipped: '.streamlit' could not be found in '../UI'.")
except PermissionError:
        print(f"Error: Permissions denied for '.streamlit' (it might be in use).")
except Exception as e:
        print("An unexpected error occurred with .streamlit ")

## mongoDB

print("Packing Up Database...")

client = MongoClient("mongodb://localhost:27017")
db = client["Collections"]

categories = os.listdir("settings/")

print(f"Packing up {len(categories)} categories...")

for category in categories:
    print(f"Packing up {category} collection")

    collection_name = category.replace(".json", "")
    table = db[collection_name]
    cursor = table.find({})

    chunk = []
    chunk_size = 50000
    file_exists = False 

    output_file = os.path.join(os.getcwd(), f"{collection_name}.parquet")

    if os.path.exists(output_file):
        os.remove(output_file)

    for document in cursor:
         chunk.append(document)

         if len(chunk) == chunk_size:
              data_frame = pd.DataFrame(chunk)
              data_frame.to_parquet(output_file, engine="fastparquet", append=file_exists)
              chunk = []
              file_exists = True 
              
    if chunk:
        data_frame = pd.DataFrame(chunk)
        data_frame.to_parquet(
            output_file, 
            engine="fastparquet", 
            append=file_exists
        )
        file_exists = True

    if file_exists:
        print(f"Successfully created: {output_file}")
    else:
        print(f"Skipped category - no documents found.")

print("Done packing up all categories!")  

print("Moving 'bin' out of the project...")

destination_outside = "../../bin_outside"

# Clear out any old destination first to prevent ghost files
if os.path.exists(destination_outside):
    try:
        shutil.rmtree(destination_outside)
    except Exception:
        pass

try:
    client.close()  
    shutil.move("../bin", destination_outside)
    print(f"Successfully moved 'bin' outside of the project to: {destination_outside}")

except FileNotFoundError:
    print("Error: Could not find the '../bin' directory to move.")
except PermissionError:
    print("OS Lock detected (Script is running inside 'bin').")
    print("Running corrected master fallback...")
    
    try:
        current_dir = os.path.abspath(".")
        os.makedirs(destination_outside, exist_ok=True)
        
        for item in os.listdir(current_dir):
            if item == os.path.basename(__file__):
                continue  # Leave the running script behind
            
            s = os.path.join(current_dir, item)
            d = os.path.join(os.path.abspath(destination_outside), item)
            
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
                
        print(f"All contents successfully forced into: {destination_outside}")
        
    except Exception as fallback_error:
        print(f"Master fallback failed: {fallback_error}")
            
except Exception as e:
    print(f"An unexpected error occurred while moving bin: {e}")