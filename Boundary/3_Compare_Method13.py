# This code is used to compare the total critical agricultural N runoff of method 1 & 3

import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import os

# Input directory
N_runoff_M1_file = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/Critical_NP_losses/Global_agri_critical_N_load.nc"
N_runoff_M2_file = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/Global_crit_N_conc_load_agri.nc"
# Output directory
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/Boundary_test"

# Read the data
ds_M1 = xr.open_dataset(N_runoff_M1_file)
N_Agri_M1 = ds_M1["critical_agri_N_load"]  # kg

ds_M2 = xr.open_dataset(N_runoff_M2_file)
N_Agri_M2 = ds_M2["Crit_N_load_agri"]      # kg

# Mask fill values
N_Agri_M1 = 0.000001 * N_Agri_M1.where(np.isfinite(N_Agri_M1))
N_Agri_M2 = 0.000001 * N_Agri_M2.where(np.isfinite(N_Agri_M2))

# Define shared color range
vmin = 0
vmax = 5

# --- Plot ---
fig, axs = plt.subplots(1, 2, figsize=(16, 6),subplot_kw={'projection': ccrs.PlateCarree()})

plots = []

# --- Method 1 ---
im1 = axs[0].pcolormesh(
    N_Agri_M1.lon, N_Agri_M1.lat, N_Agri_M1,
    transform=ccrs.PlateCarree(),
    shading='auto', vmin=vmin, vmax=vmax
)
axs[0].set_title("Critical Agri N Runoff — Method 1")
axs[0].coastlines()
axs[0].add_feature(cfeature.BORDERS, linewidth=0.4)
plots.append(im1)

# --- Method 3 ---
im2 = axs[1].pcolormesh(
    N_Agri_M2.lon, N_Agri_M2.lat, N_Agri_M2,
    transform=ccrs.PlateCarree(),
    shading='auto', vmin=vmin, vmax=vmax
)
axs[1].set_title("Critical Agri N Runoff — Method 3")
axs[1].coastlines()
axs[1].add_feature(cfeature.BORDERS, linewidth=0.4)
plots.append(im2)

# --- Shared Colorbar ---
cbar = fig.colorbar(
    plots[1], ax=axs, orientation="horizontal",
    fraction=0.05, pad=0.08
)
cbar.set_label("Critical Agricultural N Runoff (ktons)")

outfig = os.path.join(output_dir, f"Global_crit_Agri_N_runoff_comp.png")
plt.savefig(outfig, dpi=300, bbox_inches='tight')
plt.show()

print("Figure saved to:", outfig)