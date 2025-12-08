# This code is used to get the mask showing:
# 0 - Pixels with sustainbal irrigation rate and not excessive N, P losses
# 1 - Pixels with unsustainable irrigation 
# 2 - Pixels with excessive N 
# 3 - Pixels with excessive P   

import xarray as xr
import os

model_output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_1_Baseline_rainfed"
boundary_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/2_Critical_NP_losses"
irrigation_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/4_Analysis4Plotting/2_Excessive_rainfed"

basins = ["Rhine", "Indus", "LaPlata", "Yangtze"]
croptypes = ["mainrice", "secondrice", "maize", "soybean", "winterwheat"]

for basin in basins:

    critical_N_nc = f"{boundary_dir}/{basin}_crit_N_runoff_kgperha.nc"
    ds_crti_N = xr.open_dataset(critical_N_nc)
    critical_N_loss = ds_crti_N["critical_maincrop_N_runoff"]

    critical_P_nc = f"{boundary_dir}/{basin}_crit_P_runoff_kgperha.nc"
    ds_crti_P = xr.open_dataset(critical_P_nc)
    critical_P_loss = ds_crti_P["critical_maincrop_P_runoff"]

    for crop in croptypes:

        irrigation_nc = f"{irrigation_dir}/{basin}/Irrigation/{basin}_{crop}_monthly_Irri_Rate.nc"
        sus_irrigation_nc = f"{irrigation_dir}/{basin}/Irrigation/{basin}_{crop}_monthly_sus_Irri_Rate.nc"
        if not os.path.exists(irrigation_nc):
            print(f"{basin} does not have irrigation data for {crop}, skipping...")
            continue  

        ds_irri = xr.open_dataset(irrigation_nc)
        irrigation_rate = ds_irri["Irrigation_Rate"].sel(time=slice("2015-01-01", "2015-12-01")).sum(dim="time", skipna=True)
        ds_sus_irri = xr.open_dataset(sus_irrigation_nc)
        sus_irrigation_rate = ds_sus_irri["Irrigation_Rate"].sel(time=slice("2015-01-01", "2015-12-01")).sum(dim="time", skipna=True)
        excessive_irrigation_ratio = 100 * (irrigation_rate - sus_irrigation_rate)/sus_irrigation_rate 

        model_output_nc = f"{model_output_dir}/{basin}_{crop}_annual.nc"
        if not os.path.exists(model_output_nc):
            print(f"{basin} does not have model output for {crop}, skipping...")
            continue  
        ds_model = xr.open_dataset(model_output_nc)
        N_Runoff = ds_model["N_Runoff"].sel(year=slice("2010", "2019")).mean(dim="year", skipna=True)
        P_Runoff = ds_model["P_Runoff"].sel(year=slice("2010", "2019")).mean(dim="year", skipna=True)
        
        excessive_N = N_Runoff - critical_N_loss
        excessive_P = P_Runoff - critical_P_loss

        # assemble into one Dataset and add brief attributes
        ds_out = xr.Dataset({
            # "excessive_irrigation_ratio": excessive_irrigation_ratio,
            "excessive_N": excessive_N,
            "excessive_P": excessive_P,
        })

        # ds_out["excessive_irrigation_ratio"].attrs["long_name"] = "Irrigation ratio (applied - sus / sus) * 100 (%)"
        ds_out["excessive_N"].attrs["long_name"] = "Excessive N runoff "
        ds_out["excessive_P"].attrs["long_name"] = "Excessive P runoff "

        output_nc = f"{output_dir}/{basin}_{crop}_excessive_Irr_NP_losses.nc"
        ds_out.to_netcdf(output_nc)
        print(f"Saved sustainability variables for {basin} - {crop} to {output_nc}")