# This code is used to:
# 1. Identify pixels where N, P cheminal ferilizers can still be increased
# 2. Create new fertilizer input files for the year 2010 - 2019

import xarray as xr
import numpy as np
import os

Basins = ["Yangtze"] # ["Indus", "Rhine", "LaPlata", "Yangtze"]
CropTypes = ["mainrice", "secondrice"] # ["mainrice", "secondrice", "maize", "winterwheat", "soybean"]
start_year = 2010
end_year = 2019

# To adjust the N input increase parameter
Inc_para = 1.4
output_inc_para = "Inc_14" 

# Input directories for data
Data_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"

# Reduced fertilizer data directory

# Rainfed 
# model_output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_1_Baseline_rainfed"
# excessive_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/3_1_Excessive_NP_rainfed"
# Output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/4_Fertilization_Red/4_2_Increased_Fert/Rainfed"
# Fert_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/4_Fertilization_Red/4_1_Reduced_Fert/Rainfed/Red_prop"

# # Sustainable Irrigation
model_output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_2_Sus_Irrigation"
excessive_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/3_2_Excessive_NP_irrigated"
Output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/4_Fertilization_Red/4_2_Increased_Fert/Irrigated"
Fert_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/4_Fertilization_Red/4_1_Reduced_Fert/Irrigated/Red_prop"

os.makedirs(f"{Output_dir}/{output_inc_para}", exist_ok=True)

for basin in Basins:

    for crop in CropTypes:

        # Load fertilizer input - N runoff ratio
        model_output_path = os.path.join(model_output_dir, f"{basin}_{crop}_annual.nc")
        excessive_path = os.path.join(excessive_dir, f"{basin}_{crop}_excessive_NP_losses.nc")
        if not os.path.exists(excessive_path) or not os.path.exists(model_output_path):
            print(f"Missing output file: {basin} - {crop}")
            continue
        # Load model outputs
        model_output_nc = xr.open_dataset(model_output_path)
        N_runoff = model_output_nc["N_Runoff"]

        # Load model outputs with sustainble irrigation rate
        excessive_nc = xr.open_dataset(excessive_path)

        # Step 1: Get the amount where the chemical N fertilzer input should be increased
        N_exceedance = excessive_nc["excessive_N"].where(excessive_nc["excessive_N"] > 0)
        P_exceedance = excessive_nc["excessive_P"].where(excessive_nc["excessive_P"] > 0)

        # Step 2: Calculate how much N should be increased
        if crop == "mainrice":
            cropname = "Rice"
            cropname2 = cropname
        if crop == "secondrice":
            cropname = "Rice"
            cropname2 = "Secondrice"
        if crop == "soybean":
            cropname = "Soybean"
            cropname2 = cropname
        if crop == "maize":
            cropname = "Maize"
            cropname2 = cropname
        if crop == "winterwheat":
            cropname = "Wheat"
            cropname2 = cropname

        fert_path = os.path.join(Fert_dir, f"{basin}_{cropname2}_Fert_2005-2020_FixRate.nc")
        fert_ds = xr.open_dataset(fert_path)
        var_Urea_N = fert_ds[f"{cropname}_Urea_N_application_rate"]
        var_Inorg_N = fert_ds[f"{cropname}_Inorg_N_application_rate"]
        var_Manure_N = fert_ds[f"{cropname}_Manure_N_application_rate"]
        var_Inorg_P = fert_ds[f"{cropname}_P_application_rate"]
        var_Manure_P = fert_ds[f"{cropname}_Manure_P_application_rate"]

        year_slice = slice(start_year, end_year)

        # 1) Input/runoff ratio
        var_total_N_input = var_Manure_N.fillna(0) + var_Inorg_N.fillna(0) + var_Urea_N.fillna(0)
        N_runoff, var_total_N_input = xr.align(N_runoff, var_total_N_input, join="outer")
        ratio = xr.where(var_total_N_input > 0, var_total_N_input/N_runoff, 0)
        N_input_runoff_ratio_mean = ratio.sel(year=year_slice).mean(dim="year", skipna=True)

        # 2) Calculate the increase rate
        N_exceedance, N_input_runoff_ratio = xr.align(N_exceedance, N_input_runoff_ratio_mean, join="outer")
        N_fert_inc_mean = xr.where(N_exceedance < 0, - N_exceedance * N_input_runoff_ratio_mean, 0) # only increase N fertilizer when P the critical value is not surpasssed
        N_fert_inc_mean = Inc_para * N_fert_inc_mean # For sensitivity  analysis
        
        N_fert_inc = xr.broadcast(N_fert_inc_mean, var_total_N_input)[0]
        N_fert_after_inc_prop = xr.where(var_total_N_input > 0, 1 + (N_fert_inc/var_total_N_input), 0)

        # Step 3-1: Update variables related to N input
        var_Urea_N, var_Inorg_N, var_Manure_N, N_fert_inc = xr.align(var_Urea_N, var_Inorg_N, var_Manure_N, N_fert_inc, join="outer")
        var_Urea_N_updated = var_Urea_N.copy()
        var_Inorg_N_updated = var_Inorg_N.copy()
        var_Manure_N_updated = var_Manure_N.copy()

        Urea  = var_Urea_N.sel(year=year_slice)
        Inorg = var_Inorg_N.sel(year=year_slice)
        Manure = var_Manure_N.sel(year=year_slice)

        # We assume all type of N inputs are increased equally
        Urea, N_fert_after_inc_prop = xr.align(Urea, N_fert_after_inc_prop, join="outer")
        Inorg, N_fert_after_inc_prop = xr.align(Inorg, N_fert_after_inc_prop, join="outer")
        Manure, N_fert_after_inc_prop = xr.align(Manure, N_fert_after_inc_prop, join="outer")

        Urea_after = Urea * N_fert_after_inc_prop
        Inorg_after = Inorg * N_fert_after_inc_prop
        Manure_after = Manure * N_fert_after_inc_prop

        # reindex RHS to match target time index before assigning into slice to avoid coordinate conflict
        target_time = var_Urea_N_updated.sel(year=year_slice).year
        Urea_after = Urea_after.reindex(year=target_time)
        Inorg_after = Inorg_after.reindex(year=target_time)
        Manure_after = Manure_after.reindex(year=target_time)

        var_Urea_N_updated.loc[dict(year=year_slice)] = Urea_after
        var_Inorg_N_updated.loc[dict(year=year_slice)] = Inorg_after
        var_Manure_N_updated.loc[dict(year=year_slice)] = Manure_after
        var_Total_inorg_N_updated = var_Urea_N_updated + var_Inorg_N_updated

        # Step 3-2: Update inorganic P fertilzer input
        # Keep the chemical P input

        # Manure P input increase using the same proportion as manure N increase
        var_Manure_P_updated = var_Manure_P.copy()
        Manure_P = var_Manure_P.sel(year=year_slice)
        Manure_P, N_fert_after_inc_prop = xr.align(Manure_P, N_fert_after_inc_prop, join="outer")
        Manure_P_after = (Manure_P * N_fert_after_inc_prop).clip(min=0.0)
        Manure_P_after = Manure_P_after.reindex(year=target_time)
        var_Manure_P_updated.loc[dict(year=year_slice)] = Manure_P_after
        
        # Step 4: Update and output new fertilizer files
        fert_ds[f"{cropname}_Urea_N_application_rate"] = var_Urea_N_updated
        fert_ds[f"{cropname}_Inorg_N_application_rate"] = var_Inorg_N_updated
        fert_ds[f"{cropname}_Total_inorg_N_application_rate"] = var_Total_inorg_N_updated
        fert_ds[f"{cropname}_Manure_P_application_rate"] = var_Manure_P_updated
        fert_ds[f"{cropname}_Manure_N_application_rate"] = var_Manure_N_updated

        output_nc = os.path.join(Output_dir, f"{output_inc_para}/{basin}_{cropname2}_Fert_2005-2020_FixRate.nc")
        fert_ds.to_netcdf(output_nc)
        print (f"{output_nc} was calculated and saved")