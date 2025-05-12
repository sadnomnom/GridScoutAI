import os
import shutil

# Create data folder inside your dashboard project
os.makedirs("data", exist_ok=True)

# Path to your exported GPKG (adjust this if needed)
source_path = r"C:\Users\Shimmy\Projects\GridScoutAI\GridScout_Final.gpkg"

# Destination inside the dashboard/data folder
dest_path = r"data\GridScout_Final.gpkg"

# Copy the file
shutil.copyfile(source_path, dest_path)

print("✅ GPKG copied to dashboard/data/")
