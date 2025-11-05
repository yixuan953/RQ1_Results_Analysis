# This code is used to distribute the cropland N, P losses [kg] to main crops: Downscaling method 1

import xarray as xr
import numpy as np

output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1"

Crop_N_load_nc = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1/Global_cropland_critical_N_load.nc"
Crop_P_load_nc = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1/Global_cropland_critical_P_load.nc"

ds_crop_N = xr.open_dataset(Crop_N_load_nc)
ds_crop_P = xr.open_dataset(Crop_P_load_nc)

Crop_crit_N_load = ds_crop_N["critical_cropland_N_load"]
Crop_crit_P_load = ds_crop_P["critical_cropland_P_load"]

# Method 1: Assume all types of cropland should meet the same criteria [kg/ha]
total_HA_nc = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/SPAM/spam2005v3r2_global_harv_area/ncFormat/All_crop_HA.nc"
ds_HA = xr.open_dataset(total_HA_nc)
total_HA = ds_HA["Harvest_Area"]

MainCrop_crit_N_runoff = np.minimum(1000, Crop_crit_N_load / total_HA)
MainCrop_crit_P_runoff = np.minimum(1000, Crop_crit_P_load / total_HA)

MainCrop_crit_N_runoff = MainCrop_crit_N_runoff.rename("critical_maincrop_N_runoff")
MainCrop_crit_P_runoff = MainCrop_crit_P_runoff.rename("critical_maincrop_P_runoff")

MainCrop_crit_N_runoff.to_netcdf(f"{output_dir}/Global_cropland_critical_N_runoff.nc")
MainCrop_crit_P_runoff.to_netcdf(f"{output_dir}/Global_cropland_critical_P_runoff.nc")