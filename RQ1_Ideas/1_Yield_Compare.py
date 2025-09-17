import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import geopandas as gpd
from pathlib import Path
import glob
import matplotlib.gridspec as gridspec

# Basins and crops
basins = ["LaPlata", "Indus", "Yangtze", "Rhine"] # ["LaPlata", "Indus", "Yangtze", "Rhine"]
crops = ["maize"] # ["wheat", "maize", "rice", "soybean"]

# Filepath templates
yp_tpl = Path("/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Yp/{basin}_{crop}_annual.csv")
wl_tpl = Path("/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Water-Limited/{basin}_{crop}_annual.csv")
wn_tpl = Path("/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Water-Nutrient-Limited/{basin}_{crop}_annual.csv")
mask_tpl = Path("/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea/{basin}/Mask/{basin}_{crop}_mask.nc")
shp_base = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_shp_StudyArea"

out_dir = Path("/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/RQ1_Ideas/Figure1")
out_dir.mkdir(parents=True, exist_ok=True)

# Discrete bins for columns 2 & 3
bins = [0, 20, 40, 60, 80, 100]
colors = ['#f7fbff','#c6dbef','#6baed6','#2171b5','#08306b']
cmap_discrete = mcolors.ListedColormap(colors)
norm_discrete = mcolors.BoundaryNorm(bins, cmap_discrete.N)

for basin in basins:
    shp_dir = f"{shp_base}/{basin}"
    shp_files = glob.glob(f"{shp_dir}/*.shp")
    if not shp_files:
        print(f"No shapefile found for {basin}, skipping.")
        continue
    shp_fp = shp_files[0]
    basin_shp = gpd.read_file(shp_fp)

    basin_crops = [crop for crop in crops if yp_tpl.with_name(f"{basin}_{crop}_annual.csv").exists()]
    if not basin_crops:
        continue

    nrow = len(basin_crops)

    # Set up gridspec
    fig = plt.figure(figsize=(18, 5*nrow))
    gs = gridspec.GridSpec(nrow, 3, figure=fig, wspace=0.25, hspace=0.3)
    axes = np.empty((nrow,3), dtype=object)
    for i in range(nrow):
        for j in range(3):
            axes[i,j] = fig.add_subplot(gs[i,j])

    for i, crop in enumerate(basin_crops):
        # Load CSVs
        yp = pd.read_csv(yp_tpl.with_name(f"{basin}_{crop}_annual.csv"))
        wl = pd.read_csv(wl_tpl.with_name(f"{basin}_{crop}_annual.csv"))
        wn = pd.read_csv(wn_tpl.with_name(f"{basin}_{crop}_annual.csv"))

        # Subset years
        yp = yp[(yp["Year"] >= 1986) & (yp["Year"] <= 2015)]
        wl = wl[(wl["Year"] >= 1986) & (wl["Year"] <= 2015)]
        wn = wn[(wn["Year"] >= 1986) & (wn["Year"] <= 2015)]

        # Compute mean per pixel
        yp_mean = yp.groupby(["Lat","Lon"])["Storage"].mean()
        wl_mean = wl.groupby(["Lat","Lon"])["Storage"].mean()
        wn_mean = wn.groupby(["Lat","Lon"])["Storage"].mean()

        df = pd.DataFrame({"Yp": yp_mean, "S1": wl_mean, "S2": wn_mean}).reset_index()
        df["S1_ratio"] = df["S1"]/df["Yp"]*100
        df["S2_ratio"] = df["S2"]/df["Yp"]*100

        # Load mask
        mask_fp = Path(f"/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea/{basin}/Mask/{basin}_{crop}_mask.nc")
        mask = xr.open_dataset(mask_fp)
        ha_var = [v for v in mask.data_vars if "HA" in v or "mask" in v][0]
        mask_vals = mask[ha_var].values
        lats = mask["lat"].values
        lons = mask["lon"].values

        latlon_index = {(lat, lon):(i,j) for i,lat in enumerate(lats) for j,lon in enumerate(lons)}
        grid_shape = (len(lats), len(lons))
        Yp_grid = np.full(grid_shape, np.nan)
        S1_grid = np.full(grid_shape, np.nan)
        S2_grid = np.full(grid_shape, np.nan)

        for _, row in df.iterrows():
            key = (row["Lat"], row["Lon"])
            if key in latlon_index:
                i_idx, j_idx = latlon_index[key]
                if mask_vals[i_idx, j_idx] > 250:
                    Yp_grid[i_idx,j_idx] = row["Yp"]
                    S1_grid[i_idx,j_idx] = row["S1_ratio"]
                    S2_grid[i_idx,j_idx] = row["S2_ratio"]

        # Column 1: Potential yield
        im1 = axes[i,0].imshow(Yp_grid, origin="upper", cmap="Oranges",
                               extent=[lons.min(),lons.max(),lats.min(),lats.max()])
        axes[i,0].set_title(f"Potential yield of {crop} (kg/ha/year)", fontsize=12)

        # Column 2: Water-limited ratio (discrete)
        im2 = axes[i,1].imshow(S1_grid, origin="upper", cmap=cmap_discrete, norm=norm_discrete,
                               extent=[lons.min(),lons.max(),lats.min(),lats.max()])
        axes[i,1].set_title(f"Irrigated {crop} yield without nutrient limitation (% of Yp)", fontsize=12)

        # Column 3: Water+Nutrient-limited ratio (discrete)
        im3 = axes[i,2].imshow(S2_grid, origin="upper", cmap=cmap_discrete, norm=norm_discrete,
                               extent=[lons.min(),lons.max(),lats.min(),lats.max()])
        axes[i,2].set_title(f"Irrigated and fertilized {crop} yield (% of Yp)", fontsize=12)

        # Plot shapefile boundaries
        for ax in axes[i,:]:
            basin_shp.boundary.plot(ax=ax, color="black", linewidth=0.5)

    # Overall title
    fig.suptitle(f"Average yield of {basin} river basin (1986-2015)", fontsize=16)

    # Colorbars below the figure
    cbar_ax1 = fig.add_axes([0.03, 0.15, 0.015, 0.6])
    cbar1 = fig.colorbar(im1, cax=cbar_ax1, orientation='vertical')
    cbar1.set_label("Potential Yield (kg/ha)", labelpad=5)

    cbar_ax2 = fig.add_axes([0.93, 0.15, 0.015, 0.6])
    cbar2 = fig.colorbar(im2, cax=cbar_ax2, orientation='vertical', ticks=bins)
    cbar2.set_label("% of Yp", labelpad=5)

    # Save figure
    out_fp = out_dir / f"{basin}_Yp_Ya_30yAvg.png"
    fig.savefig(out_fp, dpi=300)
    plt.close(fig)
