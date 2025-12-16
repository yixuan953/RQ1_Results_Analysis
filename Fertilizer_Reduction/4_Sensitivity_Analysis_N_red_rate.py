# This code is used to get the reduced fertilzer input amount 
# The fertilizer reduction stop when:
#     1) Simulated N runoff meet the boundary
#        otherwise:
#     2) Simulated yield/N runoff reaches the highest

import os 
import numpy as np
import xarray as xr

start_year = 2010
end_year = 2019

# study areas and crop types
studyareas =  ["Yangtze"] # ["Indus", "Rhine", "LaPlata", "Yangtze"]
croptypes = ["mainrice"] # ["mainrice", "secondrice", "maize", "soybean", "winterwheat"]

# Fertilizer reduction scenario
sim_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_3_Sus_Irri_Red_Fert" # Irrigated
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/4_Analysis4Plotting/4_Sens_Analysis/4_2_Irrigated"

# sim_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_3_Rainfed" # Rainfed
# output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/4_Analysis4Plotting/4_Sens_Analysis/4_1_Rainfed"

red_scenario = ["Red_02", "Red_04", "Red_06", "Red_08", "Red_org", "Red_12"]

# Critical N, P losses .nc 
crit_loss_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/2_Critical_NP_losses"

for basin in studyareas:
    N_runoff_file = os.path.join(crit_loss_dir, f"{basin}_crit_N_runoff_kgperha.nc")
    ds_crit_runoff = xr.open_dataset(N_runoff_file)
    crit_N_runoff = ds_crit_runoff["critical_maincrop_N_runoff"]
    lat = ds_crit_runoff["lat"].values
    lon = ds_crit_runoff["lon"].values
    
    for crop in croptypes:
        # Crop name for the fertilizer files
        if crop == "winterwheat":
            cropname = "Wheat"
        elif crop == "maize":
            cropname = "Maize"
        elif crop == "soybean":
            cropname = "Soybean"
        elif crop == "mainrice":
            cropname = "Rice"
        elif crop == "secondrice":
            cropname = "Rice"  

        for sce in red_scenario:
            
            sim_result_file = os.path.join(sim_dir, sce, f"{basin}_{crop}_annual.nc")
            if not os.path.exists(sim_result_file):
                print (f" {basin} missing {crop} simulation results under {sce} scenario...")
                continue
            
            # Load fertilizer input and simulation results files 
            ds_sim = xr.open_dataset(sim_result_file)

            N_runoff_all = ds_sim["N_Runoff"].sel(year = slice(start_year, end_year))
            N_runoff = N_runoff_all.mean(dim = "year", skipna = True)
            Yield_all = ds_sim["Yield"].sel(year = slice(start_year, end_year))
            Yield = Yield_all.mean(dim = "year", skipna = True)
            Yield_Nrunoff_ratio = xr.where(N_runoff == 0, np.nan, Yield/N_runoff)
            N_boundary_meet = xr.where(N_runoff <= crit_N_runoff, 1, 0)

            ds = xr.Dataset(
                {
                "Yield_Nrunoff_ratio": (("lat", "lon"), Yield_Nrunoff_ratio.values),
                "N_boundary_meet": (("lat", "lon"), N_boundary_meet.values),             
                },
                coords = {"lat": lat, "lon": lon}
            ) 
            output_file = os.path.join(output_dir, f"{basin}_{crop}_{sce}.nc")
            ds.to_netcdf(output_file)
            print(f"----> Successfully saved the outputs in {output_file}")           