import pandas as pd
import xarray as xr
import numpy as np
import os
import matplotlib.pyplot as plt

basins = ["LaPlata", "Indus", "Yangtze", "Rhine"]
crops = ["mainrice", "secondrice", "winterwheat", "soybean", "maize"]

startyear = 2005
endyear = 2014

for basin in basins:
    plt.figure(figsize=(8, 5))
    for crop in crops:
        Irr_file = f"/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea/{basin}/Unsus_Irrigation/{basin}_{crop}_monthly_Irri_Rate.nc"
        mask_file = f"/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea/{basin}/Mask/{crop}_HA_Irrigated.nc"

        # Skip if files don’t exist
        if not os.path.exists(Irr_file) or not os.path.exists(mask_file):
            print(f"Skipping {basin}-{crop} (file missing)")
            continue

        # Load mask and select HA > 2500
        mask_nc = xr.open_dataset(mask_file)
        HA = mask_nc["area_total"]
        HA_mask = xr.where(HA > 2500, 1, 0)  # corrected mask

        # Load irrigation rate
        Irri_nc = xr.open_dataset(Irr_file)
        Irri_rate = Irri_nc["Irrigation_Rate"]

        # Select the period 2005–2015
        Irri_rate_sel = Irri_rate.sel(time=slice(f"{startyear}-01-01", f"{endyear}-12-31"))

        # Apply mask (broadcast automatically)
        Irri_masked = Irri_rate_sel * HA_mask * HA

        # Compute spatial mean (weighted by mask)
        spatial_mean = Irri_masked.mean(dim=["lat", "lon"], skipna=True)

        # Plot monthly average
        plt.plot(spatial_mean["time"], spatial_mean, label=crop)

        plt.title(f"Monthly Average Irrigation (2005–2015) — {basin}")
        plt.xlabel("Month")
        plt.ylabel("Irrigation Rate")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        fig_path = f"/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/1_Validation/CheckIrri/{basin}_{crop}_unsus_irri.png"
        plt.savefig(fig_path, dpi=300)
        plt.close()
        print(f" Saved overlayed summary bar chart: {fig_path}")       