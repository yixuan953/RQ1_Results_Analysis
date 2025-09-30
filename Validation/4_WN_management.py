import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import geopandas as gpd

# Parameters
basins = ["Indus", "Yangtze", "LaPlata", "Rhine"]
crops = ["winterwheat", "maize", "mainrice", "secondrice", "soybean"]
base_mask = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/2_Focus_Masks"
out_dir = base_mask  # save PNG in the same folder
shp_base = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_shp_StudyArea"

# Colors for categories
irrigated_colors = {
    "Better nutrient management": "#FFA07A",      # light salmon
    "Better water management": "#87CEFA",         # light blue
    "Both water & nutrient": "#AB59A8",           # orchid
    "80% Yp achieved": "#71AA71D3"                # light green
}

rainfed_colors = {
    "Better nutrient management": "#FFA07A",      # light salmon
    "Irrigation required": "#87CEFA",             # light blue
    "Both irrigation & nutrient":"#AB59A8",       # orchid
    "80% Yp achieved": "#71AA71D3"                # light green
}

for basin in basins:
    # Load basin shapefile
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

        # Irrigated categories
        full_irr = ds['Full_irrigation_actual_fert'].values
        limited_irr_suff = ds['Limited_irrigation_suff_fert'].values
        limited_irr_actual = ds['Limited_irrigation_actual_fert'].values

        irrigated_map = np.full_like(full_irr, fill_value=np.nan, dtype=object)
        irrigated_map[(full_irr==0) & (limited_irr_suff==1)] = "Better nutrient management"
        irrigated_map[(full_irr==1) & (limited_irr_suff==0)] = "Better water management"
        irrigated_map[(full_irr==0) & (limited_irr_suff==0)] = "Both water & nutrient"
        irrigated_map[(limited_irr_actual==1)] = "80% Yp achieved"

        # Rainfed categories
        rainfed_actual = ds['Rainfed_actual_fert'].values
        rainfed_suff = ds['Rainfed_suff_fert'].values

        rainfed_map = np.full_like(rainfed_actual, fill_value=np.nan, dtype=object)
        rainfed_map[(rainfed_suff==1) & (rainfed_actual==0)] = "Better nutrient management"
        rainfed_map[(rainfed_suff==0) & (rainfed_actual==1)] = "Irrigation required"
        rainfed_map[(rainfed_suff==0) & (rainfed_actual==0)] = "Both irrigation & nutrient"
        rainfed_map[(rainfed_actual==1) & (rainfed_suff==1)] = "80% Yp achieved"

        # Plot
        fig, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)
        for ax, data, colors, title in zip(
            axes,
            [irrigated_map, rainfed_map],
            [irrigated_colors, rainfed_colors],
            ["Irrigated cropland", "Rainfed cropland"]
        ):
            # Create numeric array for plotting
            numeric_map = np.full(data.shape, np.nan)
            unique_cats = list(colors.keys())
            for idx, cat in enumerate(unique_cats):
                numeric_map[data==cat] = idx

            cmap = plt.cm.get_cmap('tab10', len(unique_cats))
            im = ax.imshow(
                numeric_map, 
                origin='upper', 
                cmap=cmap,
                extent=[lon.min(), lon.max(), lat.min(), lat.max()]
            )
            # Set NaNs to appear as white
            im.set_bad(color='white')  # <--- this fixes extra colors

            ax.set_title(title)
            ax.set_xlabel('Longitude')
            ax.set_ylabel('Latitude')

            # Overlay basin boundary
            basin_gdf.boundary.plot(ax=ax, color='black', linewidth=1)

            # Legend
            handles = [plt.Line2D([0],[0], marker='s', color='w',
                                  markerfacecolor=colors[cat], markersize=10) for cat in unique_cats]
            ax.legend(handles, unique_cats, loc='lower right', fontsize=9)

        # Save
        out_path = f"{out_dir}/{basin}_{crop}_WNmanage.png"
        plt.suptitle(f"{basin} - {crop} Management Focus", fontsize=16)
        plt.savefig(out_path, dpi=300)
        plt.close()
        print(f"  ✅ Saved {out_path}")
