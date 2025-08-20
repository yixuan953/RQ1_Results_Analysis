import os 
import xarray as xr
import matplotlib.pyplot as plt
import geopandas as gpd

# Paths
base_nc = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/S1"
base_mask = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
base_shp = "/lustre/nobackup/WUR/ESG/zhou111/Data/Case_Study/shp"
out_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/S1"
os.makedirs(out_dir, exist_ok=True)

basins = ["LaPlata", "Yangtze", "Rhine", "Indus"]

crops = {
    "Mainrice": ["mainrice"],
    "Secondrice": ["secondrice"],
    "Maize": ["maize"],
    "Soybean": ["soybean"],
    "Wheat": ["winterwheat"]
}

for basin in basins:
    for crop, aliases in crops.items():
        # Find the correct .nc file
        found_file = None
        for alias in aliases:
            fname = f"{basin}_{alias}_Yp.nc"
            fpath = os.path.join(base_nc, fname)
            if os.path.exists(fpath):
                found_file = fpath
                crop_used = alias
                break
        if found_file is None:
            continue  # skip if no file

        print(f"Processing: {os.path.basename(found_file)}")
        ds = xr.open_dataset(found_file)

        # Subset years 1986–2015 and take mean
        ds_sub = ds.sel(year=slice(1986, 2015)).mean(dim="year", skipna=True)

        # Load HA mask (specific for this basin/crop)
        mask_path = os.path.join(base_mask, basin, "Mask", f"{basin}_{crop_used}_mask.nc")
        if not os.path.exists(mask_path):
            print(f"!!! No mask for {basin}, skipping...")
            continue
        mask_ds = xr.open_dataset(mask_path)
        ha = mask_ds[list(mask_ds.data_vars)[3]]  # assume first var = HA
        mask = ha > 0

        # Apply mask to variables
        Yp   = ds_sub["Yp"].where(mask) if "Yp" in ds_sub else None
        GrowthDay = ds_sub["GrowthDay"].where(mask) if "GrowthDay" in ds_sub else None
        N_Uptake  = ds_sub["N_Uptake"].where(mask) if "N_Uptake" in ds_sub else None
        P_Uptake  = ds_sub["P_Uptake"].where(mask) if "P_Uptake" in ds_sub else None

        # Read basin shapefile
        shp_path = os.path.join(base_shp, basin, f"{basin}.shp")
        basin_shp = gpd.read_file(shp_path) if os.path.exists(shp_path) else None

        # Plot 2x2 subplots
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.ravel()
        plots = [(Yp, "Potential Yield"), 
                 (GrowthDay, "Growing Days"), 
                 (N_Uptake, "N Uptake"), 
                 (P_Uptake, "P Uptake")]

        for ax, (var, title) in zip(axes, plots):
            if var is not None:
                var.plot(ax=ax, cmap="viridis", add_colorbar=True)
            ax.set_title(f"{basin} - {crop_used} - {title} (1986–2015 avg)")
            if basin_shp is not None:
                basin_shp.boundary.plot(ax=ax, color="red", linewidth=1)

        plt.tight_layout()
        out_file = os.path.join(out_dir, f"{basin}_{crop_used}_1986-2015_avg.png")
        plt.savefig(out_file, dpi=300)
        plt.close()

        ds.close()
        mask_ds.close()
