# This code is used to calculate and plot the share of agricultural N, P runoff

import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import os

# Input directory
IMAGE_file_N = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE/Output-IMAGE_GNM-SSP1_oct2020-Nitrogen_Rivers-v2.nc"
ds_IMAGE_N = xr.open_dataset(IMAGE_file_N)
total_N_load_all = ds_IMAGE_N["Naquaculture"] + ds_IMAGE_N["Ndeposition_water"] + ds_IMAGE_N["Ngroundwater_agri"] + ds_IMAGE_N["Ngroundwater_nat"] +ds_IMAGE_N["Nsurface_runoff_agri"] + ds_IMAGE_N["Nsurface_runoff_nat"] + ds_IMAGE_N["Nsewage"] + ds_IMAGE_N["Nvegetation"] 
total_N_load = total_N_load_all.sel(time = "2015-05-01")
agri_N_load = ds_IMAGE_N["Nsurface_runoff_agri"].sel(time = "2015-05-01")
frac_agri_N_load = 100 * agri_N_load/total_N_load # %

# Input directory
IMAGE_file_P = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE/Output-IMAGE_GNM-SSP1_oct2020-Phosphorus_Rivers-v2.nc"
ds_IMAGE_P = xr.open_dataset(IMAGE_file_P)
total_P_load_all = ds_IMAGE_P["Paquaculture"] + ds_IMAGE_P["Psewage"]  + ds_IMAGE_P["Psurface_runoff_agri"] + ds_IMAGE_P["Psurface_runoff_nat"]  + ds_IMAGE_P["Pvegetation"]  + ds_IMAGE_P["Pweathering"]
total_P_load = total_P_load_all.sel(time = "2015-05-01")
agri_P_load = ds_IMAGE_P["Psurface_runoff_agri"].sel(time = "2015-05-01")
frac_agri_P_load = 100 * agri_P_load/total_P_load # %

# --- Plot ---
fig, axs = plt.subplots(1, 2, figsize=(16, 6),subplot_kw={'projection': ccrs.PlateCarree()})

vmin = 0
vmax = 100

plots = []

# --- Method 1 ---
im1 = axs[0].pcolormesh(
    frac_agri_N_load.lon, frac_agri_N_load.lat, frac_agri_N_load,
    transform=ccrs.PlateCarree(),
    shading='auto', vmin=vmin, vmax=vmax
)
axs[0].set_title("Share of agricultural N runoff")
axs[0].coastlines()
axs[0].add_feature(cfeature.BORDERS, linewidth=0.4)
plots.append(im1)

# --- Method 3 ---
im2 = axs[1].pcolormesh(
    frac_agri_P_load.lon, frac_agri_P_load.lat, frac_agri_P_load,
    transform=ccrs.PlateCarree(),
    shading='auto', vmin=vmin, vmax=vmax
)
axs[1].set_title("Share of agricultural P runoff")
axs[1].coastlines()
axs[1].add_feature(cfeature.BORDERS, linewidth=0.4)
plots.append(im2)

# --- Shared Colorbar ---
cbar = fig.colorbar(
    plots[1], ax=axs, orientation="horizontal",
    fraction=0.05, pad=0.08
)
cbar.set_label("Share of agricultural N, P runoff (%)")

output_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/Boundary_test"
outfig = os.path.join(output_dir, f"Global_share_agri_NP_runoff.png")
plt.savefig(outfig, dpi=300, bbox_inches='tight')
plt.show()

print("Figure saved to:", outfig)