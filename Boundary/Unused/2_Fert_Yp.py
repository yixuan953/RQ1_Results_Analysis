import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np

# Inputs
basin = "Yangtze"  # example
crop = "mainrice"     # example
csv_file = f"/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Yp-Irrigated/{basin}_{crop}_annual.csv"
mask_file = f"/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/2_Focus_Masks/{basin}_{crop}_mask_80Yp.nc"
shp_file = f"/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_shp_StudyArea/{basin}/{basin}.shp"
out_png = f"/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/4_NP_fert/{basin}_{crop}_NP_fert_Yp.png"

# Read data
csv = pd.read_csv(csv_file)
mask_ds = xr.open_dataset(mask_file)
basin_shp = gpd.read_file(shp_file)

# Average N_fert and P_fert over 1986–2015
period = csv[(csv['Year'] >= 1986) & (csv['Year'] <= 2015)]
mean_vals = period.groupby(['Lat','Lon'])[['N_fert','P_fert']].mean().reset_index()

# Plot
fig, axes = plt.subplots(1,2, figsize=(14,6), constrained_layout=True)

# N_fert plot
axN = axes[0]
scN = axN.scatter(mean_vals['Lon'], mean_vals['Lat'], c=mean_vals['N_fert'], s=30, cmap='viridis')
basin_shp.boundary.plot(ax=axN, color='black')
axN.set_title('Mean N_fert (1986-2015)')
fig.colorbar(scN, ax=axN, shrink=0.8)

# P_fert plot
axP = axes[1]
scP = axP.scatter(mean_vals['Lon'], mean_vals['Lat'], c=mean_vals['P_fert'], s=30, cmap='viridis')
basin_shp.boundary.plot(ax=axP, color='black')
axP.set_title('Mean P_fert (1986-2015)')
fig.colorbar(scP, ax=axP, shrink=0.8)

plt.savefig(out_png, dpi=300)
plt.close()
print(f"Saved figure: {out_png}")