# This code is used to compare the outputs of WOFOST-Nutrient (N, P runoff) and the IMAGE model
# WOFOST-Nutrient: Total N, P runoff of each crop type [kg/ha] --> [ktons/yr]
# IMAGE: Total cropland N, P surplus [Mt P2O5] --> [ktons/yr]
# IMAGE: Total agricultural N, P load from agricultural [kg N or P /yr] --> [ktons/yr]

import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

data_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"

IMAGE_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE"
IMAGE_N_dir = f"{IMAGE_dir}/Output-IMAGE_GNM-SSP1_oct2020-Nitrogen_CroplandBudget-v2.nc"
IMAGE_P_dir = f"{IMAGE_dir}/Output-IMAGE_GNM-SSP1_oct2020-Phosphate_CroplandBudget-v2.nc"
IMAGE_agri_N_dir = f"{IMAGE_dir}/Output-IMAGE_GNM-SSP1_oct2020-Nitrogen_Rivers-v2.nc" 
IMAGE_agri_P_dir = f"{IMAGE_dir}/Output-IMAGE_GNM-SSP5_oct2020-Phosphorus_Rivers-v2.nc" 


IMAGE_N_nc = xr.open_dataset(IMAGE_N_dir)
IMAGE_P_nc = xr.open_dataset(IMAGE_P_dir)
IMAGE_agri_N_nc = xr.open_dataset(IMAGE_agri_N_dir)
IMAGE_agri_P_nc = xr.open_dataset(IMAGE_agri_P_dir)

IMAGE_N_surplus = IMAGE_N_nc["NutrientSurplus"].sel(time="2015-05-01 00:00:00") # Mt N
IMAGE_P2O5_surplus = IMAGE_P_nc["NutrientSurplus"].sel(time="2015-05-01 00:00:00") # Mt P2O5

IMAGE_N_agri_load = IMAGE_agri_N_nc["Nsurface_runoff_agri"].sel(time="2015-05-01 00:00:00") # kg N/yr
IMAGE_P_agri_load = IMAGE_agri_P_nc["Psurface_runoff_agri"].sel(time="2015-05-01 00:00:00") # kg P/yr

WOFOST_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_1_Baseline"

basins = ["Indus", "Rhine", "LaPlata", "Yangtze"]  # ["Indus", "Rhine", "LaPlata", "Yangtze"]
croptypes = ["maize"]  # ["mainrice", "secondrice", "maize", "soybean", "winterwheat"]

for basin in basins:
    for crop in croptypes:

        if crop == "mainrice":
            cropname = "RICE"
        elif crop == "secondrice":
            cropname = "RICE"
        elif crop == "maize":
            cropname = "MAIZ"
        elif crop == "soybean":
            cropname = "SOYB"
        elif crop == "winterwheat":
            cropname = "WHEA"

        crop_mask_file_1 = f"{data_dir}/{basin}/Harvest_Area/{cropname}_Harvest_Area_05d_{basin}.nc"
        crop_mask_nc_1 = xr.open_dataset(crop_mask_file_1)
        crop_HA_1 = crop_mask_nc_1["Harvest_Area"].values
        crop_mask_1 = np.where(crop_HA_1 > 2500, 1, np.nan)

        crop_mask_file_2 = f"{data_dir}/{basin}/Mask/{basin}_{crop}_mask.nc"
        crop_mask_nc_2 = xr.open_dataset(crop_mask_file_2)
        crop_HA_2 = crop_mask_nc_2["TSUM1"].values
        crop_mask_2 = np.where(crop_HA_2 > 0, 1, np.nan)

        crop_mask = crop_mask_1 * crop_mask_2
        crop_HA = crop_HA_1  # ha

        # Extract lat and lon from crop mask
        target_lat = crop_mask_nc_1["lat"].values
        target_lon = crop_mask_nc_1["lon"].values
        lat_min = crop_mask_nc_1["lat"].values.min()
        lat_max = crop_mask_nc_1["lat"].values.max()
        lon_min = crop_mask_nc_1["lon"].values.min()
        lon_max = crop_mask_nc_1["lon"].values.max()

        # Cut the global IMAGE surplus and runoff data to basin extent
        IMAGE_N_cut = IMAGE_N_surplus.sel(lat=slice(lat_max, lat_min),lon=slice(lon_min, lon_max))
        IMAGE_P2O5_cut = IMAGE_P2O5_surplus.sel(lat=slice(lat_max, lat_min),lon=slice(lon_min, lon_max))
        IMAGE_N_basin_surplus = IMAGE_N_cut * crop_mask_2 * 1000 # ktons N
        IMAGE_P_basin_surplus = IMAGE_P2O5_cut * crop_mask_2 * 0.436 * 1000  # ktons P

        IMAGE_N_agri_cut = IMAGE_N_agri_load.sel(lat=slice(lat_max, lat_min),lon=slice(lon_min, lon_max))
        IMAGE_P_agri_cut = IMAGE_P_agri_load.sel(lat=slice(lat_max, lat_min),lon=slice(lon_min, lon_max))
        IMAGE_N_basin_agri_load = IMAGE_N_agri_cut * crop_mask_2 * 0.000001 # ktons N
        IMAGE_P_basin_agri_load = IMAGE_P_agri_cut * crop_mask_2 * 0.000001  # ktons P

        # Calculate the WOFOST-Simulated N, P losses through water flux (surface runoff, subsurface runoff, leaching)
        WOFOST_output = f"{WOFOST_dir}/{basin}_{crop}_annual.csv"
        WOFOST_df = pd.read_csv(WOFOST_output)
        WOFOST_df = WOFOST_df[(WOFOST_df["Year"] >= 2010) &(WOFOST_df["Year"] <= 2019)]

        WOFOST_df["N_water"] = WOFOST_df["N_surf"] + WOFOST_df["N_sub"] + WOFOST_df["N_leach"] # kg N/ha 
        WOFOST_df["N_runoff"] = WOFOST_df["N_surf"] + WOFOST_df["N_sub"] 
        WOFOST_df["P_water"] = WOFOST_df["P_surf"] + WOFOST_df["P_sub"] + WOFOST_df["P_leach"] # kg P/ha  
        WOFOST_df["P_runoff"] = WOFOST_df["P_surf"] + WOFOST_df["P_sub"] 
        WOFOST_mean = (WOFOST_df.groupby(["Lat", "Lon"], as_index=False).mean(numeric_only=True))
        WOFOST_xr = WOFOST_mean.set_index(["Lat", "Lon"]).to_xarray()

        # Find the corresponding lat and lon for each grid cell in WOFOST output
        WOFOST_on_cropgrid = WOFOST_xr.reindex(Lat=target_lat,Lon=target_lon,fill_value=np.nan)
        WOFOST_N_water = WOFOST_on_cropgrid["N_water"] * crop_mask * crop_HA * 0.000001   # ktons N
        WOFOST_P_water = WOFOST_on_cropgrid["P_water"] * crop_mask * crop_HA * 0.000001   # ktons P
        WOFOST_N_runoff = WOFOST_on_cropgrid["N_runoff"] * crop_mask * crop_HA * 0.000001   # ktons N
        WOFOST_P_runoff = WOFOST_on_cropgrid["P_runoff"] * crop_mask * crop_HA * 0.000001   # ktons P

        # Summarize the total N, P losses for the basin
        IMAGE_N_total = np.nansum(IMAGE_N_basin_surplus.values)
        IMAGE_P_total = np.nansum(IMAGE_P_basin_surplus.values)

        IMAGE_N_agri_total = np.nansum(IMAGE_N_basin_agri_load.values)
        IMAGE_P_agri_total = np.nansum(IMAGE_P_basin_agri_load.values)

        WOFOST_N_total = np.nansum(WOFOST_N_water.values)
        WOFOST_P_total = np.nansum(WOFOST_P_water.values)

        WOFOST_N_runoff_total = np.nansum(WOFOST_N_runoff.values)
        WOFOST_P_runoff_total = np.nansum(WOFOST_P_runoff.values)
        print(f"{basin} - {crop} :")

        print(f"  IMAGE cropland N surplus: {IMAGE_N_total:.4f} ktons/yr")  # Fertilizer - crop uptake - NH3
        print(f"  IMAGE agricultural N runoff: {IMAGE_N_agri_total:.4f} ktons/yr") 
        print(f"  WOFOST N runoff: {WOFOST_N_runoff_total:.4f} ktons/yr")
        print(f"  WOFOST N runoff + leaching: {WOFOST_N_total:.4f} ktons/yr")

        print(f"  IMAGE cropland P surplus: {IMAGE_P_total:.4f} ktons/yr") # Fertilizer - crop uptake 
        print(f"  IMAGE agricultural P runoff: {IMAGE_P_agri_total:.4f} ktons/yr")
        print(f"  WOFOST P runoff: {WOFOST_P_runoff_total:.4f} ktons/yr")
        print(f"  WOFOST P runoff + leaching: {WOFOST_P_total:.4f} ktons/yr")


        # Plot the spatial distribution of N, P runoff from both models
        fig, axs = plt.subplots(2, 2, figsize=(12, 10))
        im1 = axs[0, 0].imshow(IMAGE_N_basin_agri_load, cmap='viridis')
        axs[0, 0].set_title(f'IMAGE N agricultural runoff')
        fig.colorbar(im1, ax=axs[0, 0])
        im2 = axs[0, 1].imshow(WOFOST_N_runoff, cmap='viridis')
        axs[0, 1].set_title(f'WOFOST N runoff ')
        fig.colorbar(im2, ax=axs[0, 1])
        im3 = axs[1, 0].imshow(IMAGE_P_basin_agri_load, cmap='viridis')
        axs[1, 0].set_title(f'IMAGE P agricultural runoff')
        fig.colorbar(im3, ax=axs[1, 0])
        im4 = axs[1, 1].imshow(WOFOST_P_runoff, cmap='viridis')
        axs[1, 1].set_title(f'WOFOST P runoff')
        fig.colorbar(im4, ax=axs[1, 1]) 

        fig_output_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/2_Model_Adj"
        fig_name = f"{fig_output_dir}/{basin}_{crop}_IMAGE_WOFOST_N_P_comparison.png"
        fig.savefig(fig_name, dpi=300)
        plt.close(fig)

        print(" Figure saved as:", fig_name)    