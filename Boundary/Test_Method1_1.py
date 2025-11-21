# This code is used to calculate the total allowable N, P losses through runoff 
# Total critical N, P losses = critical concentration * runoff / retention fraction in water

import xarray as xr

N_crit_conc_runoff = 2.5
P_crit_conc_runoff = 0.075 
retention_fraction = 0.5

output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1"

annual_runoff_nc = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/VIC_runoff/annual_runoff_mean_ssp585_inverted.nc"
ds_annual_runoff = xr.open_dataset(annual_runoff_nc)
runoff = ds_annual_runoff["OUT_RUNOFF"]

pixel_area_nc = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/General/pixel_area_m2_05d_invertedLat.nc"
ds_pixel_area = xr.open_dataset(pixel_area_nc)
pixel_area = ds_pixel_area["area"]

# Calculate the total N load through runoff (kg)
total_N_load = runoff * pixel_area * N_crit_conc_runoff  * 0.000001/0.5
total_P_load = runoff * pixel_area * P_crit_conc_runoff  * 0.000001/0.5

total_N_load = total_N_load.rename("critical_total_N_load")
total_N_load.to_netcdf(f"{output_dir}/Global_total_critical_N_load.nc")

total_P_load = total_P_load.rename("critical_total_P_load")
total_P_load.to_netcdf(f"{output_dir}/Global_total_critical_P_load.nc")