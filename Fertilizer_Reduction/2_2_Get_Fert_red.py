# This code is used to get how much fertilizer can (should) be reduced to meet the regional N boundary:
# Here we go through each fertilizer reductin scenario, the loop stops when:
# 1) N_exceedance <=0 or
# 2) Yield <= 50% of baseline yield --> The crop growth is largely compromised, making harvest not feasible


import pandas as pd
import numpy as np
import xarray as xr
import os

Basins = ["Indus", "Rhine", "LaPlata", "Yangtze"]
CropTypes = ["mainrice", "secondrice", "maize", "winterwheat", "soybean"]
red_scenarios = ["Red_02", "Red_04", "Red_06", "Red_08", "Red_10", "Red_12", "Red_14"]

baseline_sce_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/4_Analysis4Plotting/0_Summary/1_Baseline"

# Irrigated field
red_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/4_Fertilization_Red/4_1_Reduced_Fert/Irrigated" 
yield_var = "Avg_Yield_Irrigated"

# # Rainfed field
# red_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/4_Fertilization_Red/4_1_Reduced_Fert/Rainfed" 
# yield_var = "Avg_Yield_Rainfed"

for basin in Basins:
    for crop in CropTypes:

        # ================ Read the baseline yield ==================
        baseline_nc = os.path.join(baseline_sce_dir, f"{basin}_{crop}_summary.nc")
        if not os.path.exists(baseline_nc):
            print(f"Baseline file does not exist: {baseline_nc}")
            continue

        ds_baseline = xr.open_dataset(baseline_nc)
        basin_mask = ds_baseline["Basin_mask"]
        HA = ds_baseline["Total_HA"] # ha
        mask = basin_mask.where(HA > 2500, np.nan) # only consider grid cells with more than 2500 ha harvested area

        baseline_yield = ds_baseline[yield_var].where(mask.notnull()) # kg/ha 

        # ========= Loop through each fertilizer reduction scenario ===
        sens_Yield_nc = os.path.join(red_dir, f"Sens_Analysis/{basin}_{crop}_Yields.nc")
        sens_N_exceedance_nc = os.path.join(red_dir, f"Sens_Analysis/{basin}_{crop}_N_Exceedance.nc")
        if not os.path.exists(sens_Yield_nc) or not os.path.exists(sens_N_exceedance_nc):
            print(f"Sensitivity analysis files do not exist for {basin} - {crop}")
            continue    

        ds_sens_yield = xr.open_dataset(sens_Yield_nc)
        ds_sens_N_exceedance = xr.open_dataset(sens_N_exceedance_nc)

        # Initialize result grids with NaN or a flag value
        final_yield = baseline_yield.copy() 
        final_red_prop = xr.full_like(baseline_yield, 0.0)
        stopped_mask = xr.zeros_like(baseline_yield, dtype=bool)
        
        print(f"Processing {basin} - {crop}...")

        for red_sce in red_scenarios:
            sens_yield = ds_sens_yield["Yield"].sel(scenario=red_sce).where(mask.notnull())
            sens_N_exceedance = ds_sens_N_exceedance["N_exceedance"].sel(scenario=red_sce).where(mask.notnull())

            # Map the scenario string to the numeric value: e.g. Red_08 --> 0.8
            red_prop = float(red_sce.split('_')[1]) / 10.0  

            # Define the stopping conditions (Vectorized)
            # Condition 1: N_exceedance <= 0
            # Condition 2: Yield <= 60% of baseline (0.6 * baseline_yield)
            cond_n = sens_N_exceedance <= 0
            cond_yield = sens_yield <= (0.6 * baseline_yield)

            # Combine conditions and ensure we only consider pixels that haven't stopped yet
            stop_now = (cond_n | cond_yield) & (~stopped_mask) & mask.notnull()

            # Save results for pixels meeting the criteria for the FIRST time
            final_yield = xr.where(stop_now, sens_yield, final_yield)
            final_red_prop = xr.where(stop_now, red_prop, final_red_prop)

            # Update the tracker so we don't overwrite these pixels in the next scenario
            stopped_mask = stopped_mask | stop_now

            # Optional: If all pixels in the mask have stopped, we can break the scenario loop
            if stopped_mask.where(mask.notnull(), True).all():
                break

        # ================ Save the Results ==================
        output_dir_fert = os.path.join(red_dir, f"Red_prop/{basin}_{crop}_Fert_red_prop.nc")
        output_yield = os.path.join(red_dir, f"Red_prop/{basin}_{crop}_Yield_after_red.nc")
        os.makedirs(os.path.dirname(output_dir_fert), exist_ok=True)
        os.makedirs(os.path.dirname(output_yield), exist_ok=True)

        # Convert to datasets for saving
        ds_out_fert = final_red_prop.to_dataset(name="Fert_red_prop")
        ds_out_yield = final_yield.to_dataset(name="Yield_after_red")

        ds_out_fert.to_netcdf(output_dir_fert)
        ds_out_yield.to_netcdf(output_yield)
        
        print(f"Finished processing {basin} - {crop}")