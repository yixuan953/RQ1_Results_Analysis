import os
import pandas as pd
import geopandas as gpd
import xarray as xr
import matplotlib.pyplot as plt

# Input/output directories
csv_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Water-Nutrient-Limited"
shp_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_shp_StudyArea"
mask_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
out_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/RQ1_Ideas/Figure3"

# Variables to plot
n_vars = [
    "N_fert", "N_decomp", "N_uptake",
    "N_surf", "N_sub", "N_leach",
    "NH3", "N2O", "NOx"
]

# Study areas and crops
studyareas = ["LaPlata", "Yangtze", "Indus", "Rhine"] # ["LaPlata", "Yangtze", "Indus", "Rhine"]
crops = ["maize"] #["mainrice", "secondrice", "wheat", "soybean", "maize"]

for basin in studyareas:
    for crop in crops:
        # adjust crop name for mask
        mask_crop = "winterwheat" if crop == "wheat" else crop

        csv_file = os.path.join(csv_dir, f"{basin}_{crop}_annual.csv")
        mask_file = os.path.join(mask_dir, basin, "Mask", f"{basin}_{mask_crop}_mask.nc")
        if not os.path.exists(csv_file) or not os.path.exists(mask_file):
            continue  # Skip if data not available

        print(f"Processing {basin} - {crop}")

        # Read csv
        df = pd.read_csv(csv_file, delimiter=",", skipinitialspace=True)

        # Convert variables to numeric
        for col in n_vars:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Filter years
        df = df[(df["Year"] >= 1986) & (df["Year"] <= 2015)]

        # Drop rows with NaN
        df = df.dropna(subset=n_vars)
        if df.empty:
            print(f" -> No valid data for {basin} - {crop}, skipping.")
            continue

        # Average across years
        avg_df = df.groupby(["Lat", "Lon"])[n_vars].mean().reset_index()

        # Load mask file
        mask = xr.open_dataset(mask_file)
        ha = mask["HA"].load()

        # Valid HA cells
        ha_df = ha.to_dataframe().reset_index()
        ha_valid = ha_df[~ha_df["HA"].isna()][["lat", "lon"]]

        # Merge with avg_df
        merged = avg_df.merge(
            ha_valid, left_on=["Lat", "Lon"], right_on=["lat", "lon"], how="inner"
        )
        if merged.empty:
            print(f" -> No overlap with mask for {basin} - {crop}, skipping.")
            continue

        # Load basin shapefile
        shp_path = os.path.join(shp_dir, basin, f"{basin}.shp")
        basin_gdf = gpd.read_file(shp_path)

        # Create 3x3 subplot figure
        fig, axes = plt.subplots(3, 3, figsize=(15, 12), subplot_kw={'aspect': 'equal'})
        axes = axes.flatten()

        for i, var in enumerate(n_vars):
            ax = axes[i]

            # Pivot table to 2D grid
            grid = merged.pivot_table(index="Lat", columns="Lon", values=var)

            lats = grid.index.values
            lons = grid.columns.values
            vals = grid.values

            mesh = ax.pcolormesh(lons, lats, vals, cmap="viridis", shading="auto")
            basin_gdf.boundary.plot(ax=ax, color="black", linewidth=1)

            fig.colorbar(mesh, ax=ax, shrink=0.7)
            ax.set_title(var, fontsize=12)
            ax.set_axis_off()

        plt.suptitle(f"{basin} - {crop} (1986-2015 average) [kg/ha]", fontsize=16, y=1.02)

        # Save figure
        out_file = os.path.join(out_dir, f"{basin}_{crop}_Nmaps_30yAvg.png")
        plt.tight_layout()
        plt.savefig(out_file, dpi=300, bbox_inches="tight")
        plt.close()
