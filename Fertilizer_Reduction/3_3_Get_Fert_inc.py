# This code is used to get how much fertilizer can (should) be increased to meet the regional N boundary:
# Here we go through each fertilizer reductin scenario, the loop stops when: N_exceedance>=0


import pandas as pd
import numpy as np
import xarray as xr
import os

Basins = ["Indus", "Rhine", "LaPlata", "Yangtze"]
CropTypes = ["mainrice", "secondrice", "maize", "winterwheat", "soybean"]
red_scenarios = ["Inc_02", "Inc_04", "Inc_06", "Inc_08", "Inc_10", "Inc_12", "Inc_14"]

baseline_sce_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/4_Analysis4Plotting/0_Summary/1_Baseline"

# Irrigated field
# red_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/4_Fertilization_Red/4_1_Reduced_Fert/Irrigated" 
# yield_var = "Avg_Yield_Irrigated"

# Rainfed field
red_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/4_Fertilization_Red/4_1_Reduced_Fert/Rainfed" 
yield_var = "Avg_Yield_Rainfed"

for basin in Basins:
    for crop in CropTypes:
        # ================ Read the baseline yield ==================
        baseline_nc = os.path.join(baseline_sce_dir, f"{basin}_{crop}_summary.nc")
        if not os.path.exists(baseline_nc):
            continue

        ds_baseline = xr.open_dataset(baseline_nc)
        HA = ds_baseline["Total_HA"]
        mask = ds_baseline["Basin_mask"].where(HA > 2500, np.nan)
        baseline_yield = ds_baseline[yield_var].where(mask.notnull())

        # ========= Load Sensitivity Data ===
        sens_Yield_nc = os.path.join(red_dir, f"Sens_Analysis_inc/{basin}_{crop}_Yields.nc")
        sens_N_exceedance_nc = os.path.join(red_dir, f"Sens_Analysis_inc/{basin}_{crop}_N_Exceedance.nc")
        
        if not os.path.exists(sens_Yield_nc) or not os.path.exists(sens_N_exceedance_nc):
            continue    

        ds_sens_yield = xr.open_dataset(sens_Yield_nc)
        ds_sens_N_exceedance = xr.open_dataset(sens_N_exceedance_nc)

        # Initialize trackers
        # final_yield starts as baseline; if a pixel fails on the first scenario, it stays baseline.
        final_yield = baseline_yield.copy() 
        final_red_prop = xr.full_like(baseline_yield, 0.0)
        stopped_mask = xr.zeros_like(baseline_yield, dtype=bool)

        # Variables to hold the "Previous" state
        prev_yield = baseline_yield.copy()
        prev_red_prop = xr.full_like(baseline_yield, 0.0)

        for red_sce in red_scenarios:
            sens_yield = ds_sens_yield["Yield"].sel(scenario=red_sce).where(mask.notnull())
            sens_N_exceedance = ds_sens_N_exceedance["N_exceedance"].sel(scenario=red_sce).where(mask.notnull())
            
            # Extract numeric prop (e.g., 0.2, 0.4...)
            red_prop = float(red_sce.split('_')[1]) / 10.0  

            # Condition: We hit or exceed the N boundary
            # We want to stop here and take the PREVIOUS values
            stop_now = (sens_N_exceedance >= 0) & (~stopped_mask) & mask.notnull()

            # If condition met, assign the PREVIOUS scenario's values
            final_yield = xr.where(stop_now, prev_yield, final_yield)
            final_red_prop = xr.where(stop_now, prev_red_prop, final_red_prop)

            # Update tracker
            stopped_mask = stopped_mask | stop_now

            # Update "Previous" state for the next scenario in the loop
            prev_yield = sens_yield
            prev_red_prop = red_prop

            if stopped_mask.where(mask.notnull(), True).all():
                break

        # If a pixel never reached N_exceedance >= 0, it should take the last possible scenario
        # This handles pixels that are still "safe" even at Inc_14
        final_yield = xr.where(~stopped_mask & mask.notnull(), prev_yield, final_yield)
        final_red_prop = xr.where(~stopped_mask & mask.notnull(), prev_red_prop, final_red_prop)

        # ================ Save the Results ==================
        output_dir_fert = os.path.join(red_dir, f"Inc_prop/{basin}_{crop}_Fert_inc_prop.nc")
        output_yield = os.path.join(red_dir, f"Inc_prop/{basin}_{crop}_Yield_after_inc.nc")
        os.makedirs(os.path.dirname(output_dir_fert), exist_ok=True)
        
        final_red_prop.to_dataset(name="Fert_inc_prop").to_netcdf(output_dir_fert)
        final_yield.to_dataset(name="Yield_after_inc").to_netcdf(output_yield)
        
        print(f"Finished processing {basin} - {crop}")