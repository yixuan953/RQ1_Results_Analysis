# This code is used to calculate the total allowed N, P runoff [kg]

# This calculation method is based on the assumption that the water leaving the cropland should be polluted:
# Critical N, P losses (kg/ha) = Critical concentration (mg/l)  * agriculture runoff simulated by WOFOST (cm) * 0.1 / retention in water 
# Total losses = critical losses (kg/ha) * harvested area (ha)

import xarray as xr
import os

basins = ["LaPlata", "Indus", "Yangtze", "Rhine"]
crops = ["winterwheat", "maize", "mainrice", "secondrice", "soybean"]

# define critical concentrations (mg/L)
N_crit_conc_runoff = 2.5
P_crit_conc_runoff = 0.1 
Fr_ret = 0.5 
RunoffDir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/WOFOST_Runoff"
MaskDir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
OutputDir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method2"

# Define the year range you want to use
start_year = 1986
end_year = 2015

for basin in basins:
    total_N_runoff = None
    total_P_runoff = None

    for crop in crops:
        # ==== 1. Load runoff (Rainfed + Irrigated) ====
        Runoff_nc_rainfed = f"{RunoffDir}/Rainfed/{basin}_{crop}_runoff.nc"
        Runoff_nc_irrigated = f"{RunoffDir}/Unsus_Irri/{basin}_{crop}_runoff.nc"  

        if not os.path.exists(Runoff_nc_rainfed):
            print(f"{Runoff_nc_rainfed} does not exist, skipping.")
            continue
        if not os.path.exists(Runoff_nc_irrigated):
            print(f"{Runoff_nc_irrigated} does not exist, skipping.")
            continue

        runoff_rainfed = xr.open_dataset(Runoff_nc_rainfed)["Runoff"]
        runoff_irrigated = xr.open_dataset(Runoff_nc_irrigated)["Runoff"]

        # ==== 2. Select Year range ====
        if "Year" in runoff_rainfed.dims:
            runoff_rainfed = runoff_rainfed.sel(Year=slice(start_year, end_year))
        if "Year" in runoff_irrigated.dims:
            runoff_irrigated = runoff_irrigated.sel(Year=slice(start_year, end_year))

        # ==== 3. Load harvested area ====
        HA_rainfed_path = os.path.join(MaskDir, basin, "Mask", f"{crop}_HA_rainfed.nc")
        HA_irrigated_path = os.path.join(MaskDir, basin, "Mask", f"{crop}_HA_Irrigated.nc")

        if not os.path.exists(HA_rainfed_path) or not os.path.exists(HA_irrigated_path):
            print(f"Missing HA file for {crop} in {basin}, skipping.")
            continue

        HA_rainfed = xr.open_dataset(HA_rainfed_path)
        HA_irrigated = xr.open_dataset(HA_irrigated_path)

        HA_rainfed = HA_rainfed["area_total"] if "area_total" in HA_rainfed else list(HA_rainfed.data_vars.values())[0]
        HA_irrigated = HA_irrigated["area_total"] if "area_total" in HA_irrigated else list(HA_irrigated.data_vars.values())[0]

        # ==== 4. Align harvested area to runoff grid ====
        # Ensure lat/lon coordinate names match the runoff files
        HA_rainfed = HA_rainfed.rename({k: v for k, v in HA_rainfed.coords.items() if k.lower() in ['latitude', 'longitude']})
        HA_irrigated = HA_irrigated.rename({k: v for k, v in HA_irrigated.coords.items() if k.lower() in ['latitude', 'longitude']})

        # Interpolate HA to match runoff grid
        HA_rainfed = HA_rainfed.interp(lat=runoff_rainfed.Lat, lon=runoff_rainfed.Lon, method="nearest")
        HA_irrigated = HA_irrigated.interp(lat=runoff_irrigated.Lat, lon=runoff_irrigated.Lon, method="nearest")

        # ==== 5. Compute critical losses ====
        runoff_total = runoff_rainfed.fillna(0) * HA_rainfed.fillna(0) + runoff_irrigated.fillna(0) * HA_irrigated.fillna(0)
        N_runoff = N_crit_conc_runoff * 0.1 * (1 / Fr_ret) * runoff_total
        P_runoff = P_crit_conc_runoff * 0.1 * (1 / Fr_ret) * runoff_total

        # ==== 6. Accumulate over crops ====
        total_N_runoff = N_runoff if total_N_runoff is None else total_N_runoff + N_runoff
        total_P_runoff = P_runoff if total_P_runoff is None else total_P_runoff + P_runoff

        # ==== 7. Save per-crop ====
        N_runoff.name = "N_critical_runoff"
        P_runoff.name = "P_critical_runoff"
        N_runoff.to_netcdf(f"{OutputDir}/{basin}_{crop}_N_critical_runoff_{start_year}-{end_year}.nc")
        P_runoff.to_netcdf(f"{OutputDir}/{basin}_{crop}_P_critical_runoff_{start_year}-{end_year}.nc")

    # ==== 8. Save total for basin ====
    if total_N_runoff is not None and total_P_runoff is not None:
        total_N_runoff.name = "N_critical_runoff"
        total_P_runoff.name = "P_critical_runoff"
        total_N_runoff = total_N_runoff.transpose("Year", "Lat", "Lon")  # ✅ ensure clean order
        total_P_runoff = total_P_runoff.transpose("Year", "Lat", "Lon")

        total_N_runoff.to_netcdf(f"{OutputDir}/{basin}_Total_N_critical_runoff_{start_year}-{end_year}.nc")
        total_P_runoff.to_netcdf(f"{OutputDir}/{basin}_Total_P_critical_runoff_{start_year}-{end_year}.nc")
        print(f"Finished total for {basin}")
    else:
        print(f"No valid data for {basin}, skipping total.")
