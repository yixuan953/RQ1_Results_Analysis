# This code is used to get how much fertilizer can (should) be increased to increase the crop yield:
# Here we go through each fertilizer incuctin scenario, the loop stops when: N_exceedance >= 0


import pandas as pd
import numpy as np
import xarray as xr
import os

Basins = ["Indus", "Rhine", "LaPlata", "Yangtze"]
CropTypes = ["mainrice", "secondrice", "maize", "winterwheat", "soybean"]
inc_scenarios = ["Inc_01", "Inc_02", "Inc_03", "Inc_04", "inc_05", "inc_06", "inc_07", "inc_08", "inc_09", "inc_10", "inc_11", "inc_12", "inc_13", "inc_14", "inc_15"]

baseline_sce_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/4_Analysis4Plotting/0_Summary/1_Baseline"

# Irrigated field
# inc_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/4_Fertilization_inc/4_2_Increased_Fert/Irrigated" 
# yield_var = "Avg_Yield_Irrigated"

# Rainfed field
inc_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/4_Fertilization_inc/4_2_Increased_Fert/Rainfed" 
yield_var = "Avg_Yield_Rainfed"

for basin in Basins:
    for crop in CropTypes:

        # ================ Read the baseline yield ==================
        baseline_nc = os.path.join(baseline_sce_dir, f"{basin}_{crop}_summary_baseline.nc")
        if not os.path.exists(baseline_nc):
            print(f"Baseline file does not exist: {baseline_nc}")
            continue

        ds_baseline = xr.open_dataset(baseline_nc)
        basin_mask = ds_baseline["Basin_mask"]
        HA = ds_baseline["Total_HA"] # ha
        mask = basin_mask.where(HA > 2500, np.nan) # only consider grid cells with more than 2500 ha harvested area


        # ========= Loop through each fertilizer scenario ===
        sens_Yield_nc = os.path.join(inc_dir, f"Sens_Analysis/{basin}_{crop}_Yields.nc")
        sens_N_exceedance_nc = os.path.join(inc_dir, f"Sens_Analysis/{basin}_{crop}_N_Exceedance.nc")
        if not os.path.exists(sens_Yield_nc) or not os.path.exists(sens_N_exceedance_nc):
            print(f"Sensitivity analysis files do not exist for {basin} - {crop}")
            continue    

        ds_sens_yield = xr.open_dataset(sens_Yield_nc)
        ds_sens_N_exceedance = xr.open_dataset(sens_N_exceedance_nc)

        # Initialize result grids with NaN or a flag value
        final_yield = baseline_yield.copy() 
        final_inc_prop = xr.full_like(baseline_yield, 0.0)
        stopped_mask = xr.zeros_like(baseline_yield, dtype=bool)
        
        print(f"Processing {basin} - {crop}...")

        for inc_sce in inc_scenarios:
            sens_yield = ds_sens_yield["Yield"].sel(scenario=inc_sce).where(mask.notnull())
            sens_N_exceedance = ds_sens_N_exceedance["N_exceedance"].sel(scenario=inc_sce).where(mask.notnull())

            # Map the scenario string to the numeric value: e.g. inc_05 --> 0.5
            inc_prop = float(inc_sce.split('_')[1]) / 10.0  

            # Define the stopping conditions (Vectorized)
            # Condition 1: N_exceedance <= 0
            # Condition 2: Yield <= 50% of baseline (0.5 * baseline_yield)
            cond_n = sens_N_exceedance <= 0
            cond_yield = sens_yield <= (0.5 * baseline_yield)

            # Combine conditions and ensure we only consider pixels that haven't stopped yet
            stop_now = (cond_n | cond_yield) & (~stopped_mask) & mask.notnull()

            # Save results for pixels meeting the criteria for the FIRST time
            final_yield = xr.where(stop_now, sens_yield, final_yield)
            final_inc_prop = xr.where(stop_now, inc_prop, final_inc_prop)

            # Update the tracker so we don't overwrite these pixels in the next scenario
            stopped_mask = stopped_mask | stop_now

            # Optional: If all pixels in the mask have stopped, we can break the scenario loop
            if stopped_mask.where(mask.notnull(), True).all():
                break

        # ================ Save the Results ==================
        output_dir_fert = os.path.join(inc_dir, f"inc_prop/{basin}_{crop}_Fert_inc_prop.nc")
        output_yield = os.path.join(inc_dir, f"inc_prop/{basin}_{crop}_Yield_after_inc.nc")
        os.makedirs(os.path.dirname(output_dir_fert), exist_ok=True)
        os.makedirs(os.path.dirname(output_yield), exist_ok=True)

        # Convert to datasets for saving
        ds_out_fert = final_inc_prop.to_dataset(name="Fert_inc_prop")
        ds_out_yield = final_yield.to_dataset(name="Yield_after_inc")

        ds_out_fert.to_netcdf(output_dir_fert)
        ds_out_yield.to_netcdf(output_yield)
        
        print(f"Finished processing {basin} - {crop}")