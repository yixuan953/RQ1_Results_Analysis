#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import geopandas as gpd
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D

# ----------------------------------------------------------------------
# PARAMETERS
# ----------------------------------------------------------------------
basins   = ["Indus", "Yangtze", "LaPlata", "Rhine"]
crops    = ["winterwheat", "maize", "mainrice", "secondrice", "soybean"]
base_mask = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/2_Focus_Masks"
out_dir   = base_mask                     # PNGs will be written here
shp_base  = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_shp_StudyArea"

# ----------------------------------------------------------------------
# COLOUR PALLETTES – **NO ALPHA CHANNEL** (← FIX)
# ----------------------------------------------------------------------
irrigated_colors = {
    "80% Yp achieved":          "#71AA71",   # solid green
    "Better nutrient management": "#FFA07A",   # orange / salmon
    "Better water management":   "#87CEFA",   # light blue
    "Both water & nutrient":     "#AB59A8"    # purple
}

rainfed_colors = {
    "80% Yp achieved":          "#71AA71",   # solid green (may be zero pixels)
    "Better nutrient management": "#FFA07A",   # orange
    "Irrigation required":       "#87CEFA",   # blue
    "Both irrigation & nutrient": "#AB59A8"    # purple
}

# ----------------------------------------------------------------------
# MAIN LOOP
# ----------------------------------------------------------------------
for basin in basins:
    # -------------------- LOAD BASIN SHAPEFILE -----------------------
    shp_path = f"{shp_base}/{basin}/{basin}.shp"
    if not Path(shp_path).is_file():
        print(f"⚠️  Skipping {basin}: shapefile not found")
        continue
    basin_gdf = gpd.read_file(shp_path)

    for crop in crops:
        mask_path = f"{base_mask}/{basin}_{crop}_mask_80Yp.nc"
        if not Path(mask_path).is_file():
            print(f"⚠️  Skipping {basin}-{crop}: mask file not found")
            continue

        ds = xr.open_dataset(mask_path)
        lat = ds['lat'].values
        lon = ds['lon'].values

        # ------------------------------------------------------------------
        # IRRIGATED SECTION (unchanged except for colour handling later)
        # ------------------------------------------------------------------
        full_irr          = ds['Full_irrigation_actual_fert'].values
        limited_irr_suff  = ds['Limited_irrigation_suff_fert'].values
        limited_irr_actual = ds['Limited_irrigation_actual_fert'].values

        irrigated_map = np.ma.masked_all(limited_irr_actual.shape, dtype=float)

        # Mapping: order of dict keys == integer index
        irrig_cat_to_idx = {cat: i for i, cat in enumerate(irrigated_colors.keys())}

        irrigated_map[limited_irr_actual == 1] = irrig_cat_to_idx["80% Yp achieved"]
        irrigated_map[(limited_irr_actual == 0) & (limited_irr_suff == 1)] = irrig_cat_to_idx["Better nutrient management"]
        irrigated_map[(limited_irr_actual == 0) & (full_irr == 1)] = irrig_cat_to_idx["Better water management"]
        mask_both = ((limited_irr_actual == 0) & (full_irr == 1) & (limited_irr_suff == 1)) | \
                    ((limited_irr_actual == 0) & (full_irr == 0) & (limited_irr_suff == 0))
        irrigated_map[mask_both] = irrig_cat_to_idx["Both water & nutrient"]

        # ------------------------------------------------------------------
        # RAINFED SECTION – **FULL FIX**
        # ------------------------------------------------------------------
        # 1️⃣ Preserve the original no‑data mask (True = missing)
        orig_mask = np.ma.getmaskarray(ds['Rainfed_actual_fert_CompYp'].values)

        # 2️⃣ Clean integer arrays while keeping the mask
        rainfed_actual_Yp = np.where(orig_mask, 0,
                                    np.nan_to_num(ds['Rainfed_actual_fert_CompYp'].values,
                                                  nan=0)).astype(int)

        rainfed_actual_Yp_rainfed = np.where(orig_mask, 0,
                                            np.nan_to_num(ds['Rainfed_actual_fert_CompYpRainfed'].values,
                                                          nan=0)).astype(int)

        # `full_irr` was already loaded for the irrigated part; keep it as int
        full_irr = np.where(orig_mask, 0,
                            np.nan_to_num(full_irr, nan=0)).astype(int)

        # 3️⃣ Build **exclusive** masks for the three *real* categories
        mask_nutrient = (rainfed_actual_Yp == 0) & (rainfed_actual_Yp_rainfed == 0)
        mask_irr_req  = (rainfed_actual_Yp == 0) & (full_irr == 1)

        # 4️⃣ “Both irrigation & nutrient” = everything that is valid data
        #    but not covered by the two masks above.
        mask_both = (~mask_nutrient) & (~mask_irr_req) & (~orig_mask)

        # 5️⃣ Optional debug counts (feel free to comment out later)
        print(f"\n{basin} – {crop}")
        print("  Better nutrient:", mask_nutrient.sum())
        print("  Irrigation required:", mask_irr_req.sum())
        print("  Both (fallback):", mask_both.sum())
        print("  80% Yp (should be zero):", (rainfed_actual_Yp == 1).sum())
        print("  Masked (no data):", orig_mask.sum())

        # 6️⃣ Initialise the rain‑fed raster with the original mask.
        #    Cells we never write into stay masked → white.
        rainfed_map = np.ma.masked_array(np.full(rainfed_actual_Yp.shape, np.nan),
                                        mask=orig_mask)

        # Mapping – order of dict keys == integer index (must match colormap)
        rainfed_cat_to_idx = {cat: i for i, cat in enumerate(rainfed_colors.keys())}

        # 7️⃣ Fill only the categories that actually have data.
        #    We deliberately **skip** the “80% Yp” assignment if it is empty.
        rainfed_map[mask_nutrient] = rainfed_cat_to_idx["Better nutrient management"]
        rainfed_map[mask_irr_req]  = rainfed_cat_to_idx["Irrigation required"]
        rainfed_map[mask_both]     = rainfed_cat_to_idx["Both irrigation & nutrient"]
        # (If you ever want to visualise the 80 % Yp class, just add:)
        # rainfed_map[rainfed_actual_Yp == 1] = rainfed_cat_to_idx["80% Yp achieved"]

        # ------------------------------------------------------------------
        # PLOTTING
        # ------------------------------------------------------------------
        fig, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)

        # ----- Irrigated -----
        ax = axes[0]
        cmap_irrig = ListedColormap(list(irrigated_colors.values()))   # ← same order as dict
        cmap_irrig.set_bad(color='white')
        ax.imshow(irrigated_map, origin='upper', cmap=cmap_irrig,
                  extent=[lon.min(), lon.max(), lat.min(), lat.max()])
        ax.set_title("Irrigated cropland")
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        basin_gdf.boundary.plot(ax=ax, color='black', linewidth=1)

        handles = [Line2D([0], [0], marker='s', color='w',
                         markerfacecolor=color, markersize=10)
                   for color in irrigated_colors.values()]
        ax.legend(handles, list(irrigated_colors.keys()),
                  loc='lower left', fontsize=9)

        # ----- Rainfed -----
        ax = axes[1]
        cmap_rain = ListedColormap(list(rainfed_colors.values()))   # ← same order as dict
        cmap_rain.set_bad(color='white')
        ax.imshow(rainfed_map, origin='upper', cmap=cmap_rain,
                  extent=[lon.min(), lon.max(), lat.min(), lat.max()])
        ax.set_title("Rainfed cropland")
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        basin_gdf.boundary.plot(ax=ax, color='black', linewidth=1)

        handles = [Line2D([0], [0], marker='s', color='w',
                         markerfacecolor=color, markersize=10)
                   for color in rainfed_colors.values()]
        ax.legend(handles, list(rainfed_colors.keys()),
                  loc='lower left', fontsize=9)

        # ----- Save figure -----
        out_path = f"{out_dir}/{basin}_{crop}_WNmanage.png"
        plt.suptitle(f"{basin} - {crop} Management Focus", fontsize=16)
        plt.savefig(out_path, dpi=300)
        plt.close()
        print(f"✅ Saved {out_path}")