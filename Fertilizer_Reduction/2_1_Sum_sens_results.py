# This code is used to find out how much fertilzer should be reduced

import numpy as np
import os
import xarray as xr

Basins = ["Indus", "Rhine", "LaPlata", "Yangtze"]
CropTypes = ["mainrice", "soybean", "winterwheat"] # ["mainrice", "secondrice", "maize", "winterwheat", "soybean"]
red_scenarios = ["Red_01", "Red_02", "Red_03", "Red_04", "Red_05", "Red_06", "Red_07", "Red_08", "Red_09", "Red_10", "Red_11", "Red_12", "Red_13", "Red_14", "Red_15"]
start_year = 2010
end_year = 2019

Data_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
crit_loss_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/2_Critical_NP_losses/Method3"

# model output directory for rainfed field 
# model_output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_3_Rainfed"
# output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/4_Fertilization_Red/4_1_Reduced_Fert/Rainfed/Sens_Analysis"

# model output directory for irrigated field
model_output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_3_Sus_Irri_Red_Fert"
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/4_Fertilization_Red/4_1_Reduced_Fert/Irrigated/Sens_Analysis"

for basin in Basins:

    # Load basin range
    basin_mask_file = os.path.join(Data_dir, basin, f"range.nc")
    ds_basin_mask = xr.open_dataset(basin_mask_file)
    mask = ds_basin_mask["mask"]
    mask = mask.where(mask == 1.0, np.nan)

    for crop in CropTypes:

        # ===================== Load harvested area ======================
        if crop == "winterwheat":
            cropname = "WHEA"
        elif crop == "maize":
            cropname = "MAIZ"
        elif crop == "soybean":
            cropname = "SOYB"
        elif crop == "mainrice" and basin != "Yangtze":
            cropname = "RICE"
        elif crop == "mainrice" and basin == "Yangtze":
            cropname = "MAINRICE"
        elif crop == "secondrice":
            cropname = "SECONDRICE" 

        Total_HA_file = os.path.join(Data_dir, basin, f"Harvest_Area/{cropname}_Harvest_Area_05d_{basin}.nc")
        if not os.path.exists (Total_HA_file):
            print (f"Missing harvested area file for {crop} in basin {basin}")
            continue

        ds_total_HA = xr.open_dataset(Total_HA_file)
        Total_HA = ds_total_HA["Harvest_Area"]  # in ha
        Basin_mask = mask * Total_HA.where(Total_HA > 2500, np.nan) # only consider grid cells with more than 2500 ha harvested area

        #  ===================== Load critical N, P losses =====================
        if crop == "winterwheat":
            crop_crit_name = "Wheat"
        elif crop == "maize":
            crop_crit_name = "Maize"
        elif crop == "soybean":
            crop_crit_name = "Soybean"
        elif crop == "mainrice":
            crop_crit_name = "Rice"
        elif crop == "secondrice":
            crop_crit_name = "Rice" 
            
        crit_N_loss_file = os.path.join(crit_loss_dir, f"{crop_crit_name}/{basin}_crit_N_runoff_kgperha.nc")
        ds_crit_N_loss = xr.open_dataset(crit_N_loss_file)
        Crit_N_Runoff = ds_crit_N_loss["Critical_N_runoff"].where(Basin_mask>2500)

        crit_P_loss_file = os.path.join(crit_loss_dir, f"{crop_crit_name}/{basin}_crit_P_runoff_kgperha.nc")
        ds_crit_P_loss = xr.open_dataset(crit_P_loss_file)
        Crit_P_Runoff = ds_crit_P_loss["Critical_P_runoff"].where(Basin_mask>2500)

        # ================ Find the suitable fertilizer reduction scenario =================
        Yield_list = []
        N_exc_list = []
        P_exc_list = []
        scenario_names = []

        for scenario in red_scenarios:

            results_dir = os.path.join(model_output_dir, scenario)
            result_file = os.path.join(results_dir, f"{basin}_{crop}_annual.nc")

            if not os.path.exists(result_file):
                print(f"Missing {crop} for basin {basin} in scenario {scenario}")
                continue

            ds_fert = xr.open_dataset(result_file)

            Yield = ds_fert["Yield"].sel(year=slice(start_year, end_year))
            Avg_Yield = Yield.mean(dim="year", skipna=True).where(Basin_mask > 2500)

            N_Runoff = (ds_fert["N_Runoff"].sel(year=slice(start_year, end_year)).mean(dim="year", skipna=True).where(Basin_mask > 2500))
            P_Runoff = (ds_fert["P_Runoff"].sel(year=slice(start_year, end_year)).mean(dim="year", skipna=True).where(Basin_mask > 2500))

            N_Exceedance = (N_Runoff - Crit_N_Runoff).rename("N_exceedance")
            P_Exceedance = (P_Runoff - Crit_P_Runoff).rename("P_exceedance")

            # add scenario dimension
            Avg_Yield = Avg_Yield.expand_dims(scenario=[scenario])
            N_Exceedance = N_Exceedance.expand_dims(scenario=[scenario])
            P_Exceedance = P_Exceedance.expand_dims(scenario=[scenario])

            Yield_list.append(Avg_Yield)
            N_exc_list.append(N_Exceedance)
            P_exc_list.append(P_Exceedance)
            scenario_names.append(scenario)

        Yield_all = xr.concat(Yield_list, dim="scenario")
        N_Exceedance_all = xr.concat(N_exc_list, dim="scenario")
        P_Exceedance_all = xr.concat(P_exc_list, dim="scenario")

        output_Yield_file = os.path.join(output_dir, f"{basin}_{crop}_Yields.nc")
        output_N_Exceedance_file = os.path.join(output_dir, f"{basin}_{crop}_N_Exceedance.nc")
        output_P_Exceedance_file = os.path.join(output_dir, f"{basin}_{crop}_P_Exceedance.nc")

        Yield_all.to_netcdf(output_Yield_file)
        N_Exceedance_all.to_netcdf(output_N_Exceedance_file)
        P_Exceedance_all.to_netcdf(output_P_Exceedance_file)

        print (f"Processed {crop} in basin {basin} for all fertilizer reduction scenarios")