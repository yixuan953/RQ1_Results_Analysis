import xarray as xr
import glob
import os
import numpy as np
from typing import List, Dict, Union

# --- 1. Define Paths and Variables ---
P_inorg_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Fertilization/P_Fert_Inorg_1961-2019/P_Inorg_Amount_05d"
N_manure_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Fertilization/N_Fert_Man_Inorg_1961-2020/N_Manure_amount_05d"
PNratio_file = "/lustre/nobackup/WUR/ESG/zhou111/Data/Fertilization/N_Fert_Man_Inorg_1961-2020/PNratio/PNratio.nc"
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Fertilization/P_Total_Input_2015" 

manure_crop_namelist: List[str] = ['Barley', 'Cassava', 'Cotton', 'Fruits', 'Groundnut', 'Maize', 'Millet', 'Oilpalm', 'Others crops', 'Potato', 'Rapeseed', 'Rice', 'Rye', 'Sorghum', 'Soybean', 'Sugarbeet', 'Sunflower', 'Sugarcane', 'Sweetpotato', 'Vegetables', 'Wheat']
Inorg_crop_namalist: List[str] = ["Fiber crops", "Fruits", "Other Cereals", "Other crops", "Other Oilseeds", "Palm Oil fruit", "Roots and tubers", "Sugar crops", "Vegetables", "Rice", "Soybean", "Wheat", "Maize"]

TARGET_YEAR: int = 2015 
TARGET_LAT_NAME: str = 'lat'
TARGET_LON_NAME: str = 'lon'

# --- 2. Load PN Ratio and Create Alignment Template ---
print("-> Loading and renaming coordinates in PN Ratio file...")
with xr.open_dataset(PNratio_file) as ds_pn:
    # 1. Rename the coordinates to match the other input files (lat/lon)
    ds_pn = ds_pn.rename({
        'latitude': TARGET_LAT_NAME,
        'longitude': TARGET_LON_NAME
    })
    
    # 2. Extract DataArray and coordinates (using .compute() loads it into memory once)
    PN_ratio = ds_pn['PNratio'].compute()
    lat = ds_pn[TARGET_LAT_NAME].compute() 
    lon = ds_pn[TARGET_LON_NAME].compute()

# 3. Create a 2D alignment template (empty array with the correct dimensions)
# This template will be used to ensure both inorganic and manure results are on the same grid.
template_grid = xr.DataArray(
    np.empty((len(lat), len(lon)), dtype=np.float32), 
    coords={TARGET_LAT_NAME: lat, TARGET_LON_NAME: lon}
)
print(f"-> PN Ratio loaded and template grid ({len(lat)}x{len(lon)}) created successfully.")


# --- 3. Optimized Inorganic P Calculation ---
print(f"-> Starting Optimized Inorganic P calculation for {TARGET_YEAR}...")

# 1. Build a list of all inorganic file paths
inorg_file_paths = [os.path.join(P_inorg_dir, f"{crop}_P_1961-2019.nc") 
                    for crop in Inorg_crop_namalist]

# 2. Open all files robustly
# Use minimal compatibility arguments to prevent coordinate misalignment (the likely NaN cause)
ds_inorg = xr.open_mfdataset(
    inorg_file_paths, 
    combine='nested', 
    concat_dim=xr.DataArray(Inorg_crop_namalist, dims=['crop']),
    coords='minimal',  # Allow slight coordinate mismatches
    compat='override', # Override variable metadata differences
    data_vars=['P2O5'] # Only load P2O5 to save memory
)

# 3. Select year, sum across crops. This result is lazy (Dask).
total_P_inorg_lazy = (
    ds_inorg['P2O5']
    .sel(year=TARGET_YEAR)
    .sum(dim='crop')
)

# 4. Interpolate to the template grid and compute the result
total_P_inorg = total_P_inorg_lazy.interp_like(template_grid, method='nearest').compute()

print("-> Finished Optimized Inorganic P calculation.")
print(f"Number of Inorganic files loaded: {len(inorg_file_paths)}")


# --- 4. Optimized Manure P Input (Conversion N -> P) ---
print(f"-> Starting Optimized Manure P (N to P conversion) calculation for {TARGET_YEAR}...")

# 1. Build a list of all manure file paths
manure_file_paths = [os.path.join(N_manure_dir, f"N_manure_input_amount_{crop}_1961-2020.nc") 
                     for crop in manure_crop_namelist]

# 2. Open all files robustly (using the same arguments as inorganic)
ds_manure = xr.open_mfdataset(
    manure_file_paths, 
    combine='nested', 
    concat_dim=xr.DataArray(manure_crop_namelist, dims=['crop']),
    coords='minimal', 
    compat='override',
    data_vars=['N_manure_amount']
)

# 3. Select the year and sum the N manure input across the crops (lazy)
n_manure_crop_sum_lazy = (
    ds_manure['N_manure_amount']
    .sel(year=TARGET_YEAR)
    .sum(dim='crop')
)

# 4. Perform the conversion (P Manure = N Manure * PN_ratio) and compute
# We first align the N-sum to the template before multiplying with the PN_ratio.
total_P_manure = (
    n_manure_crop_sum_lazy
    .interp_like(template_grid, method='nearest') # Align N-sum to template
    * PN_ratio                                   # Multiply with P/N ratio
).compute() 

print("-> Finished Optimized Manure P calculation.")
print(f"Number of Manure files loaded: {len(manure_file_paths)}")


# --- 5. Combine and Save Final Result ---

# total_P_inorg and total_P_manure are now both guaranteed to be 2D (lat, lon) 
# and share the same exact coordinates due to interpolation against template_grid.
total_P_input = total_P_inorg + total_P_manure

# Create a new Dataset for saving
ds_output = xr.Dataset(
    data_vars={'P_Total_Input': total_P_input}, 
    # Use the extracted coordinates
    coords = {TARGET_LAT_NAME: lat, TARGET_LON_NAME: lon}
)
    
# Inherit units and add metadata
ds_output['P_Total_Input'].attrs['units'] = total_P_input.attrs.get('units', 'kg')
ds_output.attrs['description'] = f"Total Phosphorus (P) fertilizer input (Inorganic + Manure) summed across all crops for the year {TARGET_YEAR}."
    
# Save to NetCDF
output_filename = os.path.join(output_dir, f"All_crop_sum_P_{TARGET_YEAR}.nc")
ds_output.to_netcdf(output_filename)
print(f"\n✅ Successfully created and saved total P input to: {output_filename}")