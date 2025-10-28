import xarray as xr
import numpy as np
import os

# Input paths
baseflow_nc = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/VIC_baseflow/monthly_baseflow_ensembleMean_1986-2015_latfix.nc"
runoff_nc   = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/VIC_runoff/monthly_runoff_ensembleMean_1986-2015_latfix.nc"
cropland_frac_nc = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/Boundary/Cropland_Frac.nc"

# Output directory
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/Boundary"

# Critical concentrations (mg/L)
N_crit_conc_leach = 11.3
N_crit_conc_river = 2.5
N_nat_conc_runoff = 0.5

# --- Load datasets ---
ds_baseflow = xr.open_dataset(baseflow_nc)
baseflow = ds_baseflow[list(ds_baseflow.data_vars)[0]]

ds_runoff = xr.open_dataset(runoff_nc)
runoff = ds_runoff[list(ds_runoff.data_vars)[0]]

ds_crop_frac = xr.open_dataset(cropland_frac_nc)
cropland_frac = ds_crop_frac[list(ds_crop_frac.data_vars)[0]]

# --- Match dimensions ---
# Broadcast cropland fraction to have the same (time, lat, lon) as baseflow/runoff
cropland_frac_expanded = cropland_frac.broadcast_like(baseflow)

# --- Avoid division by zero ---
# Replace near-zero fractions with NaN to avoid inf or huge numbers
frac_safe = xr.where(cropland_frac_expanded < 1e-6, np.nan, cropland_frac_expanded)

# --- Compute critical losses (kg/ha) ---
N_leaching = 0.01 * N_crit_conc_leach * baseflow
N_runoff   = 0.01 * ((N_crit_conc_river - (1 - frac_safe) * N_nat_conc_runoff) / frac_safe) * runoff

# --- Save results ---
N_leaching.name = "Critical_N_leaching"
N_runoff.name = "Critical_N_runoff"

N_leaching.to_netcdf(os.path.join(output_dir, "Critical_N_leaching.nc"))
N_runoff.to_netcdf(os.path.join(output_dir, "Critical_N_runoff.nc"))

print("Finished generating monthly Critical N losses!")
