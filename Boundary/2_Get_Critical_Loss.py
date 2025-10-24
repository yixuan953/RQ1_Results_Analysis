import xarray as xr
import os

basins = ["LaPlata", "Indus", "Yangtze", "Rhine"]

# define critical concentrations (mg/L)
N_crit_conc_runoff = 5.0
N_crit_conc_leach = 11.3
P_crit_conc_runoff = 0.16 
P_crit_conc_leach = 0.16 

for basin in basins:
    hydro_dir = f"/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea/{basin}/Hydro"

    # open baseflow and runoff
    ds_baseflow = xr.open_dataset(f"{hydro_dir}/{basin}_monthly_baseflow_1986-2015.nc")
    ds_runoff   = xr.open_dataset(f"{hydro_dir}/{basin}_monthly_runoff_1986-2015.nc")

    # assume variable names are 'baseflow' and 'runoff'; adjust if needed
    baseflow = ds_baseflow[list(ds_baseflow.data_vars)[0]]
    runoff   = ds_runoff[list(ds_runoff.data_vars)[0]]

    # calculate critical losses (kg/ha)
    N_leaching = N_crit_conc_leach * baseflow * 0.01
    N_runoff   = N_crit_conc_runoff * runoff   * 0.01
    P_leaching = P_crit_conc_runoff * baseflow * 0.01
    P_runoff   = P_crit_conc_leach * runoff   * 0.01

    # save results
    N_leaching.to_netcdf(f"{hydro_dir}/{basin}_N_critical_leaching_1986-2015.nc")
    N_runoff.to_netcdf(f"{hydro_dir}/{basin}_N_critical_runoff_1986-2015.nc")
    P_leaching.to_netcdf(f"{hydro_dir}/{basin}_P_critical_leaching_1986-2015.nc")
    P_runoff.to_netcdf(f"{hydro_dir}/{basin}_P_critical_runoff_1986-2015.nc")

    print(f"Finished {basin}")