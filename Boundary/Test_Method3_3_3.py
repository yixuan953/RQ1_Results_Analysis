import xarray as xr
import glob
import os
import numpy as np
from typing import List, Dict, Union

# --- 1. Define Paths and Variables ---
# Input directories and files
P_inorg_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Fertilization/P_Fert_Inorg_1961-2019/P_Inorg_Amount_05d"
N_manure_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Fertilization/N_Fert_Man_Inorg_1961-2020/N_Manure_amount_05d"
PNratio_file = "/lustre/nobackup/WUR/ESG/zhou111/Data/Fertilization/N_Fert_Man_Inorg_1961-2020/PNratio/PNratio.nc"
output_root_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Fertilization/P_Total_Input_2015" 
os.makedirs(output_root_dir, exist_ok=True) # Ensure output directory exists

# List of target crops
TARGET_CROPS: List[str] = ['Wheat', 'Rice', 'Maize', 'Soybean']

TARGET_YEAR: int = 2015 
TARGET_LAT_NAME: str = 'lat'
TARGET_LON_NAME: str = 'lon'


# --- 2. Load PN Ratio for Manure Conversion (with Coordinate Renaming) ---
print("-> Loading and preparing PN Ratio file...")
with xr.open_dataset(PNratio_file) as ds_pn:
    # Rename coordinates (critical for alignment with manure/inorganic files)
    ds_pn = ds_pn.rename({
        'latitude': TARGET_LAT_NAME,
        'longitude': TARGET_LON_NAME
    })
    
    # Extract DataArray and coordinates, loaded into memory
    PN_ratio = ds_pn['PNratio'].compute()
    lat = ds_pn[TARGET_LAT_NAME].compute() 
    lon = ds_pn[TARGET_LON_NAME].compute()
print("-> PN Ratio loaded and coordinates renamed successfully.")

# --- 3. Iterate and Calculate Total P Input for Each Crop ---

for crop in TARGET_CROPS:
    print(f"\n==============================================")
    print(f"-> Starting calculation for: {crop}")
    print(f"==============================================")
    
    # ----------------------------------------------------
    # A. CALCULATE INORGANIC P INPUT
    # ----------------------------------------------------
    try:
        # Construct path for inorganic file
        # ASSUMPTION: File naming convention uses the crop name and _P_1961-2019.nc
        inorg_file_path = os.path.join(P_inorg_dir, f"{crop}_P_1961-2019.nc") 
        
        with xr.open_dataset(inorg_file_path) as ds_p:
            # Select the target year. .sel(year=2015) automatically drops the year dimension.
            total_P_inorg = ds_p['P2O5'].sel(year=TARGET_YEAR).compute()
            
            # Interpolate to the PN_ratio grid to guarantee coordinate alignment
            total_P_inorg = total_P_inorg.interp_like(PN_ratio, method='nearest')
            print(f"  -> Inorganic P for {crop} loaded successfully.")

    except FileNotFoundError:
        print(f"  ❌ Inorganic file not found for {crop} at: {inorg_file_path}. Setting to zero.")
        # Create a zero-filled DataArray on the correct grid
        total_P_inorg = xr.zeros_like(PN_ratio)
    except KeyError as e:
        print(f"  ❌ Error reading P2O5 for {crop}. Check variable/coordinate names. Error: {e}")
        total_P_inorg = xr.zeros_like(PN_ratio)

    # ----------------------------------------------------
    # B. CALCULATE MANURE P INPUT (N -> P Conversion)
    # ----------------------------------------------------
    try:
        # Construct path for manure file
        manure_file_path = os.path.join(N_manure_dir, f"N_manure_input_amount_{crop}_1961-2020.nc") 
        
        with xr.open_dataset(manure_file_path) as ds_n:
            # Select the target year.
            n_manure_crop = ds_n['N_manure_amount'].sel(year=TARGET_YEAR)

            # 1. Align the N input to the PN_ratio grid
            n_manure_crop_aligned = n_manure_crop.interp_like(PN_ratio, method='nearest')

            # 2. Perform the conversion (P Manure = N Manure * PN_ratio)
            total_P_manure = (n_manure_crop_aligned * PN_ratio).compute() 
            print(f"  -> Manure P for {crop} converted and loaded successfully.")

    except FileNotFoundError:
        print(f"  ❌ Manure file not found for {crop} at: {manure_file_path}. Setting to zero.")
        total_P_manure = xr.zeros_like(PN_ratio)
    except KeyError as e:
        print(f"  ❌ Error reading N_manure_amount for {crop}. Check variable/coordinate names. Error: {e}")
        total_P_manure = xr.zeros_like(PN_ratio)

    # ----------------------------------------------------
    # C. COMBINE AND SAVE FINAL RESULT
    # ----------------------------------------------------
    total_P_input_crop = total_P_inorg + total_P_manure
    
    # Create output Dataset
    ds_output = xr.Dataset(
        data_vars={f'{crop}_P_Total_Input': total_P_input_crop}, 
        coords = {TARGET_LAT_NAME: lat, TARGET_LON_NAME: lon}
    )
        
    # Add metadata
    ds_output[f'{crop}_P_Total_Input'].attrs['units'] = total_P_input_crop.attrs.get('units', 'kg')
    ds_output.attrs['description'] = f"Total Phosphorus (P) fertilizer input (Inorganic + Manure) for the crop {crop} in the year {TARGET_YEAR}."
        
    # Save to NetCDF
    output_filename = os.path.join(output_root_dir, f"{crop}_total_P_input_{TARGET_YEAR}.nc")
    ds_output.to_netcdf(output_filename)
    print(f"  ✅ Output saved to: {output_filename}")

print("\n\n*** All individual crop P input calculations complete. ***")