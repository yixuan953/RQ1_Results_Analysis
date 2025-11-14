# This code is used to calculate the critical <Agricultural> N, P losses through runoff 
# The IAMGE-GNM data can be downloaded from: https://dataportaal.pbl.nl/IMAGE/GNM

import xarray as xr

output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1"

# Load total critical N, P runoff: Monthly 
IMAGE_data_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE"
total_N_load_nc = f"{output_dir}/Global_total_critical_N_load.nc"
total_P_load_nc = f"{output_dir}/Global_total_critical_P_load.nc"

total_N_load = xr.open_dataset(total_N_load_nc)["critical_total_N_load"]
total_P_load = xr.open_dataset(total_P_load_nc)["critical_total_P_load"]

# Load total N, P losses: every five years, here we use year 2005 to calculate the proportion
N_loss_nc = f"{IMAGE_data_dir}/Output-IMAGE_GNM-SSP5_oct2020-Nitrogen_Rivers-v2.nc"
P_loss_nc = f"{IMAGE_data_dir}/Output-IMAGE_GNM-SSP5_oct2020-Phosphorus_Rivers-v2.nc"

ds_N_loss_all = xr.open_dataset(N_loss_nc)
ds_P_loss_all = xr.open_dataset(P_loss_nc)

# Select the year used for proportion (e.g., 2005)
ds_N_loss = ds_N_loss_all.sel(time= "2015")
ds_P_loss = ds_P_loss_all.sel(time= "2015")

# Calculate total and agricultural proportions 
Total_N_loss = (
    ds_N_loss["Naquaculture"]
    + ds_N_loss["Nsewage"]
    + ds_N_loss["Nsurface_runoff_agri"]
    + ds_N_loss["Nsurface_runoff_nat"]
    + ds_N_loss["Nvegetation"]
)

Total_P_loss = (
    ds_P_loss["Paquaculture"]
    + ds_P_loss["Psewage"]
    + ds_P_loss["Psurface_runoff_agri"]
    + ds_P_loss["Psurface_runoff_nat"]
    + ds_P_loss["Pvegetation"]
    + ds_P_loss["Pweathering"]
)

prop_N_agri = ds_N_loss["Nsurface_runoff_agri"] / Total_N_loss
prop_P_agri = ds_P_loss["Psurface_runoff_agri"] / Total_P_loss

#  Drop the time coordinate so it won't interfere with broadcasting
if "time" in prop_N_agri.dims:
    prop_N_agri = prop_N_agri.squeeze("time", drop=True)
if "time" in prop_P_agri.dims:
    prop_P_agri = prop_P_agri.squeeze("time", drop=True)
if "time" in prop_N_agri.coords:
    prop_N_agri = prop_N_agri.drop_vars("time")
if "time" in prop_P_agri.coords:
    prop_P_agri = prop_P_agri.drop_vars("time")

# Apply the 2005 proportion to all years/months in total load
Agri_N_loss = total_N_load * prop_N_agri
Agri_P_loss = total_P_load * prop_P_agri

# Rename variables correctly
Agri_N_loss = Agri_N_loss.rename("critical_agri_N_load")
Agri_P_loss = Agri_P_loss.rename("critical_agri_P_load")

# Save to NetCDF
Agri_N_loss.to_netcdf(f"{output_dir}/Global_agri_critical_N_load.nc")
Agri_P_loss.to_netcdf(f"{output_dir}/Global_agri_critical_P_load.nc")