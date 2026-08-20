import os
import shutil
import pandas as pd
from pymongo import MongoClient

print("Starting unpacking and restoration process...")

destination_path = "../4DAI/Server"

if not os.path.isdir(destination_path):
    print("Project files do not exist")

exclude_files = ["unpack.py", "pack.py"]

files = os.listdir()

# 1. Move regular assets over to the server folder (forcing overwrites)
print("\nMoving project files to Server...")
for file in files:
    if file in exclude_files:
        continue

    if ".parquet" in file:
        continue

    dest_file_path = os.path.join(destination_path, file)
    
    # Just delete the old one if it's blocking the move
    if os.path.exists(dest_file_path):
        if os.path.isdir(dest_file_path):
            shutil.rmtree(dest_file_path)
        else:
            os.remove(dest_file_path)

    shutil.move(file, destination_path)
    print(f"Moved: {file}")


# 2. Rebuild MongoDB Database from clean Parquet files
print("\nRestoring MongoDB Database from Parquet files...")

client = MongoClient("mongodb://localhost:27017")
db = client["Collections"]

parquet_files = [f for f in os.listdir(".") if f.endswith(".parquet")]

if parquet_files:
    print(f"Found {len(parquet_files)} database collections to restore...")

    for file in parquet_files:
        category = file.replace(".parquet", "")
        print(f"Importing collection: {category}")

        table = db[category]
        table.delete_many({}) 

        df = pd.read_parquet(file, engine="fastparquet")
        records = df.to_dict(orient="records")
        
        if records:
            table.insert_many(records)
            print(f"Successfully imported {len(records)} documents into '{category}'.")

    print("Database restoration complete!")
else:
    print("No database parquet files found to import.")

client.close()

# 3. Move pack.py and unpack.py into a new 'bin' folder on the same level as Server
print("\nMoving script utilities into project 'bin' folder...")

new_bin_path = os.path.join("../4DAI", "bin")
os.makedirs(new_bin_path, exist_ok=True)

for script in ["pack.py", "unpack.py"]:
    if os.path.exists(script):
        shutil.copy(script, os.path.join(new_bin_path, script))
        print(f"Copied {script} to {new_bin_path}")

print("\nUnpack and deployment migration finished successfully!")