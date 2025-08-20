import xarray as xr
import numpy as np
import os

# Paths
base_mask = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea/Yangtze/Mask"
base_nc   = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/S1"

# Input mask files
mask_main_file = os.path.join(base_mask, "Yangtze_mainrice_mask.nc")
mask_second_file = os.path.join(base_mask, "Yangtze_secondrice_mask.nc")

# Output corrected files
mask_main_out   = os.path.join(base_mask, "Yangtze_mainrice_mask_corr.nc")
mask_second_out = os.path.join(base_mask, "Yangtze_secondrice_mask_corr.nc")

# Open mask datasets
ds_main = xr.open_dataset(mask_main_file)
ds_second = xr.open_dataset(mask_second_file)

ha_main = ds_main["HA"].copy()
ha_second = ds_second["HA"].copy()

# Open Yp files
yp_second = xr.open_dataset(os.path.join(base_nc, "Yangtze_secondrice_Yp.nc"))
yp_main   = xr.open_dataset(os.path.join(base_nc, "Yangtze_mainrice_Yp.nc"))

yp_second_mean = yp_second.sel(year=slice(1986, 2015)).mean(dim="year", skipna=True)
yp_main_mean   = yp_main.sel(year=slice(1986, 2015)).mean(dim="year", skipna=True)

# Conditions
cond1 = ha_main > 200000
cond2 = ((ds_second["Sow_date"] > 17) & (yp_second_mean["GrowthDay"] < 140) &(ds_main["Sow_date"] < 10) & (yp_main_mean["GrowthDay"] < 140))

condition = cond1 | cond2  # either condition triggers correction

# Apply corrections
ha_second_corr = xr.where(condition, ha_second / 2, np.nan)
ha_main_corr   = xr.where(condition, ha_main - ha_second_corr, ha_main)

# Update datasets
ds_second_corr = ds_second.copy()
ds_main_corr   = ds_main.copy()

ds_second_corr["HA"].values = ha_second_corr.values
ds_main_corr["HA"].values   = ha_main_corr.values

# Save outputs
ds_second_corr.to_netcdf(mask_second_out)
ds_main_corr.to_netcdf(mask_main_out)

print(f"Corrected masks saved to:\n {mask_second_out}\n {mask_main_out}")