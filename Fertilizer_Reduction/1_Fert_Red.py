# This code is used to:
# 1. Identify pixels where N, P cheminal ferilizers should be reduced 
# 2. Create new fertilizer input files for the year 1986 - 2015

import xarray as xr
import numpy as np
import os

Basins = ["Indus", "Rhine", "LaPlata", "Yangtze"]
CropTypes = ["mainrice", "secondrice", "maize", "winterwheat", "soybean"]
start_year = 2010
end_year = 2019

# To adjust the N input reduction
Red_para = 1.2
output_red_para = "Red_12" # e.g., "Red_12", "Red_08", "Red_org"

# Input directories for data
Data_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"

# Rainfed 
model_output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_1_Baseline_rainfed"
excessive_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/4_Analysis4Plotting/2_Excessive_rainfed"
Output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/4_Analysis4Plotting/3_Fert_after_Red_rainfed"

# # # Sustainable Irrigation
# model_output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_2_Sus_Irrigation"
# excessive_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/4_Analysis4Plotting/2_Excessive_with_sus_Irri"
# Output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/4_Analysis4Plotting/3_Fert_after_Red"


for basin in Basins:

    for crop in CropTypes:

        # Load fertilizer input - N runoff ratio
        model_output_path = os.path.join(model_output_dir, f"{basin}_{crop}_annual.nc")
        excessive_path = os.path.join(excessive_dir, f"{basin}_{crop}_excessive_Irr_NP_losses.nc")
        if not os.path.exists(excessive_path) or not os.path.exists(model_output_path):
            print(f"Missing output file: {basin} - {crop}")
            continue
        # Load model outputs
        model_output_nc = xr.open_dataset(model_output_path)
        N_runoff = model_output_nc["N_Runoff"]

        # Load model outputs with sustainble irrigation rate
        excessive_nc = xr.open_dataset(excessive_path)

        # Step 1: Get the amount where the chemical N fertilzer input should be reduced
        N_exceedance = excessive_nc["excessive_N"]
        P_exceedance = excessive_nc["excessive_P"]

        # Step 2: Calculate how much N should be reduced
        if crop == "mainrice" or crop == "secondrice":
            cropname = "Rice"
        if crop == "soybean":
            cropname = "Soybean"
        if crop == "maize":
            cropname = "Maize"
        if crop == "winterwheat":
            cropname = "Wheat"

        fert_path = os.path.join(Data_dir,basin,"Fertilization",f"{basin}_{cropname}_Fert_2005-2020_FixRate.nc")
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


        # 2) Calculate the reuction rate
        N_exceedance, N_input_runoff_ratio = xr.align(N_exceedance, N_input_runoff_ratio_mean, join="outer")
        N_fert_red_mean = xr.where(N_exceedance > 0, N_exceedance * N_input_runoff_ratio_mean, 0) # only reduce N fertilizer when there's N exceedance
        N_fert_red_mean = Red_para * N_fert_red_mean # For sensitivity  analysis
        
        N_fert_red = xr.broadcast(N_fert_red_mean, var_total_N_input)[0]
        N_fert_after_red_prop = xr.where(var_total_N_input > 0, 1 - (N_fert_red/var_total_N_input), 0)
        N_fert_after_red_prop = xr.where(N_fert_after_red_prop < 0, 0, N_fert_after_red_prop)

        mask_P_fert = xr.where(P_exceedance > 0, 0, 1) # mask for P fertilizer reduction

        # Step 3-1: Update variables related to N input
        var_Urea_N, var_Inorg_N, var_Manure_N, N_fert_red = xr.align(var_Urea_N, var_Inorg_N, var_Manure_N, N_fert_red, join="outer")
        var_Urea_N_updated = var_Urea_N.copy()
        var_Inorg_N_updated = var_Inorg_N.copy()
        var_Manure_N_updated = var_Manure_N.copy()

        Urea  = var_Urea_N.sel(year=year_slice)
        Inorg = var_Inorg_N.sel(year=year_slice)
        Manure = var_Manure_N.sel(year=year_slice)

        # We assume all type of N inputs are reduced equally
        Urea, N_fert_after_red_prop = xr.align(Urea, N_fert_after_red_prop, join="outer")
        Inorg, N_fert_after_red_prop = xr.align(Inorg, N_fert_after_red_prop, join="outer")
        Manure, N_fert_after_red_prop = xr.align(Manure, N_fert_after_red_prop, join="outer")

        Urea_after = Urea * N_fert_after_red_prop
        Inorg_after = Inorg * N_fert_after_red_prop
        Manure_after = Manure * N_fert_after_red_prop

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
        # Stop inputting chemical P
        var_Inorg_P_updated = var_Inorg_P.copy()
        var_Inorg_P_updated_sel = var_Inorg_P_updated.sel(year=year_slice)
        var_Inorg_P_updated_sel, mask_P_fert_aligned = xr.align(var_Inorg_P_updated_sel, mask_P_fert, join="outer")
        var_Inorg_P_updated.loc[dict(year=year_slice)] = var_Inorg_P_updated_sel * mask_P_fert_aligned

        # Manure P input reduced using the same proportion as manure N reduction
        var_Manure_P_updated = var_Manure_P.copy()
        Manure_P = var_Manure_P.sel(year=year_slice)
        Manure_P, N_fert_after_red_prop = xr.align(Manure_P, N_fert_after_red_prop, join="outer")
        Manure_P_after = (Manure_P * N_fert_after_red_prop).clip(min=0.0)
        Manure_P_after = Manure_P_after.reindex(year=target_time)
        var_Manure_P_updated.loc[dict(year=year_slice)] = Manure_P_after
        
        # Step 4: Update and output new fertilizer files
        fert_ds[f"{cropname}_Urea_N_application_rate"] = var_Urea_N_updated
        fert_ds[f"{cropname}_Inorg_N_application_rate"] = var_Inorg_N_updated
        fert_ds[f"{cropname}_Total_inorg_N_application_rate"] = var_Total_inorg_N_updated
        fert_ds[f"{cropname}_P_application_rate"] = var_Inorg_P_updated
        fert_ds[f"{cropname}_Manure_P_application_rate"] = var_Manure_P_updated
        fert_ds[f"{cropname}_Manure_N_application_rate"] = var_Manure_N_updated


        output_nc = os.path.join(Output_dir, f"{output_red_para}/{basin}_{cropname}_Fert_2005-2020_FixRate.nc")
        fert_ds.to_netcdf(output_nc)
        print (f"{output_nc} was calculated and saved")