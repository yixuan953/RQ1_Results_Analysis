import pandas as pd
import xarray as xr
import numpy as np
import os

basins = ["LaPlata", "Indus", "Yangtze", "Rhine"]
crops = ["winterwheat", "maize", "mainrice", "soybean", "secondrice"]

# Variables of interest
vars_interest = ["Storage","GrowthDay","N_decomp","N_dep","N_fix","N_fert","NH3","N2O","NOx","N2",
                 "N_surf","N_sub","N_leach","N_uptake",
                 "P_decomp","P_dep","P_fert","LabileP","StableP","PrecP","P_acc",
                 "P_surf","P_sub","P_leach","P_uptake"]

for basin in basins:
    for crop in crops:
        csv_file = f"/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Ya-Limited-Irrigation/{basin}_{crop}_annual.csv"
        mask_file = f"/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea/{basin}/Mask/{basin}_{crop}_mask.nc"
        out_file = f"/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/1_Validation/GYGA/{basin}_{crop}_GYGA_Ya-Limited-Irrigation.csv"

        # Skip if files don’t exist
        if not os.path.exists(csv_file) or not os.path.exists(mask_file):
            print(f"Skipping {basin}-{crop} (file missing)")
            continue

        print(f"Processing {basin}-{crop} ...")

        # 1) Load mask and select HA > 2500
        ds_mask = xr.open_dataset(mask_file)
        HA = ds_mask["HA"]
        mask_pixels = HA.where(HA > 2500).dropna(dim="lat", how="all").dropna(dim="lon", how="all")
        mask_df = mask_pixels.to_dataframe().reset_index()
        mask_df = mask_df.dropna(subset=["HA"])

        # 2) Load model CSV
        df = pd.read_csv(csv_file)
        df = df[(df["Year"] >= 1986) & (df["Year"] <= 2015)]

        # 3) Mean per pixel
        df_mean = df.groupby(["Lat","Lon"])[vars_interest].mean().reset_index()

        # 4) Keep only pixels with HA > 2500
        df_valid = df_mean.merge(mask_df[["lat","lon"]], left_on=["Lat","Lon"], right_on=["lat","lon"], how="inner")

        if df_valid.empty:
            print(f"No valid pixels for {basin}-{crop}, skipping.")
            continue

        # 5) Compute percentiles
        percentiles = {}
        for v in vars_interest:
            percentiles[f"{v}_10"] = np.percentile(df_valid[v], 10)
            percentiles[f"{v}_90"] = np.percentile(df_valid[v], 90)

        # 6) Save
        out_df = pd.DataFrame([percentiles])
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        out_df.to_csv(out_file, index=False)

        print(f"Saved results -> {out_file}")
