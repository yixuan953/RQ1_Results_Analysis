# This code is used to get the mean excessive N and P losses [kg/ha] for each crop in each basin over 2010-2019

import xarray as xr
import os

boundary_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/2_Critical_NP_losses/Method3"
data_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
input_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/4_Analysis4Plotting/0_Summary"

# Rainfed scenario
model_output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_1_Baseline_rainfed"
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/3_1_Excessive_NP_rainfed"

# Sustainable irrigated scenario
# model_output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_2_Sus_Irrigation"
# output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/3_2_Excessive_NP_irrigated"

basins = [ "Indus", "LaPlata", "Yangtze", "Rhine"]
croptypes = ["mainrice", "secondrice", "maize", "soybean", "winterwheat"]

for basin in basins:
    for crop in croptypes:

        if crop == "secondrice" or crop == "mainrice":
            crop_name = "Rice"
        elif crop == "maize":
            crop_name = "Maize"
        elif crop == "soybean":
            crop_name = "Soybean"
        elif crop == "winterwheat":
            crop_name = "Wheat"

        input_file = os.path.join(input_dir, f"{basin}_{crop}_summary_baseline.nc") # Baseline scenario
        if not os.path.exists(input_file):
            print(f"{basin} basin does not have {crop}")
            continue
        ds_input = xr.open_dataset(input_file)
        Basin_mask = ds_input["Basin_mask"].where(ds_input["Total_HA"] > 2500) #  only consider pixels with > 2500 ha of this crop in the basin

        critical_N_nc = f"{boundary_dir}/{crop_name}/{basin}_crit_N_runoff_kgperha.nc"
        ds_crti_N = xr.open_dataset(critical_N_nc)
        critical_N_loss = ds_crti_N["Critical_N_runoff"].where(Basin_mask == 1)

        critical_P_nc = f"{boundary_dir}/{crop_name}/{basin}_crit_P_runoff_kgperha.nc"
        ds_crti_P = xr.open_dataset(critical_P_nc)
        critical_P_loss = ds_crti_P["Critical_P_runoff"].where(Basin_mask == 1)

        model_output_nc = f"{model_output_dir}/{basin}_{crop}_annual.nc"
        if not os.path.exists(model_output_nc):
            print(f"{basin} does not have model output for {crop}, skipping...")
            continue  
        ds_model = xr.open_dataset(model_output_nc)
        N_Runoff = ds_model["N_Runoff"].sel(year=slice("2010", "2019")).mean(dim="year", skipna=True).where(Basin_mask == 1)
        P_Runoff = ds_model["P_Runoff"].sel(year=slice("2010", "2019")).mean(dim="year", skipna=True).where(Basin_mask == 1)
        
        excessive_N = N_Runoff - critical_N_loss
        excessive_P = P_Runoff - critical_P_loss

        # assemble into one Dataset and add brief attributes
        ds_out = xr.Dataset({
            # "excessive_irrigation_ratio": excessive_irrigation_ratio,
            "excessive_N": excessive_N,
            "excessive_P": excessive_P,
        })

        ds_out["excessive_N"].attrs["long_name"] = "Excessive N runoff "
        ds_out["excessive_P"].attrs["long_name"] = "Excessive P runoff "

        output_nc = f"{output_dir}/{basin}_{crop}_excessive_NP_losses.nc"
        ds_out.to_netcdf(output_nc)
        print(f"Saved sustainability variables for {basin} - {crop} to {output_nc}")