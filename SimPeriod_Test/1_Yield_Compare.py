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
# crops = ["winterwheat", "mainrice", "maize"]   # adjust per basin

# studyarea = "Yangtze"   # change when looping
# crops = ["mainrice","secondrice","maize", "winterwheat", "soybean"]   # adjust per basin

# studyarea = "LaPlata"   # change when looping
# crops = ["soybean",  "maize",  "mainrice", "winterwheat"]   # adjust per basin

studyarea = "Rhine"   # change when looping
crops = ["winterwheat", "maize"]   # adjust per basin

# Directories
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/WOFOST-withoutNPLimit/Output"
dir_mask = f"/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea/{studyarea}/Mask"
shp_path = f"/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_shp_StudyArea/{studyarea}/{studyarea}.shp"
out_path_Yp = f"/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/1_Validation/CheckClimate/{studyarea}_Yp.png"
out_path_rainfed = f"/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/1_Validation/CheckClimate/{studyarea}_rainfed.png"

# Basin shapefile
basin = gpd.read_file(shp_path)

# -------------------------
# Figure setup with GridSpec
# -------------------------
nrows = len(crops)
ncols = 3
fig = plt.figure(figsize=(5*ncols, 5*nrows))
gs = gridspec.GridSpec(nrows, ncols, figure=fig, wspace=0.3, hspace=0.4)

global_vmin_rainfed, global_vmax_rainfed = np.inf, -np.inf
grids_all_rainfed = {}

global_vmin_Yp, global_vmax_Yp = np.inf, -np.inf
grids_all_Yp = {}

# -------------------------------
# Pass 1: compute global vmin/vmax
# -------------------------------
for crop in crops:
    # Wheat mask file uses "winterwheat"
    mask_crop = "winterwheat" if crop == "wheat" else crop
    mask_file = f"{dir_mask}/{studyarea}_{mask_crop}_mask.nc"
    mask = xr.open_dataset(mask_file)["HA"]

    # --- Read CSVs ---
    f1 = f"{output_dir}/{studyarea}_Yp_{crop}_Annual.csv"
    f2 = f"{output_dir}/{studyarea}_wl_noIrri_{crop}_Annual.csv"
    df1 = pd.read_csv(f1)
    df2 = pd.read_csv(f2)

    # Filter years
    df1_30y = df1[(df1["Year"]>=1990) & (df1["Year"]<=2019)]
    df1_10y = df1[(df1["Year"]>=2010) & (df1["Year"]<=2019)]  
    df2_30y = df2[(df2["Year"]>=1990) & (df2["Year"]<=2019)]
    df2_10y = df2[(df2["Year"]>=2010) & (df2["Year"]<=2019)] 

    # Average Storage
    df1_30y_mean = df1_30y.groupby(["Lat","Lon"])["Storage"].mean().reset_index()
    df1_10y_mean = df1_10y.groupby(["Lat","Lon"])["Storage"].mean().reset_index()

    df2_30y_mean = df2_30y.groupby(["Lat","Lon"])["Storage"].mean().reset_index()
    df2_10y_mean = df2_10y.groupby(["Lat","Lon"])["Storage"].mean().reset_index()

    merged_Yp = pd.merge(df1_30y_mean, df1_10y_mean, on=["Lat","Lon"], suffixes=("_30y","_10y"))
    merged_Yp["Dif_Yp"] =  merged_Yp["Storage_10y"] -merged_Yp["Storage_30y"]

    merged_rainfed = pd.merge(df2_30y_mean, df2_10y_mean, on=["Lat","Lon"], suffixes=("_30y","_10y"))
    merged_rainfed["Dif_rainfed"] = merged_rainfed["Storage_10y"] - merged_rainfed["Storage_30y"] 

    # Reindex onto mask grid
    df_mask = pd.DataFrame({
        "Lat": mask.lat.values.repeat(len(mask.lon)),
        "Lon": np.tile(mask.lon.values, len(mask.lat))
    })
    merged_Yp = pd.merge(df_mask, merged_Yp, on=["Lat","Lon"], how="left")
    merged_rainfed = pd.merge(df_mask, merged_rainfed, on=["Lat","Lon"], how="left")

    grid1_Yp = merged_Yp["Storage_30y"].values.reshape(len(mask.lat), len(mask.lon))
    grid2_Yp = merged_Yp["Storage_10y"].values.reshape(len(mask.lat), len(mask.lon))
    dif_Yp = merged_Yp["Dif_Yp"].values.reshape(len(mask.lat), len(mask.lon))

    grid1_rainfed = merged_rainfed["Storage_30y"].values.reshape(len(mask.lat), len(mask.lon))
    grid2_rainfed = merged_rainfed["Storage_10y"].values.reshape(len(mask.lat), len(mask.lon))
    dif_rainfed = merged_rainfed["Dif_rainfed"].values.reshape(len(mask.lat), len(mask.lon))

    # Apply mask
    mask_vals = mask.values

    # Rainfed
    grid1_rainfed = np.where(np.isnan(mask_vals), np.nan, grid1_rainfed)
    grid2_rainfed = np.where(np.isnan(mask_vals), np.nan, grid2_rainfed)
    dif_rainfed = np.where(np.isnan(mask_vals), np.nan, dif_rainfed)
    # store for later plotting
    grids_all_rainfed[crop] = (grid1_rainfed, grid2_rainfed, dif_rainfed, mask)
    # update global range
    crop_vmin_rainfed = np.nanmin([grid1_rainfed, grid2_rainfed])
    crop_vmax_rainfed = np.nanmax([grid1_rainfed, grid2_rainfed])
    global_vmin_rainfed = min(global_vmin_rainfed, crop_vmin_rainfed)
    global_vmax_rainfed = max(global_vmax_rainfed, crop_vmax_rainfed)

    # Yp
    grid1_Yp = np.where(np.isnan(mask_vals), np.nan, grid1_Yp)
    grid2_Yp = np.where(np.isnan(mask_vals), np.nan, grid2_Yp)
    dif_Yp = np.where(np.isnan(mask_vals), np.nan, dif_Yp)
    # store for later plotting
    grids_all_Yp[crop] = (grid1_Yp, grid2_Yp, dif_Yp, mask)
    # update global range
    crop_vmin_Yp = np.nanmin([grid1_Yp, grid2_Yp])
    crop_vmax_Yp = np.nanmax([grid1_Yp, grid2_Yp])
    global_vmin_Yp = min(global_vmin_Yp, crop_vmin_Yp)
    global_vmax_Yp = max(global_vmax_Yp, crop_vmax_Yp)

# -------------------------------
# Pass 2: plot with shared vmin/vmax
# -------------------------------
num_rows = len(crops)
fig_height = 3.5 * num_rows   # dynamic height
fig = plt.figure(figsize=(18, fig_height))
gs = fig.add_gridspec(num_rows, 3, wspace=0., hspace=0.3)

for i, crop in enumerate(crops):
    grid1_rainfed, grid2_rainfed, dif_rainfed, mask = grids_all_rainfed[crop]

    for j, (data, title) in enumerate(zip(
        [grid1_rainfed, grid2_rainfed, dif_rainfed],
        [f"{crop.upper()} - 30-year avg.",
         f"{crop.upper()} - 10-year avg.",
         f"{crop.upper()} - Differences"]
    )):
        ax = fig.add_subplot(gs[i, j])

        if j < 2:
            im = ax.pcolormesh(mask.lon, mask.lat, data,
                               cmap="YlGnBu", vmin=global_vmin_rainfed, vmax=global_vmax_rainfed)
            if j == 1:
                im_shared = im       # Save for shared avg colorbar
        else:
            im = ax.pcolormesh(mask.lon, mask.lat, data,
                               cmap="RdBu_r", vmin=-1000, vmax=1000)
            im_diff = im            # Save for shared difference colorbar

        basin.boundary.plot(ax=ax, edgecolor="black", linewidth=1)
        ax.set_title(title, fontsize=12, fontweight="bold", pad=15)

# Shared avg colorbar (bottom)
cbar_ax1 = fig.add_axes([0.25, 0.05, 0.5, 0.02])
fig.colorbar(im_shared, cax=cbar_ax1, orientation="horizontal",
             label="Average yield comparison [kg/ha]")

# Shared difference colorbar (right side)
cbar_ax2 = fig.add_axes([0.90, 0.20, 0.015, 0.6])  
fig.colorbar(im_diff, cax=cbar_ax2, orientation="vertical",
             label="Difference [kg/ha]")

plt.savefig(out_path_rainfed, dpi=300, bbox_inches="tight")
plt.close()


# -------------------------------
# Pass 3: plot with shared vmin/vmax
# -------------------------------
num_rows = len(crops)
fig_height = 3.5 * num_rows   # dynamic height
fig = plt.figure(figsize=(18, fig_height))
gs = fig.add_gridspec(num_rows, 3, wspace=0., hspace=0.3)

for i, crop in enumerate(crops):
    grid1_Yp, grid2_Yp, dif_Yp, mask = grids_all_Yp[crop]

    for j, (data, title) in enumerate(zip(
        [grid1_Yp, grid2_Yp, dif_Yp],
        [f"{crop.upper()} - 30-year avg.",
         f"{crop.upper()} - 10-year avg.",
         f"{crop.upper()} - Differences"]
    )):
        ax = fig.add_subplot(gs[i, j])

        if j < 2:
            im = ax.pcolormesh(mask.lon, mask.lat, data,
                               cmap="YlGnBu", vmin=global_vmin_Yp, vmax=global_vmax_Yp)
            if j == 1:
                im_shared = im
        else:
            im = ax.pcolormesh(mask.lon, mask.lat, data,
                               cmap="RdBu_r", vmin=-1000, vmax=1000)
            im_diff = im

        basin.boundary.plot(ax=ax, edgecolor="black", linewidth=1)
        ax.set_title(title, fontsize=12, fontweight="bold", pad=15)

# Shared avg colorbar (bottom)
cbar_ax1 = fig.add_axes([0.25, 0.05, 0.5, 0.02])
fig.colorbar(im_shared, cax=cbar_ax1, orientation="horizontal",
             label="Average yield comparison [kg/ha]")

# Shared difference colorbar (right side)
cbar_ax2 = fig.add_axes([0.90, 0.20, 0.015, 0.6])  
fig.colorbar(im_diff, cax=cbar_ax2, orientation="vertical",
             label="Difference [kg/ha]")

plt.savefig(out_path_Yp, dpi=300, bbox_inches="tight")
plt.close()
