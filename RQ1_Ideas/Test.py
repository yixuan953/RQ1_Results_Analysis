import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# -----------------------------
# User-defined parameters
# -----------------------------
csv_file = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Water-Nutrient-Limited/Indus_maize_monthly.csv"
basin = "Indus"  # change as needed
crop = "maize"
mask_file = f"/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea/{basin}/Mask/{basin}_{crop}_mask.nc"
shp_file = f"/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_shp_StudyArea/{basin}/{basin}.shp"
output_file = f"/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/RQ1_Ideas/Figure3/Test_{basin}_{crop}_monthly_leaching.png"

years = np.arange(1986, 2016)

# -----------------------------
# Load CSV
# -----------------------------
df = pd.read_csv(csv_file)

# Filter for years of interest
df = df[df['Year'].isin(years)]

# -----------------------------
# Load crop mask (HA)
# -----------------------------
mask_ds = xr.open_dataset(mask_file)
HA = mask_ds['HA']  # variable assumed to be HA
mask = HA > 2500

# -----------------------------
# Average monthly P leaching
# -----------------------------
monthly_avg = df.groupby(['Lat', 'Lon', 'Month'])['P_Leaching'].mean().reset_index()

lats = np.sort(monthly_avg['Lat'].unique())
lons = np.sort(monthly_avg['Lon'].unique())
months = np.arange(1, 13)

# Fill into 3D array [month, lat, lon]
P_leach_array = np.full((len(months), len(lats), len(lons)), np.nan)
lat_idx = {lat: i for i, lat in enumerate(lats)}
lon_idx = {lon: i for i, lon in enumerate(lons)}

for _, row in monthly_avg.iterrows():
    i = lat_idx[row['Lat']]
    j = lon_idx[row['Lon']]
    k = int(row['Month']) - 1
    P_leach_array[k, i, j] = row['P_Leaching']

# -----------------------------
# Align mask to CSV grid
# -----------------------------
# Convert boolean mask -> numeric (1 for True, 0 for False)
mask_numeric = mask.astype(int)

# Interpolate numeric mask to CSV grid
mask_interp = mask_numeric.interp(lat=lats, lon=lons)

# Convert back to boolean (threshold at 0.5)
mask_subset = (mask_interp.values > 0.5)

# Apply mask
P_leach_array_masked = np.where(mask_subset, P_leach_array, np.nan)

# -----------------------------
# Load basin shapefile
# -----------------------------
basin_gdf = gpd.read_file(shp_file)

# -----------------------------
# Plotting
# -----------------------------
fig, axes = plt.subplots(
    3, 4, figsize=(22, 14),
    subplot_kw={'projection': ccrs.PlateCarree()},
    constrained_layout=True  # <- better than tight_layout for Cartopy
)
axes = axes.flatten()

vmin = np.nanmin(P_leach_array_masked)
vmax = np.nanmax(P_leach_array_masked)

for m in range(12):
    ax = axes[m]
    im = ax.pcolormesh(
        lons, lats, P_leach_array_masked[m],
        transform=ccrs.PlateCarree(),
        shading='auto', cmap='viridis',
        vmin=vmin, vmax=vmax
    )
    # Only basin boundary
    basin_gdf.boundary.plot(ax=ax, edgecolor='red', linewidth=1.2, transform=ccrs.PlateCarree())
    # Add coastlines only
    ax.coastlines(resolution='50m', linewidth=0.8)
    ax.set_title(f"Month {m+1}", fontsize=14)

# Shared colorbar on the LEFT
cbar = fig.colorbar(
    im, ax=axes, orientation='vertical',
    fraction=0.03, pad=0.02, location='left'
)
cbar.set_label("P Leaching", fontsize=14)

plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()