# This code is used to calculate the fraction of cropland area for major crops in terms of total cropland

import os
import numpy as np
import xarray as xr

# Define paths
input_path = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/SPAM/SPAM2010_HA_nc"
output_path = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/SPAM/SPAM2010_HA_nc"

# Define main crops
main_crops = ["RICE", "WHEA", "MAIZ", "SOYB"]

# Get all the crop files
all_nc_files = [f for f in os.listdir(input_path) if f.endswith("_Harvest_Area_05d.nc")]
all_crops = [f.split("_")[0] for f in all_nc_files]

print(f"Found {len(all_nc_files)} crop netCDF files")

# Check if main crops exist in the data
for crop in main_crops:
    if f"{crop}_Harvest_Area_05d.nc" not in all_nc_files:
        print(f"Warning: Main crop {crop} not found in dataset")

# Function to calculate harvest area (Harvest Area * harvest Proportion)
def calculate_harvest_area(file_path):
    try:
        ds = xr.open_dataset(file_path)
        
        # Check if required variables exist
        if "Harvest_Area" not in ds:
            print(f"Error: Required variables missing in {file_path}")
            return None
        
        # Calculate harvest area
        harvest_area = ds["Harvest_Area"]
        
        # Replace NaN with 0 for proper summation
        harvest_area = harvest_area.fillna(0)
        
        # Get lat/lon coordinates for later
        if "lat" in ds.dims and "lon" in ds.dims:
            lats = ds.lat.values
            lons = ds.lon.values
        else:
            print(f"Warning: Expected dimensions not found in {file_path}")
            return None
            
        ds.close()
        return harvest_area, lats, lons
        
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return None

# Initialize arrays to store sums
main_crop_harvest_area = None
all_crop_harvest_area = None
lats = None
lons = None

# Dictionary to store individual main crop harvest areas
main_crop_data = {}

# First, process all crops to get total harvest area
print("Calculating total harvest area for all crops...")
for crop in all_crops:
    file_path = os.path.join(input_path, f"{crop}_Harvest_Area_05d.nc")
    
    result = calculate_harvest_area(file_path)
    if result is None:
        continue
        
    harvest_area, crop_lats, crop_lons = result
    
    # Store coordinates from first file
    if lats is None:
        lats = crop_lats
        lons = crop_lons
    
    # Initialize or add to the sum
    if all_crop_harvest_area is None:
        all_crop_harvest_area = harvest_area
    else:
        all_crop_harvest_area += harvest_area
    
    # Store individual main crop data and add to main crop sum
    if crop in main_crops:
        # Store the individual main crop data
        main_crop_data[crop] = harvest_area
        
        # Also add to main crop sum
        if main_crop_harvest_area is None:
            main_crop_harvest_area = harvest_area
        else:
            main_crop_harvest_area += harvest_area
        print(f"Added {crop} to main crop sum")

# Check if we have valid data
if main_crop_harvest_area is None or all_crop_harvest_area is None:
    print("Error: Could not calculate harvest areas")
    exit(1)

# Handle missing main crops by creating zero arrays
for crop in main_crops:
    if crop not in main_crop_data:
        print(f"Creating zero array for missing crop: {crop}")
        main_crop_data[crop] = xr.zeros_like(all_crop_harvest_area)

# Calculate the fraction: main_crops / all_crops
print("Calculating main crop fraction...")
# Avoid division by zero by creating a mask
mask = (all_crop_harvest_area > 0)
main_crop_fraction = xr.zeros_like(all_crop_harvest_area)
main_crop_fraction = main_crop_fraction.where(~mask, main_crop_harvest_area / all_crop_harvest_area)

# Create a dataset with variables for each main crop
dataset_dict = {
    "Main_Crop_harvest_Area": (["lat", "lon"], main_crop_harvest_area.values),
    "All_Crop_harvest_Area": (["lat", "lon"], all_crop_harvest_area.values),
    "Frac_MainCrop": (["lat", "lon"], main_crop_fraction.values),
}

# Add individual main crop variables
for crop in main_crops:
    var_name = f"{crop}_Harvest_Area"
    dataset_dict[var_name] = (["lat", "lon"], main_crop_data[crop].values)

# Create the dataset
result_ds = xr.Dataset(
    dataset_dict,
    coords={
        "lat": lats,
        "lon": lons
    }
)

# Add attributes
result_ds["Main_Crop_harvest_Area"].attrs = {
    "units": "ha",
    "long_name": "harvest area for main crops (RICE, WHEA, MAIZ, SOYB)",
    "_FillValue": np.nan
}

result_ds["All_Crop_harvest_Area"].attrs = {
    "units": "ha",
    "long_name": "harvest area for all crops",
    "_FillValue": np.nan
}

result_ds["Frac_MainCrop"].attrs = {
    "units": "fraction",
    "long_name": "Fraction of harvest area occupied by main crops",
    "main_crops": "RICE, WHEA, MAIZ, SOYB",
    "_FillValue": np.nan
}

# Add attributes for individual main crop variables
for crop in main_crops:
    var_name = f"{crop}_Harvest_Area"
    result_ds[var_name].attrs = {
        "units": "ha",
        "long_name": f"harvest area for {crop}",
        "_FillValue": np.nan
    }

# Save the result
output_file = os.path.join(output_path, "MainCrop_Fraction_05d.nc")
encoding = {
    "Main_Crop_harvest_Area": {"zlib": True, "complevel": 5},
    "All_Crop_harvest_Area": {"zlib": True, "complevel": 5},
    "Frac_MainCrop": {"zlib": True, "complevel": 5}
}

# Add encoding for individual main crop variables
for crop in main_crops:
    var_name = f"{crop}_Harvest_Area"
    encoding[var_name] = {"zlib": True, "complevel": 5}

result_ds.to_netcdf(output_file, encoding=encoding)
print(f"Saved: {output_file}")