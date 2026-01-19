# This code is used to compare the cropland runoff from GLOBIOM and WOFOST models:
# 7_1: Calculate the cropland runoff for each crop (global) [ktons]
# 7_2: Cut the range and compare to WOFOST results [ktons]


import os
import xarray as xr
import numpy as np

# Read the data from the files

# GLOBIOM runoff data files
GLOBIOM_N_runoff_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/Globiom/Output-SSP2_NPK_NF31-Nitrogen_Budget-MANAGEMENTGLOBIOM-Nutrient-Nitrogen.nc"
GLOBIOM_P_runoff_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/Globiom/Output-SSP2_NPK_NF31-Phosphorus_Budget-MANAGEMENTGLOBIOM-Nutrient-Phosphorus.nc"

ds_GLOBIOM_N = xr.open_dataset(GLOBIOM_N_runoff_dir)
lat = ds_GLOBIOM_N["lat"].values
lon = ds_GLOBIOM_N["lon"].values
CropSurfaceRunoff_N = ds_GLOBIOM_N["CropSurfaceRunoff_N"].sel(time_counter=2) # Year 2020

ds_GLOBIOM_P = xr.open_dataset(GLOBIOM_P_runoff_dir)
CropSurfaceRunoff_P = ds_GLOBIOM_P["CropSurfaceRunoff_P"].sel(time_counter=2) # Year 2020

# FERTILIZER INPUT FILE PATHS
fertilizer_input_N_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Fertilization/N_Total_Input_2015"
fertilizer_input_P_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Fertilization/P_Total_Input_2015"

Total_N_input_file = os.path.join(fertilizer_input_N_dir, f"All_crop_sum_N.nc")
ds_total_N_input = xr.open_dataset(Total_N_input_file)
All_crop_N_input = xr.DataArray(
    ds_total_N_input["Total_N_input"].values,
    coords={"lat": lat, "lon": lon},
    dims=("lat", "lon")
)

Total_P_input_file = os.path.join(fertilizer_input_P_dir, f"All_crop_sum_P.nc") 
ds_total_P_input = xr.open_dataset(Total_P_input_file)
All_crop_P_input = xr.DataArray(
    ds_total_P_input["P_Total_Input"].values, # Assumed variable name
    coords={"lat": lat, "lon": lon},
    dims=("lat", "lon")
)


# Distribute total cropland runoff to each crop based on their fertilizer input proportions
crop_namelist = ['Wheat', 'Rice', 'Maize', 'Soybean']

for crop in crop_namelist:
    # -------------------------------------------------------------------
    crop_N_input_file = os.path.join(fertilizer_input_N_dir, f"{crop}_total_N_input_2015.nc")
    ds_crop_input = xr.open_dataset(crop_N_input_file)
    crop_N_input = xr.DataArray(
        ds_crop_input["Total_N_input"].values,
        coords={"lat": lat, "lon": lon},
        dims=("lat", "lon")
    )   
    crop_frac_N = xr.where(All_crop_N_input > 0, crop_N_input / All_crop_N_input, 1)
    # -------------------------------------------------------------------
    crop_P_input_file = os.path.join(fertilizer_input_P_dir, f"{crop}_total_P_input_2015.nc")
    ds_crop_input = xr.open_dataset(crop_P_input_file)
    crop_P_input = xr.DataArray(
        ds_crop_input["Total_P_input"].values,
        coords={"lat": lat, "lon": lon},
        dims=("lat", "lon")
    )   
    crop_frac_P = xr.where(All_crop_P_input > 0, crop_P_input / All_crop_P_input, 1)
    # -------------------------------------------------------------------

    # Calculate and save the N, P runoff for each crop [ktons] 
    crop_crit_N_loss = 1000 * CropSurfaceRunoff_N * crop_frac_N
    crop_crit_P_loss = 1000 * CropSurfaceRunoff_P * crop_frac_P

    # Save the results 
    ds_crop_surface_runoff_loss = xr.Dataset(
        {
            "GLOBIOM_cropland_N_runoff_2020": crop_crit_N_loss,
            "GLOBIOM_cropland_P_runoff_2020": crop_crit_P_loss
        },
        coords={
            "lat": lat,
            "lon": lon
        }
    )
    output_name = f"/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/Globiom/{crop}_GLOBIOM_cropland_runoff_2020.nc"
    ds_crop_surface_runoff_loss.to_netcdf(output_name)
    print(f"Saved GLOBIOM cropland runoff for {crop} in 2020 to {output_name}")