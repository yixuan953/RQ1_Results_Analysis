import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import geopandas as gpd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from mpl_toolkits.axes_grid1 import make_axes_locatable

# -------------------------
# Config
# -------------------------
# studyarea = "Indus"   # change when looping
# crops = ["mainrice", "maize", "wheat"]   # adjust per basin

# studyarea = "Yangtze"   # change when looping
# crops = ["mainrice","secondrice", "maize", "wheat", "soybean"]   # adjust per basin

# studyarea = "LaPlata"   # change when looping
# crops = ["mainrice", "maize", "wheat", "soybean"]   # adjust per basin

studyarea = "Rhine"   # change when looping
crops = ["maize", "wheat"]   # adjust per basin

# Checking points
checking_points = {
    "Indus": {
        "mainrice": (32.25, 75.75),
        "maize": (31.75, 74.25),
        "wheat": (32.75, 71.25),
    },
    "LaPlata": {
        "mainrice": (-26.25, -48.75),
        "maize": (-23.75, -48.25),
        "soybean": (-22.75, -47.75),
        "wheat": (-26.25, -52.25),
    },
    "Rhine": {
        "maize": (52.25, 4.75),
        "wheat": (48.75, 8.25),
    },
    "Yangtze": {
        "mainrice": (26.75, 114.25),
        "secondrice": (27.25, 117.25),
        "maize": (31.25, 117.75),
        "soybean": (33.75, 109.75),
        "wheat": (29.75, 114.75),
    }
}

# Directories
dir_S1 = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/S1"
dir_S2 = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/S2"
dir_mask = f"/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea/{studyarea}/Mask"
shp_path = f"/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_shp_StudyArea/{studyarea}/{studyarea}.shp"
out_path = f"/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/Sall/{studyarea}_Yp_WNlY_30yAvg.png"


# Basin shapefile
basin = gpd.read_file(shp_path)

# -------------------------
# Figure setup with GridSpec
# -------------------------
nrows = len(crops)
ncols = 3
fig = plt.figure(figsize=(5*ncols, 5*nrows))
gs = gridspec.GridSpec(nrows, ncols, figure=fig, wspace=0.3, hspace=0.4)

global_vmin, global_vmax = np.inf, -np.inf
grids_all = {}

# -------------------------------
# Pass 1: compute global vmin/vmax
# -------------------------------
for crop in crops:
    # Wheat mask file uses "winterwheat"
    mask_crop = "winterwheat" if crop == "wheat" else crop
    mask_file = f"{dir_mask}/{studyarea}_{mask_crop}_mask.nc"
    mask = xr.open_dataset(mask_file)["HA"]

    # --- Read CSVs ---
    f1 = f"{dir_S1}/{studyarea}_{mask_crop}_annual.csv"
    f2 = f"{dir_S2}/{studyarea}_{crop}_annual.csv"
    df1 = pd.read_csv(f1)
    df2 = pd.read_csv(f2)

    # Filter years
    df1 = df1[(df1["Year"]>=1986) & (df1["Year"]<=2015)]
    df2 = df2[(df2["Year"]>=1986) & (df2["Year"]<=2015)]

    # Average Storage
    df1_mean = df1.groupby(["Lat","Lon"])["Storage"].mean().reset_index()
    df2_mean = df2.groupby(["Lat","Lon"])["Storage"].mean().reset_index()

    merged = pd.merge(df1_mean, df2_mean, on=["Lat","Lon"], suffixes=("_S1","_S2"))
    merged["ratio"] = merged["Storage_S2"]/merged["Storage_S1"]

    # Reindex onto mask grid
    df_mask = pd.DataFrame({
        "Lat": mask.lat.values.repeat(len(mask.lon)),
        "Lon": np.tile(mask.lon.values, len(mask.lat))
    })
    merged = pd.merge(df_mask, merged, on=["Lat","Lon"], how="left")

    grid1 = merged["Storage_S1"].values.reshape(len(mask.lat), len(mask.lon))
    grid2 = merged["Storage_S2"].values.reshape(len(mask.lat), len(mask.lon))
    ratio = merged["ratio"].values.reshape(len(mask.lat), len(mask.lon))

    # Apply mask
    mask_vals = mask.values
    grid1 = np.where(np.isnan(mask_vals), np.nan, grid1)
    grid2 = np.where(np.isnan(mask_vals), np.nan, grid2)
    ratio = np.where(np.isnan(mask_vals), np.nan, ratio)

    # store for later plotting
    grids_all[crop] = (grid1, grid2, ratio, mask)

    # update global range
    crop_vmin = np.nanmin([grid1, grid2])
    crop_vmax = np.nanmax([grid1, grid2])
    global_vmin = min(global_vmin, crop_vmin)
    global_vmax = max(global_vmax, crop_vmax)


# -------------------------------
# Pass 2: plot with shared vmin/vmax
# -------------------------------
for i, crop in enumerate(crops):
    grid1, grid2, ratio, mask = grids_all[crop]

    for j, (data, title) in enumerate(zip(
        [grid1, grid2, ratio],
        [f"{crop.upper()} - Potential yield",
         f"{crop.upper()} - Water & nutrient-limited yield",
         f"{crop.upper()} - 80% Yp achieved"]
    )):
        ax = fig.add_subplot(gs[i,j])
        if j < 2:
            im = ax.pcolormesh(mask.lon, mask.lat, data,
                               cmap="YlGnBu", vmin=global_vmin, vmax=global_vmax)
            if j == 1:
                im_shared = im  # save for colorbar
        else:
            class_map = np.full(data.shape, np.nan)
            class_map[data < 0.6] = 1
            class_map[(data >= 0.6) & (data < 0.8)] = 2
            class_map[data >= 0.8] = 3
            cmap3 = plt.matplotlib.colors.ListedColormap(["#ffffff","#fcf4ec","#f3907ae4"])
            ax.pcolormesh(mask.lon, mask.lat, class_map, cmap=cmap3)

        basin.boundary.plot(ax=ax, edgecolor="black", linewidth=1)
        ax.set_title(title, fontsize=12, fontweight="bold", pad=15)

        if crop in checking_points[studyarea]:
            latc, lonc = checking_points[studyarea][crop]
            ax.plot(lonc, latc, marker="*", color="red", markersize=15)

# Add one shared colorbar
cbar_ax = fig.add_axes([0.25, 0.05, 0.5, 0.02])
fig.colorbar(im_shared, cax=cbar_ax, orientation="horizontal",
             label="Average yield [kg/ha] (1986–2015)")

plt.savefig(out_path, dpi=300, bbox_inches="tight")
plt.close()