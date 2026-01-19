# This code is used to get the critical N, P losses for major crops
import xarray as xr
import numpy as np

output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3"

Crop_N_load_nc = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/Global_crit_N_runoff_cropland.nc"
Crop_P_load_nc = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/Global_crit_P_runoff_cropland.nc"

ds_crop_N = xr.open_dataset(Crop_N_load_nc)
ds_crop_P = xr.open_dataset(Crop_P_load_nc)

Crop_crit_N_load = ds_crop_N["Crit_N_cropland"]
Crop_crit_P_load = ds_crop_P["Crit_P_cropland"]

# Method 1: Assume all types of cropland should meet the same criteria [kg/ha]
total_HA_nc = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/Masks_SPAM2010/MajorCrop_Total_HA.nc"
ds_HA = xr.open_dataset(total_HA_nc)
total_HA = ds_HA["All_Crop_harvest_Area"]
maincrop_frac = ds_HA["Frac_MainCrop"]

MainCrop_crit_N_runoff = np.minimum(1000, Crop_crit_N_load / total_HA)
MainCrop_crit_P_runoff = np.minimum(1000, Crop_crit_P_load / total_HA)

maincrop_total_N_loss = Crop_crit_N_load * maincrop_frac
maincrop_total_P_loss = Crop_crit_P_load * maincrop_frac

MainCrop_crit_N_runoff = MainCrop_crit_N_runoff.rename("critical_maincrop_N_runoff")
MainCrop_crit_P_runoff = MainCrop_crit_P_runoff.rename("critical_maincrop_P_runoff")

maincrop_total_N_loss = maincrop_total_N_loss.rename("critical_total_maincrop_N_runoff")
maincrop_total_P_loss = maincrop_total_P_loss.rename("critical_total_maincrop_P_runoff")

MainCrop_crit_N_runoff.to_netcdf(f"{output_dir}/Global_cropland_critical_N_runoff_kgPerha.nc")
MainCrop_crit_P_runoff.to_netcdf(f"{output_dir}/Global_cropland_critical_P_runoff_kgPerha.nc")

maincrop_total_N_loss.to_netcdf(f"{output_dir}/Global_maincrop_critical_total_N_runoff.nc")
maincrop_total_P_loss.to_netcdf(f"{output_dir}/Global_maincrop_critical_total_P_runoff.nc")