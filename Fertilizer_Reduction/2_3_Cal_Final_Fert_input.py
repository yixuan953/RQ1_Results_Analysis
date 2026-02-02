# This code is used to get the final fertilizer input files after reduction

import xarray as xr
import numpy as np
import os

Basins = ["Indus", "Rhine", "LaPlata", "Yangtze"]
CropTypes = ["mainrice", "secondrice", "maize", "winterwheat", "soybean"]
start_year = 2010
end_year = 2019

# Input directories for data
Data_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"

# Rainfed 
model_output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_1_Baseline_rainfed"
excessive_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/3_1_Excessive_NP_rainfed"
Output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/4_Fertilization_Red/4_1_Reduced_Fert/Rainfed"

# Sustainable Irrigated
# model_output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_2_Sus_Irrigation"
# excessive_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/3_2_Excessive_NP_irrigated"
# Output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/4_Fertilization_Red/4_1_Reduced_Fert/Irrigated"

os.makedirs(f"{Output_dir}/Red_prop", exist_ok=True)

for basin in Basins:

    for crop in CropTypes:

        # Load baseline N, P exceedance
        model_output_path = os.path.join(model_output_dir, f"{basin}_{crop}_annual.nc")
        excessive_path = os.path.join(excessive_dir, f"{basin}_{crop}_excessive_NP_losses.nc")
        if not os.path.exists(excessive_path) or not os.path.exists(model_output_path):
            print(f"Missing output file: {basin} - {crop}")
            continue

        # Load model outputs
        model_output_nc = xr.open_dataset(model_output_path)
        N_runoff = model_output_nc["N_Runoff"]
        excessive_nc = xr.open_dataset(excessive_path)
        N_exceedance = excessive_nc["excessive_N"].where(excessive_nc["excessive_N"] > 0)
        P_exceedance = excessive_nc["excessive_P"].where(excessive_nc["excessive_P"] > 0)

        # Load reduction proportion file
        red_prop_dir = os.path.join(Output_dir, f"Red_prop/{basin}_{crop}_Fert_red_prop.nc")
        if not os.path.exists(red_prop_dir):
            print(f"Missing reduction proportion file: {basin} - {crop}")
            continue
        red_prop_nc = xr.open_dataset(red_prop_dir)
        N_red_prop = red_prop_nc["Fert_red_prop"]

        # Load original fertilizer input files
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

        # 1) Calculate the original reduction rate
        var_total_N_input = var_Manure_N.fillna(0) + var_Inorg_N.fillna(0) + var_Urea_N.fillna(0)
        N_runoff, var_total_N_input = xr.align(N_runoff, var_total_N_input, join="outer")
        ratio = xr.where(var_total_N_input > 0, var_total_N_input/N_runoff, 0)
        N_input_runoff_ratio_mean = ratio.sel(year=year_slice).mean(dim="year", skipna=True)

        N_exceedance, N_input_runoff_ratio = xr.align(N_exceedance, N_input_runoff_ratio_mean, join="outer")
        N_fert_red_mean = xr.where(N_exceedance > 0, N_exceedance * N_input_runoff_ratio_mean, 0) # only reduce N fertilizer when there's N exceedance
        
        # 2) Apply the reduction proportion
        N_fert_red_mean = N_red_prop * N_fert_red_mean # Apply the reduction proportion
        N_fert_red = xr.broadcast(N_fert_red_mean, var_total_N_input)[0]
        N_fert_after_red_prop = xr.where(var_total_N_input > 0, 1 - (N_fert_red/var_total_N_input), 0)
        N_fert_after_red_prop = xr.where(N_fert_after_red_prop < 0, 0, N_fert_after_red_prop)

        # 3): Update variables related to N input
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

        # 4) Update variables related to P input
        mask_P_fert = xr.where(P_exceedance > 0, 0, 1) # mask for P fertilizer reduction
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

        # 5): Update and output new fertilizer files
        fert_ds[f"{cropname}_Urea_N_application_rate"] = var_Urea_N_updated
        fert_ds[f"{cropname}_Inorg_N_application_rate"] = var_Inorg_N_updated
        fert_ds[f"{cropname}_Total_inorg_N_application_rate"] = var_Total_inorg_N_updated
        fert_ds[f"{cropname}_P_application_rate"] = var_Inorg_P_updated
        fert_ds[f"{cropname}_Manure_P_application_rate"] = var_Manure_P_updated
        fert_ds[f"{cropname}_Manure_N_application_rate"] = var_Manure_N_updated

        output_nc = os.path.join(Output_dir, f"Red_prop/{basin}_{cropname}_Fert_2005-2020_FixRate.nc")
        fert_ds.to_netcdf(output_nc)
        print (f"{output_nc} was calculated and saved")
