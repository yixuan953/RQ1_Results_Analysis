# This calculation method is based on the assumption that the water leaving the cropland should be polluted:
# Critical N, P losses (kg/ha) = Critical concentration (mg/l)  * agriculture runoff simulated by WOFOST (cm) * 0.1 / retention in water 

import xarray as xr
import os

basins = ["LaPlata", "Indus", "Yangtze", "Rhine"]
crops = ["winterwheat", "maize", "mainrice", "secondrice", "soybean"]

# define critical concentrations (mg/L)
N_crit_conc_runoff = 2.5
P_crit_conc_runoff = 0.1 
Fr_ret = 0.5 
RunoffDir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/WOFOST_Runoff/Rainfed"
OutputDir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method2/Rainfed"

for basin in basins:
    for crop in crops:
        ds_runoff_nc = f"{RunoffDir}/{basin}_{crop}_runoff.nc"
        if not os.path.exists(ds_runoff_nc):
            print(f"{ds_runoff} does not exist, skipping.")
            continue
        ds_runoff   = xr.open_dataset(ds_runoff_nc)
        runoff = ds_runoff["Runoff"]

        # calculate critical losses (kg/ha)
        N_runoff   = N_crit_conc_runoff * runoff * (1/Fr_ret) * 0.1
        P_runoff   = P_crit_conc_runoff * runoff * (1/Fr_ret) * 0.1

        # save results
        N_runoff.to_netcdf(f"{OutputDir}/{basin}_{crop}_N_critical_runoff_1986-2015.nc")
        P_runoff.to_netcdf(f"{OutputDir}/{basin}_{crop}_P_critical_runoff_1986-2015.nc")
    
    print(f"Finished {basin}")