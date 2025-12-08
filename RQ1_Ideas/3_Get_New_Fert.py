# This code is used to:
# 1. Identify pixels where N, P cheminal ferilizers should be reduced 
# 2. Create new fertilizer input files for the year 1986 - 2015

import xarray as xr
import numpy as np
import os

Basins = ["Indus", "Rhine", "LaPlata", "Yangtze"]
CropTypes = ["mainrice", "secondrice", "maize", "winterwheat", "soybean"]
start_year = 1986
end_year = 2015

# Input directories for data
Unsus_Irri_ouput_dir = r"C:\Users\zhou111\OneDrive - Wageningen University & Research\0_Project\RQ1\2_Model_output\Part1_Unsus_Irri\Output_nc"
Sus_Irri_ouput_dir = r"C:\Users\zhou111\OneDrive - Wageningen University & Research\0_Project\RQ1\2_Model_output\Part2_Sus_Irri\Output_nc"
Data_dir = r"C:\Users\zhou111\OneDrive - Wageningen University & Research\0_Project\RQ1\1_Data_Methods\2_Data"
Output_dir = r"C:\Users\zhou111\OneDrive - Wageningen University & Research\0_Project\RQ1\2_Model_output\Output_adjust_fert"

# To adjust the N input reduction
Red_para = 1.0
output_red_para = "Red_org" # "Red_12" "Red_14" "Red_18", etc.

for basin in Basins:

    # Load boundary datasets and subset to 1986-2015
    try:
        N_leach_boundary_nc = xr.open_dataset(os.path.join(Data_dir, basin, "Hydro", f"{basin}_N_critical_leaching_annual.nc")).sel(time=slice(str(start_year), str(end_year)))
        P_leach_boundary_nc = xr.open_dataset(os.path.join(Data_dir, basin, "Hydro", f"{basin}_P_critical_leaching_annual.nc")).sel(time=slice(str(start_year), str(end_year)))
        N_runoff_boundary_nc = xr.open_dataset(os.path.join(Data_dir, basin, "Hydro", f"{basin}_N_critical_runoff_annual.nc")).sel(time=slice(str(start_year), str(end_year)))
        P_runoff_boundary_nc = xr.open_dataset(os.path.join(Data_dir, basin, "Hydro", f"{basin}_P_critical_runoff_annual.nc")).sel(time=slice(str(start_year), str(end_year)))
    except FileNotFoundError:
        print(f"Boundary files missing for {basin}, skipping basin.")
        continue

    for crop in CropTypes:

        # Load model outputs with unsustainable irrigation rate 
        unsus_irri_path = os.path.join(Unsus_Irri_ouput_dir, f"{basin}_{crop}_annual.nc")
        if not os.path.exists(unsus_irri_path):
            print(f"Missing output file: {unsus_irri_path}")
            continue
        unsus_irri_nc = xr.open_dataset(unsus_irri_path)

        # Load model outputs with sustainble irrigation rate
        sus_irri_path = os.path.join(Sus_Irri_ouput_dir, f"{basin}_{crop}_annual.nc")
        if not os.path.exists(sus_irri_path):
            print(f"Missing output file: {sus_irri_path}")
            continue
        sus_irri_nc = xr.open_dataset(sus_irri_path)

        # Step 1-1: Calculate how much N losses through runoff and leaching should be reduced
        N_leach  = sus_irri_nc["N_leach"]
        N_runoff = sus_irri_nc["N_surf"].fillna(0) + sus_irri_nc["N_sub"].fillna(0)

        N_leach_boundary  = N_leach_boundary_nc["OUT_BASEFLOW"]
        N_runoff_boundary = N_runoff_boundary_nc["OUT_RUNOFF"]

        N_leach_boundary = N_leach_boundary.assign_coords(time=N_leach_boundary["time.year"])
        N_runoff_boundary = N_runoff_boundary.assign_coords(time=N_runoff_boundary["time.year"])

        N_leach_exceed = xr.where(N_leach - N_leach_boundary > 0, N_leach - N_leach_boundary, 0)
        N_runoff_exceed = xr.where(N_runoff - N_runoff_boundary > 0, N_runoff - N_runoff_boundary, 0)

        # Step 1-2: Calcualte how much N uptake has reduced due to water deficiency
        N_uptake_sus = sus_irri_nc["N_uptake"]
        N_uptake_unsus = unsus_irri_nc["N_uptake"]
        N_uptake_red = xr.where(N_uptake_unsus - N_uptake_sus > 0, N_uptake_unsus - N_uptake_sus, 0)

        # Step 1-3: Caculate how much N chemical fertilizer should be reduced 
        N_fert_red = N_leach_exceed + N_runoff_exceed + N_uptake_red      

        # Step 2: Get the mask where the chemical P fertilzer input should be stopped
        P_leach_boundary  = P_leach_boundary_nc["OUT_BASEFLOW"]
        P_runoff_boundary = P_runoff_boundary_nc["OUT_RUNOFF"]

        P_runoff_boundary = P_runoff_boundary.assign_coords(time=P_runoff_boundary["time.year"])
        P_leach_boundary = P_leach_boundary.assign_coords(time=P_leach_boundary["time.year"])

        P_leach  = sus_irri_nc["P_leach"]
        P_runoff = sus_irri_nc["P_surf"].fillna(0) + sus_irri_nc["P_sub"].fillna(0)

        P_leach_exceed = P_leach - P_leach_boundary
        P_runoff_exceed = P_runoff - P_runoff_boundary

        P_leach_exceed_mean  = P_leach_exceed.mean(dim="time", skipna=True)
        P_runoff_exceed_mean = P_runoff_exceed.mean(dim="time", skipna=True)

        mask_P_fert = xr.where(
            (P_leach_exceed_mean > 0)|
            (P_runoff_exceed_mean > 0), 
            0, 1
        )

        # Step 3: Update the fertilzer input file
        if crop == "mainrice" or crop == "secondrice":
            cropname = "Rice"
        if crop == "soybean":
            cropname = "Soybean"
        if crop == "maize":
            cropname = "Maize"
        if crop == "winterwheat":
            cropname = "Wheat"

        fert_path = os.path.join(Data_dir,basin,"Fertilization",f"{basin}_{cropname}_Fert_1981-2016.nc")
        fert_ds = xr.open_dataset(fert_path)
        fert_ds = fert_ds.rename({"year": "time"})
        var_Urea_N = fert_ds["Urea_N_application_rate"]
        var_Inorg_N = fert_ds["Inorg_N_application_rate"]
        var_Inorg_P = fert_ds["P_application_rate"]

        year_slice = slice(start_year, end_year)

        # Step 3-1: Update variables related to N input
        var_Urea_N, var_Inorg_N, N_fert_red = xr.align(var_Urea_N, var_Inorg_N, N_fert_red, join="outer")
        var_Urea_N_updated = var_Urea_N.copy()
        var_Inorg_N_updated = var_Inorg_N.copy()
        Urea  = var_Urea_N.sel(time=year_slice)
        Inorg = var_Inorg_N.sel(time=year_slice)
        Red = Red_para * N_fert_red.sel(time=year_slice)

        # Reduce urea input first, then other inorganic N fertilzer, until there's no inorganic N fertilizer available
        Urea_after = xr.where(Urea >= Red, Urea - Red, 0)
        Remaining_red = xr.where(Urea >= Red, 0, Red - Urea)
        Inorg_after = xr.where(Inorg >= Remaining_red, Inorg - Remaining_red, 0)

        var_Urea_N_updated.loc[dict(time=year_slice)] = Urea_after
        var_Inorg_N_updated.loc[dict(time=year_slice)] = Inorg_after
        var_Total_N_updated = var_Urea_N_updated + var_Inorg_N_updated

        # Step 3-2: Update inorganic P fertilzer input
        var_Inorg_P_updated = var_Inorg_P.copy()
        var_Inorg_P_updated_sel = var_Inorg_P_updated.sel(time=year_slice)
        mask_P_fert_aligned, var_Inorg_P_updated_sel = xr.align(mask_P_fert, var_Inorg_P_updated_sel, join="right")
        var_Inorg_P_updated.loc[dict(time=year_slice)] = var_Inorg_P_updated_sel * mask_P_fert_aligned

        # Step 4: Update and output new fertilizer files
        fert_ds["Urea_N_application_rate"] = var_Urea_N_updated
        fert_ds["Inorg_N_application_rate"] = var_Inorg_N_updated
        fert_ds["Total_inorg_N_application_rate"] = var_Total_N_updated
        fert_ds["P_application_rate"] = var_Inorg_P_updated

        output_nc = os.path.join(Output_dir, f"{basin}_{crop}_Fert_{output_red_para}.nc")
        fert_ds.to_netcdf(output_nc)
        print (f"{output_nc} was calculated and saved")