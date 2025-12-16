# This code is used to get the critical N, P concentration in runoff water [mg/L]

import os
import xarray as xr
import numpy as np

# Input directory for N
IMAGE_file_N = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE/Output-IMAGE_GNM-SSP1_oct2020-Nitrogen_Rivers-v2.nc"
ds_IMAGE_N = xr.open_dataset(IMAGE_file_N)
total_N_load_all = ds_IMAGE_N["Naquaculture"] + ds_IMAGE_N["Ndeposition_water"] + ds_IMAGE_N["Ngroundwater_agri"] + ds_IMAGE_N["Ngroundwater_nat"] +ds_IMAGE_N["Nsurface_runoff_agri"] + ds_IMAGE_N["Nsurface_runoff_nat"] + ds_IMAGE_N["Nsewage"] + ds_IMAGE_N["Nvegetation"] 
total_N_load = total_N_load_all.sel(time = "2015-05-01")
agri_N_load = ds_IMAGE_N["Nsurface_runoff_agri"].sel(time = "2015-05-01")
nat_N_load = ds_IMAGE_N["Nsurface_runoff_nat"].sel(time = "2015-05-01")

lat = ds_IMAGE_N["lat"].values
lon = ds_IMAGE_N["lon"].values

# Input directory for P
IMAGE_file_P = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE/Output-IMAGE_GNM-SSP1_oct2020-Phosphorus_Rivers-v2.nc"
ds_IMAGE_P = xr.open_dataset(IMAGE_file_P)
total_P_load_all = ds_IMAGE_P["Paquaculture"] + ds_IMAGE_P["Psewage"]  + ds_IMAGE_P["Psurface_runoff_agri"] + ds_IMAGE_P["Psurface_runoff_nat"]  + ds_IMAGE_P["Pvegetation"]  + ds_IMAGE_P["Pweathering"]
total_P_load = total_P_load_all.sel(time = "2015-05-01")
agri_P_load = ds_IMAGE_P["Psurface_runoff_agri"].sel(time = "2015-05-01")
nat_P_load = ds_IMAGE_P["Psurface_runoff_nat"].sel(time = "2015-05-01")

# Output directory
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3"

# -------- Calcualtion --------
frac_retention = 0.5
crit_N_conc_surf_water = 2.5 # [mg N/L]
crit_P_conc_surf_water = 0.1 # [mg P/L] # Dissolved + suspended P

# Calculate how much N, P is contributed by runoff
frac_runoff_N_load = (agri_N_load + nat_N_load)/total_N_load 
frac_runoff_P_load = (agri_P_load + nat_P_load)/total_P_load  

crit_N_conc_runoff = crit_N_conc_surf_water * frac_runoff_N_load / frac_retention
crit_P_conc_runoff = crit_P_conc_surf_water * frac_runoff_P_load / frac_retention

ds_crit_NP_conc_runoff = xr.Dataset(
    {
       "Crit_N_conc_runoff": (("lat", "lon"), crit_N_conc_runoff.values),  
       "Crit_P_conc_runoff": (("lat", "lon"), crit_P_conc_runoff.values), 
    },
    coords = {"lat": lat, "lon": lon}
)
ds_crit_NP_conc_runoff["Crit_N_conc_runoff"].attrs["units"] = "mg/L"
ds_crit_NP_conc_runoff["Crit_P_conc_runoff"].attrs["units"] = "mg/L"

output_file = os.path.join(output_dir, f"Global_crit_NP_conc_runoff.nc")
ds_crit_NP_conc_runoff.to_netcdf(output_file)
print(f"Computed and saved {output_file}")
print(f"Good luck for the next step!")