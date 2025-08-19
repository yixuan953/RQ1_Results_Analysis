import os
import xarray as xr
import matplotlib.pyplot as plt
import geopandas as gpd

# Paths
base_nc = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/S0"
base_mask = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
base_shp = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_shp_StudyArea"
out_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/S0"
os.makedirs(out_dir, exist_ok=True)

basins = ["LaPlata", "Yangtze", "Rhine", "Indus"]

# Define logical crops and all possible .nc filename variations
crops = {
    "Mainrice": ["Mainrice", "mainrice"],
    "Secondrice": ["Secondrice", "rice", "secondrice"],
    "Maize": ["Maize", "maize"],
    "Soybean": ["Soybean", "soybean", "Soy"],
    "Wheat": ["Wheat", "winterwheat", "Winterwheat"]
}

# Map crop names to mask file names
mask_name_map = {
    "Mainrice": "mainrice",
    "Secondrice": "secondrice",
    "Maize": "maize",
    "Soybean": "soybean",
    "Wheat": "winterwheat"  # even if .nc is 'Wheat', mask is 'winterwheat'
}

for basin in basins:
    for crop, aliases in crops.items():
        # Find first existing .nc file matching any alias
        found_file = None
        for alias in aliases:
            fname = f"{basin}_{alias}_MaxAvg.nc"
            fpath = os.path.join(base_nc, fname)
            if os.path.exists(fpath):
                found_file = fpath
                crop_used = alias
                break
        if found_file is None:
            continue  # skip if no matching file

        print(f"Processing: {os.path.basename(found_file)}")
        ds = xr.open_dataset(found_file)

        # Load variables directly
        TSUM1 = ds["TSUM1"] if "TSUM1" in ds else None
        TSUM2 = ds["TSUM2"] if "TSUM2" in ds else None
        Sow_date = ds["Sow_date"] if "Sow_date" in ds else None

        # Read HA mask
        mask_crop_name = mask_name_map.get(crop, crop.lower())
        mask_path = os.path.join(base_mask, basin, "Mask", f"{mask_crop_name}_mask.nc")
        HA = None
        if os.path.exists(mask_path):
            mask_ds = xr.open_dataset(mask_path)
            HA = mask_ds[list(mask_ds.data_vars)[0]]

        # Read basin shapefile
        shp_path = os.path.join(base_shp, basin, f"{basin}.shp")
        basin_shp = gpd.read_file(shp_path) if os.path.exists(shp_path) else None

        # Plot 2x2 subplots
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.ravel()
        plots = [(TSUM1, "TSUM1"), (TSUM2, "TSUM2"), (Sow_date, "Sow_date"), (HA, "HA")]

        for ax, (var, title) in zip(axes, plots):
            if var is not None:
                var.plot(ax=ax, cmap="viridis", add_colorbar=True)
            ax.set_title(f"{basin} - {crop_used} - {title}")
            if basin_shp is not None:
                basin_shp.boundary.plot(ax=ax, color="red", linewidth=1)

        plt.tight_layout()
        out_file = os.path.join(out_dir, f"{basin}_{crop_used}_summary.png")
        plt.savefig(out_file, dpi=300)
        plt.close()

        ds.close()
        if HA is not None:
            mask_ds.close()

