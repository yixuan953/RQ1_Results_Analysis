import pandas as pd
import xarray as xr
import numpy as np
import os

basins = ["LaPlata", "Indus", "Yangtze", "Rhine"]
crops = ["mainrice",  "secondrice", "winterwheat", "soybean", "maize"]

startyear = 1986
endyear = 2015

for basin in basins:
    for crop in crops:
        csv_file = f"/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Output_Unsus_Irrigation/{basin}_{crop}_annual.csv"
        mask_file = f"/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea/{basin}/Mask/{basin}_{crop}_mask.nc"
        out_file = f"/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/1_Validation/NP_balance/{basin}_{crop}_NP.csv"

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
        df = df[(df["Year"] >= startyear) & (df["Year"] <= endyear)]

        # 3) Validation variabled
        df["N_app"] = df["N_fert"] + df["N_surf"] + df["N2O"] + df["NOx"] + df["NH3"] + df ["N2"]
        df["N_runoff"] = df["N_surf"] + df["N_sub"]
        df["total_N_loss"] = df["N_runoff"] + df["N_leach"] +  df["N_surf"] + df["N2O"] + df["NOx"] + df["NH3"] + df ["N2"]
        df["total_N_uptake_loss"] = df["total_N_loss"]  + df["N_uptake"]
        df["N_surplus"] = df["N_leach"] + df["N_sub"] + df["N2"]
        df["N_runoff_perc"] = df["N_runoff"]/df["N_app"]
        df["N_leach_perc"] = df["N_leach"]/df["N_app"]
        df["NH3_perc"] = df["NH3"]/df["N_app"]
        df["N2O_perc"] = df["N2O"]/df["N_app"]
        df["NOx_perc"] = df["NOx"]/df["N_app"]

        # Variables for validation
        val_variables = ["N_runoff", "total_N_loss", "total_N_uptake_loss", "N_surplus", "N_runoff_perc", "N_leach_perc", "NH3_perc", "N2O_perc","NOx_perc", "P_acc", "NH3","N2O","NOx","N2","N_surf","N_sub","N_leach","N_uptake","P_surf","P_sub","P_leach","P_uptake"]
        
        # 3) Mean per pixel over time period
        df_mean = df.groupby(["Lat","Lon"])[val_variables].mean().reset_index()

        # 4) Keep only pixels with HA > 2500
        df_valid = df_mean.merge(mask_df[["lat","lon"]], left_on=["Lat","Lon"], right_on=["lat","lon"], how="inner")

        if df_valid.empty:
            print(f"No valid pixels for {basin}-{crop}, skipping.")
            continue

        # 5) Compute percentiles
        percentiles = {}
        for v in val_variables:
            percentiles[f"{v}_10"] = np.percentile(df_valid[v], 10)
            percentiles[f"{v}_90"] = np.percentile(df_valid[v], 90)

        # 6) Save
        out_df = pd.DataFrame([percentiles])
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        out_df.to_csv(out_file, index=False)

        print(f"Saved results -> {out_file}")
