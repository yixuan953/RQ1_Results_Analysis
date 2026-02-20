# This code is used to calculate the critical N, P runoff from major cropland

import os
import xarray as xr
import numpy as np

# --- FILE PATHS ---

# N-Files
cropland_N_file = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/Global_crit_N_runoff_cropland.nc"
fertilizer_input_N_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Fertilization/N_Total_Input_2015"
# P-Files (Assumed paths, adjust if necessary)
cropland_P_file = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/Global_crit_P_runoff_cropland.nc"
fertilizer_input_P_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Fertilization/P_Total_Input_2015"

HA_area_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/Masks_SPAM2010"
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3"

# Crop list
crop_namelist = ['Wheat', 'Rice', 'Maize', 'Soybean']

# --- LOAD GENERAL DATA (N, P, and Coordinates) ---
# Load Critical N Load and Coordinates
ds_crit_N_cropland = xr.open_dataset(cropland_N_file)
total_N_load = ds_crit_N_cropland["Crit_N_cropland"]
lat = ds_crit_N_cropland["lat"].values
lon = ds_crit_N_cropland["lon"].values
# Load Total N Input (All crops summed)
Total_N_input_file = os.path.join(fertilizer_input_N_dir, f"All_crop_sum_N.nc")
ds_total_N_input = xr.open_dataset(Total_N_input_file)
All_crop_N_input = xr.DataArray(
    ds_total_N_input["Total_N_input"].values,
    coords={"lat": lat, "lon": lon},
    dims=("lat", "lon")
)

# Load Critical P Load
ds_crit_P_cropland = xr.open_dataset(cropland_P_file)
total_P_load = ds_crit_P_cropland["Crit_P_cropland"] # Assumed variable name
# Load Total P Input (All crops summed)
Total_P_input_file = os.path.join(fertilizer_input_P_dir, f"All_crop_sum_P.nc") 
ds_total_P_input = xr.open_dataset(Total_P_input_file)
All_crop_P_input = xr.DataArray(
    ds_total_P_input["P_Total_Input"].values, # Assumed variable name
    coords={"lat": lat, "lon": lon},
    dims=("lat", "lon")
)

# --- START CALCULATION LOOP ---

for crop in crop_namelist:
    # -------------------------------------------------------------------
    # A. NITROGEN (N) CALCULATION (UNCHANGED)
    # -------------------------------------------------------------------
    
    # Load crop N input
    crop_N_input_file = os.path.join(fertilizer_input_N_dir, f"{crop}_total_N_input_2015.nc")
    ds_crop_input = xr.open_dataset(crop_N_input_file)
    crop_N_input = xr.DataArray(
        ds_crop_input["Total_N_input"].values,
        coords={"lat": lat, "lon": lon},
        dims=("lat", "lon")
    )
    
    # Calculate crop fraction based on N input
    # Use xr.where to prevent division by zero in non-cropland areas
    crop_frac_N = xr.where(All_crop_N_input > 0, crop_N_input / All_crop_N_input, 1)

    # Calculate and save the total critical N loss for each crop [kg] 
    crop_crit_N_loss = total_N_load * crop_frac_N
    
    ds_kg = xr.Dataset(
    {
       "Critical_N_runoff": (("lat", "lon"), crop_crit_N_loss.values), 
    },
    coords = {"lat": lat, "lon": lon}
    )
    ds_kg["Critical_N_runoff"].attrs["units"] = "kg N"
    ds_kg["Critical_N_runoff"].attrs["Descriptions"] = "Critical N loss through runoff"
    output_file1 = os.path.join(output_dir, f"{crop}_crit_N_runoff_kg.nc")
    ds_kg.to_netcdf(output_file1)

    # Calculate and save the critical N loss for each crop [kg/ha]
    if crop == "Wheat":
        cropname = "WHEA"
    elif crop == "Maize":
        cropname = "MAIZ"
    elif crop == "Soybean":
        cropname = "SOYB"
    elif crop == "Rice":
        cropname = "RICE"     
        
    HA_file = os.path.join(HA_area_dir, f"{cropname}_Harvest_Area_05d.nc")
    ds_HA= xr.open_dataset(HA_file)
    Harvest_area = ds_HA["Harvest_Area"]
    crop_crit_N_loss_kgperha = xr.where(Harvest_area!=0, crop_crit_N_loss/Harvest_area, 0)
    
    ds_kgperha = xr.Dataset(
    {
       "Critical_N_runoff": (("lat", "lon"), crop_crit_N_loss_kgperha.values), 
    },
    coords = {"lat": lat, "lon": lon}
    )
    ds_kgperha["Critical_N_runoff"].attrs["units"] = "kg N/ha"
    ds_kgperha["Critical_N_runoff"].attrs["Descriptions"] = "Critical N loss through runoff per harvested area"
    output_file2 = os.path.join(output_dir, f"{crop}_crit_N_runoff_kgperha.nc")
    ds_kgperha.to_netcdf(output_file2) 

    # -------------------------------------------------------------------
    # B. PHOSPHORUS (P) CALCULATION (NEW)
    # -------------------------------------------------------------------

    # Load crop P input
    crop_P_input_file = os.path.join(fertilizer_input_P_dir, f"{crop}_total_P_input_2015.nc")
    ds_crop_P_input = xr.open_dataset(crop_P_input_file)
    # Assumed variable name is P_Total_Input, matching the output of the previous script
    crop_P_input = xr.DataArray(
        ds_crop_P_input[f"{crop}_P_Total_Input"].values, 
        coords={"lat": lat, "lon": lon},
        dims=("lat", "lon")
    )
    
    # Calculate crop fraction based on P input
    crop_frac_P = xr.where(All_crop_P_input > 0, crop_P_input / All_crop_P_input, 1)

    # Calculate and save the total critical P loss for each crop [kg] 
    # Distribute the total P load based on the P fraction
    crop_crit_P_loss = total_P_load * crop_frac_P
    
    ds_P_kg = xr.Dataset(
    {
       "Critical_P_runoff": (("lat", "lon"), crop_crit_P_loss.values), 
    },
    coords = {"lat": lat, "lon": lon}
    )
    ds_P_kg["Critical_P_runoff"].attrs["units"] = "kg P"
    ds_P_kg["Critical_P_runoff"].attrs["Descriptions"] = "Critical P loss through runoff"
    output_file3 = os.path.join(output_dir, f"{crop}_crit_P_runoff_kg.nc")
    ds_P_kg.to_netcdf(output_file3)

    # Calculate and save the critical P loss for each crop [kg/ha]
    # Reuse the Harvest_area loaded from the N calculation section
    crop_crit_P_loss_kgperha = xr.where(Harvest_area!=0, crop_crit_P_loss/Harvest_area, 0)
    
    ds_P_kgperha = xr.Dataset(
    {
       "Critical_P_runoff": (("lat", "lon"), crop_crit_P_loss_kgperha.values), 
    },
    coords = {"lat": lat, "lon": lon}
    )
    ds_P_kgperha["Critical_P_runoff"].attrs["units"] = "kg P/ha"
    ds_P_kgperha["Critical_P_runoff"].attrs["Descriptions"] = "Critical P loss through runoff per harvested area"
    output_file4 = os.path.join(output_dir, f"{crop}_crit_P_runoff_kgperha.nc")
    ds_P_kgperha.to_netcdf(output_file4) 

    print(f"Successfully calculated and saved critical N and P runoff for {crop}")

print("Good luck for the next step!")
