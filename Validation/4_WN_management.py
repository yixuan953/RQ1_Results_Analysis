import pandas as pd 
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import geopandas as gpd
from matplotlib.colors import ListedColormap

# Parameters
basins = ["Indus", "Yangtze", "LaPlata", "Rhine"]
crops = ["winterwheat", "maize", "mainrice", "secondrice", "soybean"]
base_mask = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/2_Focus_Masks"
out_dir = base_mask  # save PNG in the same folder
shp_base = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_shp_StudyArea"

# Colors for categories
irrigated_colors = {
    "80% Yp achieved": "#71AA71D3",        # light green
    "Better nutrient management": "#FFA07A",  # light salmon
    "Better water management": "#87CEFA",     # light blue
    "Both water & nutrient": "#AB59A8"        # orchid
}

rainfed_colors = {
    "80% Yp achieved": "#71AA71D3",           # light green
    "Better nutrient management": "#FFA07A",  # light salmon
    "Irrigation required": "#87CEFA",         # light blue
    "Both irrigation & nutrient": "#AB59A8"   # orchid
}

for basin in basins:
    shp_path = f"{shp_base}/{basin}/{basin}.shp"
    if not Path(shp_path).is_file():
        print(f"  ⚠️ Skipping {basin}: shapefile not found")
        continue
    basin_gdf = gpd.read_file(shp_path)

    for crop in crops:
        mask_path = f"{base_mask}/{basin}_{crop}_mask_80Yp.nc"
        if not Path(mask_path).is_file():
            print(f"  ⚠️ Skipping {basin}-{crop}: mask file not found")
            continue

        ds = xr.open_dataset(mask_path)
        lat = ds['lat'].values
        lon = ds['lon'].values

        # ===== Irrigated categories =====
        full_irr = ds['Full_irrigation_actual_fert'].values
        limited_irr_suff = ds['Limited_irrigation_suff_fert'].values
        limited_irr_actual = ds['Limited_irrigation_actual_fert'].values

        irrigated_map = np.full(full_irr.shape, fill_value=np.nan, dtype=object)

        # Priority order: exact conditions first
        irrigated_map[limited_irr_actual==1] = "80% Yp achieved"
        irrigated_map[(limited_irr_actual==0) & (limited_irr_suff==1)] = "Better nutrient management"
        irrigated_map[(limited_irr_actual==0) & (full_irr==1)] = "Better water management"
        # Remaining irrigated pixels → "Both"
        irrigated_map[(limited_irr_actual==0) & pd.isna(irrigated_map)] = "Both water & nutrient"

        # ===== Rainfed categories =====
        rainfed_actual_Yp = ds['Rainfed_actual_fert_CompYp'].values
        rainfed_actual_Yp_rainfed = ds['Rainfed_actual_fert_CompYpRainfed'].values
        rainfed_suff = ds['Rainfed_suff_fert'].values

        rainfed_map = np.full(rainfed_actual_Yp.shape, fill_value=np.nan, dtype=object)

        rainfed_map[rainfed_actual_Yp==1] = "80% Yp achieved"
        rainfed_map[(rainfed_actual_Yp==0) & (rainfed_actual_Yp_rainfed==0)] = "Better nutrient management"
        rainfed_map[(rainfed_actual_Yp==0) & (full_irr==1)] = "Irrigation required"
        # Remaining rainfed pixels → "Both"
        rainfed_map[(rainfed_actual_Yp==0) & pd.isna(rainfed_map)] = "Both irrigation & nutrient"

        # ===== Plotting =====
        fig, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)

        # ---- Irrigated ----
        ax = axes[0]
        ordered_cats_irrigated = list(irrigated_colors.keys())
        cmap_irrigated = ListedColormap([irrigated_colors[c] for c in ordered_cats_irrigated])
        cmap_irrigated.set_bad(color='white')

        numeric_map = np.full(irrigated_map.shape, np.nan)
        for idx, cat in enumerate(ordered_cats_irrigated):
            numeric_map[irrigated_map==cat] = idx
        numeric_map_masked = np.ma.masked_invalid(numeric_map)

        ax.imshow(numeric_map_masked, origin='upper', cmap=cmap_irrigated,
                  extent=[lon.min(), lon.max(), lat.min(), lat.max()])
        ax.set_title("Irrigated cropland")
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        basin_gdf.boundary.plot(ax=ax, color='black', linewidth=1)

        handles = [plt.Line2D([0],[0], marker='s', color='w',
                              markerfacecolor=irrigated_colors[c], markersize=10)
                   for c in ordered_cats_irrigated]
        ax.legend(handles, ordered_cats_irrigated, loc='lower left', fontsize=9)

        # ---- Rainfed ----
        ax = axes[1]
        ordered_cats_rainfed = list(rainfed_colors.keys())
        cmap_rainfed = ListedColormap([rainfed_colors[c] for c in ordered_cats_rainfed])
        cmap_rainfed.set_bad(color='white')

        numeric_map = np.full(rainfed_map.shape, np.nan)
        for idx, cat in enumerate(ordered_cats_rainfed):
            numeric_map[rainfed_map==cat] = idx
        numeric_map_masked = np.ma.masked_invalid(numeric_map)

        ax.imshow(numeric_map_masked, origin='upper', cmap=cmap_rainfed,
                  extent=[lon.min(), lon.max(), lat.min(), lat.max()])
        ax.set_title("Rainfed cropland")
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        basin_gdf.boundary.plot(ax=ax, color='black', linewidth=1)

        handles = [plt.Line2D([0],[0], marker='s', color='w',
                              markerfacecolor=rainfed_colors[c], markersize=10)
                   for c in ordered_cats_rainfed]
        ax.legend(handles, ordered_cats_rainfed, loc='lower left', fontsize=9)

        # Save
        out_path = f"{out_dir}/{basin}_{crop}_WNmanage.png"
        plt.suptitle(f"{basin} - {crop} Management Focus", fontsize=16)
        plt.savefig(out_path, dpi=300)
        plt.close()
        print(f"  ✅ Saved {out_path}")
