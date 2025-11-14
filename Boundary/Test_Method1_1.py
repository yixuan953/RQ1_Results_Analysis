# This code is used to calculate the total allowed N, P losses through runoff 
# Here we do not consider retention, as it was already considered in IMAGE model

import xarray as xr

N_crit_conc_runoff = 2.5
P_crit_conc_runoff = 0.1 

output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1"

# monthly_runoff_nc = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/VIC_runoff/monthly_runoff_ensembleMean_1986-2015_latfix.nc"
# ds_monthly_runoff = xr.open_dataset(monthly_runoff_nc)
# runoff = ds_monthly_runoff["OUT_RUNOFF"]

annual_runoff_nc = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/VIC_runoff/annual_runoff_mean_ssp585_inverted.nc"
ds_annual_runoff = xr.open_dataset(annual_runoff_nc)
runoff = ds_annual_runoff["OUT_RUNOFF"]

pixel_area_nc = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/General/pixel_area_m2_05d_invertedLat.nc"
ds_pixel_area = xr.open_dataset(pixel_area_nc)
pixel_area = ds_pixel_area["area"]

# Calculate the total N load through runoff (kg)
total_N_load = runoff * pixel_area * N_crit_conc_runoff  * 0.000001
total_P_load = runoff * pixel_area * P_crit_conc_runoff  * 0.000001

total_N_load = total_N_load.rename("critical_total_N_load")
total_N_load.to_netcdf(f"{output_dir}/Global_total_critical_N_load.nc")

total_P_load = total_P_load.rename("critical_total_P_load")
total_P_load.to_netcdf(f"{output_dir}/Global_total_critical_P_load.nc")