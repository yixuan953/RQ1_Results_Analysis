# This code is used to plot the losses --> reduction of land use --> Impact on total production

import numpy as np
import xarray as xr
import os
from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib import ticker

# Define basins and crops
basins = ['LaPlata', 'Indus', 'Yangtze', 'Rhine']
all_crops = ['winterwheat', 'maize', 'mainrice', 'secondrice', 'soybean']
model_output_base = '/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios'
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/Red_Fert_Test/Red_HA"

# Base paths
data_base = '/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea'
shp_base = '/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_shp_StudyArea'
critical_NP_losses_base = '/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/2_Critical_NP_losses/1_Sens_analysis'

for basin in basins:
    # Basin shp file
    basin_shp_file = f"{shp_base}/{basin}/{basin}.shp"
    river_shp_file = f"{shp_base}/{basin}/{basin}_River.shp"
    basin_gdf = gpd.read_file(basin_shp_file)
    river_gdf = gpd.read_file(river_shp_file)

    # Load critical losses data
    n_crit_runoff_file = f"{critical_NP_losses_base}/{basin}_crit_N_runoff_kgperha_org.nc"
    n_crit_loss_org = xr.open_dataset(n_crit_runoff_file)['critical_maincrop_N_runoff']


    for crop in all_crops:

        # ======= Load output of losses: Original & Reduced =================
        # Irrigated
        irrigated_baseline_file = f"{model_output_base}/2_1_Baseline/{basin}_{crop}_annual.nc"
        irrigated_fert_red_file = f"{model_output_base}/2_3_Sus_Irri_Red_Fert/Red_org/{basin}_{crop}_annual.nc"
        if not os.path.exists(irrigated_baseline_file) or not os.path.exists(irrigated_fert_red_file):
            print(f"!!! Irrigated model output missing for {basin} - {crop}, skipping...")
            continue
        # Rainfed
        rainfed_baseline_file = f"{model_output_base}/2_1_Baseline_rainfed/{basin}_{crop}_annual.nc"
        rainfed_fert_red_file = f"{model_output_base}/2_3_Rainfed/Red_org/{basin}_{crop}_annual.nc"
        if not os.path.exists(rainfed_baseline_file) or not os.path.exists(rainfed_fert_red_file):
            print(f"!!! Rainfed model output missing for {basin} - {crop}, skipping...")
            continue

        irrigated_baseline_ds = xr.open_dataset(irrigated_baseline_file)
        irrigated_baseline_ds = irrigated_baseline_ds.sel(year=slice('2010', '2019'))
        irrigated_baseline_N_runoff = irrigated_baseline_ds['N_Runoff'].mean(dim='year')
        irrigated_basline_yield = irrigated_baseline_ds['Yield'].mean(dim='year')

        irrigated_fert_red_ds = xr.open_dataset(irrigated_fert_red_file)
        irrigated_fert_red_ds = irrigated_fert_red_ds.sel(year=slice('2010', '2019'))
        irrigated_fert_red_N_runoff = irrigated_fert_red_ds['N_Runoff'].mean(dim='year')
        irrigated_fert_red_yield = irrigated_fert_red_ds['Yield'].mean(dim='year')

        rainfed_baseline_ds = xr.open_dataset(rainfed_baseline_file)
        rainfed_baseline_ds = rainfed_baseline_ds.sel(year=slice('2010', '2019'))
        rainfed_baseline_N_runoff = rainfed_baseline_ds['N_Runoff'].mean(dim='year')
        rainfed_baseline_yield = rainfed_baseline_ds['Yield'].mean(dim='year')

        rainfed_fert_red_ds = xr.open_dataset(rainfed_fert_red_file)
        rainfed_fert_red_ds = rainfed_fert_red_ds.sel(year=slice('2010', '2019'))
        rainfed_fert_red_N_runoff = rainfed_fert_red_ds['N_Runoff'].mean(dim='year')
        rainfed_fert_red_yield = rainfed_fert_red_ds['Yield'].mean(dim='year')  

        # ======= Load harvested area for different land use types ==========
        if crop == "winterwheat":
            mask_crop = "WHEA"
        elif crop == "maize":
            mask_crop = "MAIZ"
        elif crop == "soybean":
            mask_crop = "SOYB"
        elif crop == "mainrice" and basin != "Yangtze":
            mask_crop = "RICE "
        elif crop == "mainrice" and basin == "Yangtze":
            mask_crop = "MAINRICE"
        elif crop == "secondrice":
            mask_crop = "SECONDRICE"

        irrigated_HA_file=f"{data_base}/{basin}/Harvest_Area/{mask_crop}_Irrigated_Harvest_Area_05d_{basin}.nc"
        rainfed_HA_file=f"{data_base}/{basin}/Harvest_Area/{mask_crop}_Rainfed_Harvest_Area_05d_{basin}.nc"

        if not os.path.exists(irrigated_HA_file) or not os.path.exists(rainfed_HA_file):
            print(f"!!! Harvest area file missing for {basin} - {crop}, skipping...")
            continue

        irrigated_HA_ds = xr.open_dataset(irrigated_HA_file)
        irrigated_HA = irrigated_HA_ds['Harvest_Area'].sel(lat=irrigated_baseline_ds['lat'], lon=irrigated_baseline_ds['lon'], method='nearest').values  # in ha
        rainfed_HA_ds = xr.open_dataset(rainfed_HA_file)
        rainfed_HA = rainfed_HA_ds['Harvest_Area'].sel(lat=rainfed_baseline_ds['lat'], lon=rainfed_baseline_ds['lon'], method='nearest').values  # in ha    
        
        # ======= Calculate the requirment of harvested area reduction ==========
        # How much N runoff is allowed [kg]
        total_N_runoff_baseline_irrigated = n_crit_loss_org * irrigated_HA # in kg
        total_N_runoff_baseline_rainfed = n_crit_loss_org * rainfed_HA # in kg

        # Calculate the maximum harvested area that can be allowed with org fertilizer use
        max_ha_with_org_fert_irrigated = total_N_runoff_baseline_irrigated / irrigated_baseline_N_runoff  # in ha
        red_irrigated_org = (max_ha_with_org_fert_irrigated/irrigated_HA)
        max_ha_with_org_fert_rainfed = total_N_runoff_baseline_rainfed / rainfed_baseline_N_runoff  # in ha
        red_rainfed_org = (max_ha_with_org_fert_rainfed / rainfed_HA)

        # Calculate the maximum harvested area that can be allowed with reduced fertilizer use
        max_ha_with_red_fert_irrigated = total_N_runoff_baseline_irrigated / irrigated_fert_red_N_runoff  # in ha
        red_irrigated_red_fert = (max_ha_with_red_fert_irrigated / irrigated_HA)
        max_ha_with_red_fert_rainfed = total_N_runoff_baseline_rainfed / rainfed_fert_red_N_runoff  # in ha
        red_rainfed_red_fert = (max_ha_with_red_fert_rainfed / rainfed_HA)
        
        # What could be the impact on crop yield
        production_baseline_irrigated = (irrigated_basline_yield * irrigated_HA) / 1000000  # in kton
        production_baseline_rainfed = (rainfed_baseline_yield * rainfed_HA) / 1000000  # in kton
        total_production_baseline = production_baseline_irrigated + production_baseline_rainfed
        
        # Reduce land use only
        production_red_irrigated = (irrigated_basline_yield * max_ha_with_org_fert_irrigated) / 1000000  # in kton
        production_red_rainfed = (rainfed_baseline_yield * max_ha_with_org_fert_rainfed) / 1000000  # in kton
        total_production_irrigated_red = production_red_irrigated + production_red_rainfed

        # Reduce fertilizer + land use
        production_red_irrigated_org = (irrigated_fert_red_yield * max_ha_with_org_fert_irrigated) / 1000000  # in kton
        production_red_rainfed_org = (rainfed_fert_red_yield * max_ha_with_org_fert_rainfed) / 1000000  # in kton
        total_production_irrigated_red_org = production_red_irrigated_org + production_red_rainfed_org

        # ============ Start plotting maps ===========

        lats = irrigated_baseline_ds['lat'].values
        lons = irrigated_baseline_ds['lon'].values
        lon2d, lat2d = np.meshgrid(lons, lats)

        # mask arrays where harvested area == 0
        irr_mask = irrigated_HA > 250
        rf_mask = rainfed_HA > 250

        # prepare plotting arrays (mask out where HA==0)
        irr_N_loss = np.where(irr_mask, irrigated_baseline_N_runoff.values, np.nan)
        irr_N_red_fert_loss = np.where(irr_mask, irrigated_fert_red_N_runoff.values,np.nan)
        irr_landuse_red_org = np.where(irr_mask, red_irrigated_org.values, np.nan)
        irr_landuse_red_fert_red = np.where(irr_mask, red_irrigated_red_fert, np.nan)
        irr_prod_baseline = np.where(irr_mask, production_baseline_irrigated, np.nan)
        irr_prod_redfert = np.where(irr_mask, production_red_irrigated_org, np.nan)

        rf_N_loss = np.where(rf_mask, rainfed_baseline_N_runoff.values, np.nan)
        rf_N_red_fert_loss = np.where(rf_mask, rainfed_fert_red_N_runoff.values,np.nan)
        rf_landuse_red_org = np.where(rf_mask, red_rainfed_org, np.nan)
        rf_landuse_red_fert_red = np.where(rf_mask, red_rainfed_red_fert, np.nan)
        rf_prod_baseline = np.where(rf_mask, production_baseline_rainfed, np.nan)
        rf_prod_redfert = np.where(rf_mask, production_red_rainfed_org, np.nan)

        total_prod_baseline = total_production_baseline
        total_prod_landuse_red = total_production_irrigated_red
        total_prod_landuse_plus_fert = total_production_irrigated_red_org


        cmap_div = "RdYlBu_r"
        cmap_seq = "YlGn"

        # 1) Irrigated: 2x3 (row1 baseline N_loss, landuse reduction, production baseline;
        #                    row2 baseline N_loss, landuse reduction, production with reduced fert)
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        axs = axes.ravel()

        im0 = axs[0].pcolormesh(lon2d, lat2d, irr_N_loss, cmap=cmap_seq, shading="auto")
        axs[0].set_title("N runoff (kg/ha)")
        basin_gdf.boundary.plot(ax=axs[0], color="black", linewidth=1)
        plt.colorbar(im0, ax=axs[0], orientation="vertical", fraction=0.046, pad=0.04)

        im1 = axs[1].pcolormesh(lon2d, lat2d, 100 * irr_landuse_red_org, cmap="viridis", shading="auto", vmin=0, vmax=100)
        axs[1].set_title("Allowable HA/Current [%]")
        basin_gdf.boundary.plot(ax=axs[1], color="black", linewidth=1)
        cbar1 = plt.colorbar(im1, ax=axs[1], orientation="vertical", fraction=0.046, pad=0.04)
        cbar1.set_ticks(np.linspace(0, 100, 6))

        im2 = axs[2].pcolormesh(lon2d, lat2d, irr_prod_baseline, cmap="YlOrBr", shading="auto")
        axs[2].set_title("Crop production (kton)")
        basin_gdf.boundary.plot(ax=axs[2], color="black", linewidth=1)
        plt.colorbar(im2, ax=axs[2], orientation="vertical", fraction=0.046, pad=0.04)

        # second row: same N loss & landuse red (for context), production with reduced fertilizer
        im3 = axs[3].pcolormesh(lon2d, lat2d, irr_N_red_fert_loss, cmap=cmap_seq, shading="auto")
        axs[3].set_title("N runoff (kg/ha)")
        basin_gdf.boundary.plot(ax=axs[3], color="black", linewidth=1)
        plt.colorbar(im3, ax=axs[3], orientation="vertical", fraction=0.046, pad=0.04)

        im4 = axs[4].pcolormesh(lon2d, lat2d, 100 * irr_landuse_red_fert_red, cmap="viridis", shading="auto", vmin=0, vmax=100)
        axs[4].set_title("Allowable HA/Current [%]")
        basin_gdf.boundary.plot(ax=axs[4], color="black", linewidth=1)
        cbar4 = plt.colorbar(im4, ax=axs[4], orientation="vertical", fraction=0.046, pad=0.04)
        cbar4.set_ticks(np.linspace(0, 100, 6))

        im5 = axs[5].pcolormesh(lon2d, lat2d, irr_prod_redfert, cmap="YlOrBr", shading="auto")
        axs[5].set_title("Crop production (kton) ")
        basin_gdf.boundary.plot(ax=axs[5], color="black", linewidth=1)
        plt.colorbar(im5, ax=axs[5], orientation="vertical", fraction=0.046, pad=0.04)

        for ax in axs:
            ax.set_aspect("equal", adjustable="box")
        fig.suptitle(f"{basin} - {crop} (Irrigated) average 2010-2019", fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        out_irrig = os.path.join(output_dir, f"{basin}_{crop}_Irrigated_maps.png")
        fig.savefig(out_irrig, dpi=200, bbox_inches="tight")
        plt.close(fig)

        # 2) Rainfed: same layout
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        axs = axes.ravel()

        im0 = axs[0].pcolormesh(lon2d, lat2d, rf_N_loss, cmap=cmap_seq, shading="auto")
        axs[0].set_title("N runoff (kg/ha)")
        basin_gdf.boundary.plot(ax=axs[0], color="black", linewidth=1)
        plt.colorbar(im0, ax=axs[0], orientation="vertical", fraction=0.046, pad=0.04)

        im1 = axs[1].pcolormesh(lon2d, lat2d, 100 * rf_landuse_red_org, cmap="viridis", shading="auto", vmin=0, vmax=100)
        axs[1].set_title("Allowable HA/Current [%]")
        basin_gdf.boundary.plot(ax=axs[1], color="black", linewidth=1)
        cbar1 = plt.colorbar(im1, ax=axs[1], orientation="vertical", fraction=0.046, pad=0.04)
        cbar1.set_ticks(np.linspace(0, 100, 6))        

        im2 = axs[2].pcolormesh(lon2d, lat2d, rf_prod_baseline, cmap="YlOrBr", shading="auto")
        axs[2].set_title("Crop Production (kton)")
        basin_gdf.boundary.plot(ax=axs[2], color="black", linewidth=1)
        plt.colorbar(im2, ax=axs[2], orientation="vertical", fraction=0.046, pad=0.04)

        im3 = axs[3].pcolormesh(lon2d, lat2d, rf_N_red_fert_loss, cmap=cmap_seq, shading="auto")
        axs[3].set_title("N runoff (kg/ha)")
        basin_gdf.boundary.plot(ax=axs[3], color="black", linewidth=1)
        plt.colorbar(im3, ax=axs[3], orientation="vertical", fraction=0.046, pad=0.04)

        im4 = axs[4].pcolormesh(lon2d, lat2d, 100 * rf_landuse_red_fert_red, cmap="viridis", shading="auto", vmin=0, vmax=100)
        axs[4].set_title("Allowable HA/Current [%]")
        basin_gdf.boundary.plot(ax=axs[4], color="black", linewidth=1)
        cbar4 = plt.colorbar(im4, ax=axs[4], orientation="vertical", fraction=0.046, pad=0.04)
        cbar4.set_ticks(np.linspace(0, 100, 6))

        im5 = axs[5].pcolormesh(lon2d, lat2d, rf_prod_redfert, cmap="YlOrBr", shading="auto")
        axs[5].set_title("Crop Production (kton)")
        basin_gdf.boundary.plot(ax=axs[5], color="black", linewidth=1)
        plt.colorbar(im5, ax=axs[5], orientation="vertical", fraction=0.046, pad=0.04)

        for ax in axs:
            ax.set_aspect("equal", adjustable="box")
        fig.suptitle(f"{basin} - {crop} (Rainfed) average 2010-2019", fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        out_rain = os.path.join(output_dir, f"{basin}_{crop}_Rainfed_maps.png")
        fig.savefig(out_rain, dpi=200, bbox_inches="tight")
        plt.close(fig)

        # 3) Total production: 1x3 (Baseline total production, land-use reduction total, land-use + fert reduction total)
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        axs = axes.ravel()

        im0 = axs[0].pcolormesh(lon2d, lat2d, np.where((irr_mask | rf_mask), total_prod_baseline, np.nan), cmap="YlOrBr", shading="auto")
        axs[0].set_title("Crop production baseline (kton)")
        basin_gdf.boundary.plot(ax=axs[0], color="black", linewidth=1)
        plt.colorbar(im0, ax=axs[0], orientation="vertical", fraction=0.046, pad=0.04)

        im1 = axs[1].pcolormesh(lon2d, lat2d, np.where((irr_mask | rf_mask), total_prod_landuse_red, np.nan), cmap="YlOrBr", shading="auto")
        axs[1].set_title("Crop production (org_fert + red_HA) (kton)")
        basin_gdf.boundary.plot(ax=axs[1], color="black", linewidth=1)
        plt.colorbar(im1, ax=axs[1], orientation="vertical", fraction=0.046, pad=0.04)

        im2 = axs[2].pcolormesh(lon2d, lat2d, np.where((irr_mask | rf_mask), total_prod_landuse_plus_fert, np.nan), cmap="YlOrBr", shading="auto")
        axs[2].set_title("Crop production (red_fert + red_HA) (kton)")
        basin_gdf.boundary.plot(ax=axs[2], color="black", linewidth=1)
        plt.colorbar(im2, ax=axs[2], orientation="vertical", fraction=0.046, pad=0.04)

        for ax in axs:
           ax.set_aspect("equal", adjustable="box")
        fig.suptitle(f"{basin} - {crop} (Total production) average 2010-2019", fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        out_total = os.path.join(output_dir, f"{basin}_{crop}_TotalProduction_maps.png")
        fig.savefig(out_total, dpi=200, bbox_inches="tight")
        plt.close(fig)

        print(f"Saved maps for {basin} - {crop} to {output_dir}")        
        


    
    
