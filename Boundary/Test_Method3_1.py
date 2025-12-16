# This code is used to calculate the critical N, P concentration [mg/L] & critical N, P load [kg] for agricultural runoff

import os
import xarray as xr
import numpy as np

IMAGE_land_use_file = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE/Output-IMAGE_GNM-SSP5_oct2020-LandCover-v2.nc"
Global_crit_NP_conc_runoff_file = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/Global_crit_NP_conc_runoff.nc"
VIC_runoff_file = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/VIC_runoff/annual_runoff_mean_ssp585_inverted.nc"
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3"

# Load the critcial N, P concentration for runoff water
ds_crit_NP_conc_runoff = xr.open_dataset(Global_crit_NP_conc_runoff_file)
Crit_N_conc_runoff = ds_crit_NP_conc_runoff["Crit_N_conc_runoff"]
Crit_P_conc_runoff = ds_crit_NP_conc_runoff["Crit_P_conc_runoff"]

# Load the cropland data
ds_agri_land = xr.open_dataset(IMAGE_land_use_file)
lat = ds_agri_land["lat"].values
lon = ds_agri_land["lon"].values

cropland_area = ds_agri_land["Cropland"].sel(time = "2015-05-01")
pasture_area = ds_agri_land["Pasture"].sel(time = "2015-05-01")
nat_area = ds_agri_land["NonAgriculturalLand"].sel(time = "2015-05-01")

agri_area = cropland_area + pasture_area
total_area = agri_area + nat_area
frac_agri = xr.where(total_area!=0, agri_area/total_area, np.nan)

# Load the runoff data
ds_runoff = xr.open_dataset(VIC_runoff_file)
runoff_raw = ds_runoff["OUT_RUNOFF"].sel(year = "2014")
runoff = xr.where (runoff_raw<3, 0, runoff_raw)

# Calculate the critical N, P concentration and load for agricultural runoff
N_nat = 0.5   # mg/l
P_nat = 0.003 # mg/l
frac_dissolved_P = 0.25 

raw_N_conc = (Crit_N_conc_runoff - N_nat * (1 - frac_agri)) / frac_agri
crit_N_conc_agri = xr.where(frac_agri > 0, np.maximum(raw_N_conc, N_nat), N_nat) 
crit_N_load_agri = crit_N_conc_agri * runoff * agri_area * 10000 # kg

raw_P_conc = (Crit_P_conc_runoff - P_nat * (1 - frac_agri)) / frac_agri
crit_P_conc_agri = xr.where(frac_agri > 0, np.maximum(raw_P_conc, P_nat), P_nat)  # mg/l
crit_P_load_agri = frac_dissolved_P * crit_P_conc_agri * runoff * agri_area * 10000 # kg

# Save the outputs

ds_crit_N_conc = xr.Dataset(
    {
       "Crit_N_conc_agri": (("lat", "lon"), crit_N_conc_agri.values),  
       "Crit_N_load_agri": (("lat", "lon"), crit_N_load_agri.values), 
    },
    coords = {"lat": lat, "lon": lon}
)
ds_crit_N_conc["Crit_N_conc_agri"].attrs["units"] = "mg/L"
ds_crit_N_conc["Crit_N_load_agri"].attrs["units"] = "kg N"

output_file1 = os.path.join(output_dir, f"Global_crit_N_conc_load_agri.nc")
ds_crit_N_conc.to_netcdf(output_file1)


ds_crit_P_conc = xr.Dataset(
    {
       "Crit_P_conc_agri": (("lat", "lon"), crit_P_conc_agri.values),  
       "Crit_P_load_agri": (("lat", "lon"), crit_P_load_agri.values), 
    },
    coords = {"lat": lat, "lon": lon}
)
ds_crit_P_conc["Crit_P_conc_agri"].attrs["units"] = "mg/L"
ds_crit_P_conc["Crit_P_load_agri"].attrs["units"] = "kg P"

output_file2 = os.path.join(output_dir, f"Global_crit_P_conc_load_agri.nc")
ds_crit_P_conc.to_netcdf(output_file2)

print(f"Computed and saved {output_file1} & {output_file2}")
print(f"Good luck for the next step!")