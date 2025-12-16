import xarray as xr
import numpy as np
import os
import matplotlib.pyplot as plt

# Input directory
IMAGE_file_P = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE/Output-IMAGE_GNM-SSP1_oct2020-Phosphorus_Rivers-v2.nc"
ds_IMAGE_P = xr.open_dataset(IMAGE_file_P)
P_conc = ds_IMAGE_P["Pconc"].sel(time = "2015-05-01")
P_values = P_conc.values.flatten()

# Remove NaNs and extreme fill values (>1e5 or < -1e5)
P_values = P_values[np.isfinite(P_values)]
P_values = P_values[(P_values > -1e5) & (P_values < 1e5)]

# Compute percentiles
percentiles = np.percentile(P_values, [10, 20, 25, 30, 50, 70, 75, 80, 90])

print("Global P concentration percentiles for 2015-05-01:")
print(f"10%: {percentiles[0]:.4f}")
print(f"20%: {percentiles[1]:.4f}")
print(f"25%: {percentiles[2]:.4f}")
print(f"30%: {percentiles[3]:.4f}")
print(f"50%: {percentiles[4]:.4f}")
print(f"70%: {percentiles[5]:.4f}")
print(f"75%: {percentiles[6]:.4f}")
print(f"80%: {percentiles[7]:.4f}")
print(f"90%: {percentiles[8]:.4f}")

# ---- Plot histogram ----
plt.figure(figsize=(8,5))
plt.hist(P_values, bins=50)
plt.xlabel("P concentration [mg P/L]")
plt.ylabel("Frequency")
plt.title("Histogram of Global P Concentration (2015)")
plt.grid(True, linestyle="--", alpha=0.4)
plt.tight_layout()

# ---- Save as PNG ----
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/Boundary_test"
outfig = f"{output_dir}/Histogram_Pconc.png"
plt.savefig(outfig, dpi=300, bbox_inches="tight")

plt.close()  # close the figure

print("Histogram saved to:", outfig)