# This code is used to compare the cropland runoff from GLOBIOM and WOFOST models:
# 7_1: Calculate the cropland runoff for each crop (global) [ktons]
# 7_2: Cut the range, plot and compare to WOFOST results [ktons]

import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

data_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
globiom_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/Globiom"
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/2_Model_Adj/GLOBIOM"

basins = ["Indus", "Rhine", "LaPlata", "Yangtze"]  # ["Indus", "Rhine", "LaPlata", "Yangtze"]
croptypes = ["Maize", "Rice", "Wheat", "Soybean"] 

for basin in basins:
    for crop in croptypes:

        if crop == "Rice":
            cropname = "RICE"
            crop_mask_name = "mainrice"
        elif crop == "Maize":
            cropname = "MAIZ"
            crop_mask_name = "maize"
        elif crop == "Soybean":
            cropname = "SOYB"
            crop_mask_name = "soybean"
        elif crop == "Wheat":
            cropname = "WHEA"
            crop_mask_name = "winterwheat"

        crop_mask_file_1 = f"{data_dir}/{basin}/Harvest_Area/{cropname}_Harvest_Area_05d_{basin}.nc"
        crop_mask_file_2 = f"{data_dir}/{basin}/Mask/{basin}_{crop_mask_name}_mask.nc"

        if not os.path.exists(crop_mask_file_1) or not os.path.exists(crop_mask_file_2):
            print(f"Skipping: Files for {crop} in {basin} do not exist.")
            continue

        crop_mask_nc_1 = xr.open_dataset(crop_mask_file_1)
        crop_HA_1 = crop_mask_nc_1["Harvest_Area"].values
        crop_mask_1 = np.where(crop_HA_1 > 2500, 1, np.nan)

        crop_mask_nc_2 = xr.open_dataset(crop_mask_file_2)
        crop_HA_2 = crop_mask_nc_2["TSUM1"].values
        crop_mask_2 = np.where(crop_HA_2 > 0, 1, np.nan)

        crop_mask = crop_mask_1 * crop_mask_2

        # Extract lat and lon from crop mask
        target_lat = crop_mask_nc_1["lat"].values
        target_lon = crop_mask_nc_1["lon"].values
        lat_min = crop_mask_nc_1["lat"].values.min()
        lat_max = crop_mask_nc_1["lat"].values.max()
        lon_min = crop_mask_nc_1["lon"].values.min()
        lon_max = crop_mask_nc_1["lon"].values.max() 

        # Load GLOBIOM cropland runoff data
        globiom_runoff_file = os.path.join(globiom_dir, f"{crop}_GLOBIOM_cropland_runoff_2020.nc")
        globiom_nc = xr.open_dataset(globiom_runoff_file, decode_times=False)
        globiom_N_runoff = globiom_nc["GLOBIOM_cropland_N_runoff_2020"].sel(lat=slice(lat_max, lat_min),lon=slice(lon_min, lon_max))
        globiom_N_leaching = globiom_nc["GLOBIOM_cropland_N_leaching_2020"].sel(lat=slice(lat_max, lat_min),lon=slice(lon_min, lon_max))
        globiom_NH3NOx = globiom_nc["GLOBIOM_cropland_NH3NOx_2020"].sel(lat=slice(lat_max, lat_min),lon=slice(lon_min, lon_max))
        globiom_N2 = globiom_nc["GLOBIOM_cropland_N2_2020"].sel(lat=slice(lat_max, lat_min),lon=slice(lon_min, lon_max))

        globiom_P_runoff = globiom_nc["GLOBIOM_cropland_P_runoff_2020"].sel(lat=slice(lat_max, lat_min),lon=slice(lon_min, lon_max))

        globiom_N_runoff = globiom_N_runoff * crop_mask
        globiom_P_runoff = globiom_P_runoff * crop_mask
        globiom_N_leaching = globiom_N_leaching * crop_mask
        globiom_NH3NOx = globiom_NH3NOx * crop_mask
        globiom_N2 = globiom_N2 * crop_mask

        # Sum up the total runoff in the basin and plot the runoff maps
        globiom_N_basin_runoff = globiom_N_runoff.sum(dim=["lat","lon"]) # ktons N
        globiom_N_basin_leaching = globiom_N_leaching.sum(dim=["lat","lon"]) # ktons N
        globiom_N_basin_NH3NOx = globiom_NH3NOx.sum(dim=["lat","lon"]) # ktons N
        globiom_N_basin_N2 = globiom_N2.sum(dim=["lat","lon"]) # ktons N

        globiom_P_basin_runoff = globiom_P_runoff.sum(dim=["lat","lon"]) # ktons P


        print(f"{basin} - {crop} - GLOBIOM N Runoff (ktons): {globiom_N_basin_runoff.values}")
        print(f"{basin} - {crop} - GLOBIOM N Leaching (ktons): {globiom_N_basin_leaching.values}")
        print(f"{basin} - {crop} - GLOBIOM NH3 + NOx (ktons): {globiom_N_basin_NH3NOx.values}")
        print(f"{basin} - {crop} - GLOBIOM N2  (ktons): {globiom_N_basin_N2.values}")
        print(f"{basin} - {crop} - GLOBIOM P Runoff (ktons): {globiom_P_basin_runoff.values}")
        
        # fig, ax = plt.subplots(1, 2, figsize=(12, 5))
        # globiom_N_runoff.plot(ax=ax[0], cmap='viridis')
        # ax[0].set_title(f"GLOBIOM {crop} N Runoff in {basin} (ktons)")
        # globiom_P_runoff.plot(ax=ax[1], cmap='viridis')
        # ax[1].set_title(f"GLOBIOM {crop} P Runoff in {basin} (ktons)")
        # plt.tight_layout()
        # output_figure = os.path.join(output_dir, f"{basin}_{crop}_GLOBIOM_runoff_maps.png")
        # plt.savefig(output_figure)
        # plt.close()

