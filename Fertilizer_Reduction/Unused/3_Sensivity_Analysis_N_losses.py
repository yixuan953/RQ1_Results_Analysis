# This code is used to plot 
# x-aixis: Fertilizer input amount (kg N/ha)
# y-axis: N losses through runoff (kg N/ha)

import os
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt

# study areas and crop types
studyareas =  ["LaPlata"] # ["Indus", "Rhine", "LaPlata", "Yangtze"]
croptypes = ["soybean"] # ["mainrice", "secondrice", "maize", "soybean", "winterwheat"]

# Harvest area
ha_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
cropland_type = "Rainfed" # or "Rainfed"

# Baseline scenario
baseline_csv_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_1_Baseline"
# Fertilizer reduction scenario
red_csv_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_3_Rainfed"
red_scenario = ["Red_org", "Red_08", "Red_09", "Red_11", "Red_12", "Red_13", "Red_14", "Red_15", "Red_20", "Red_25", "Red_30", "Red_35", "Red_40", "Red_50"]

all_csv_dirs = [(sce, os.path.join(red_csv_dir, sce)) for sce in red_scenario] + [("Baseline", baseline_csv_dir)]

# Output directory for plots
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/Red_Fert_Test/Sens_Analsyis"

# Variables to analyze
vars = ["N_fert_input", "N_runoff", "Storage", "N_uptake"]

for basin in studyareas:
    for crop in croptypes:

        # ======= Load harvest area =========
        if crop == "winterwheat":
            mask_crop = "WHEA"
        elif crop == "maize":
            mask_crop = "MAIZ"
        elif crop == "soybean":
            mask_crop = "SOYB"
        elif crop == "mainrice" and basin != "Yangtze":
            mask_crop = "MAINRICE "
        elif crop == "mainrice" and basin == "Yangtze":
            mask_crop = "MAINRICE"
        elif crop == "secondrice":
            mask_crop = "SECONDRICE"
        
        ha_file = os.path.join(ha_dir, basin, "Harvest_Area", f"{mask_crop}_{cropland_type}_Harvest_Area_05d_{basin}.nc")
        if not os.path.exists(ha_file):
            print(f"!!! Harvest area file missing for {basin} - {crop}, skipping...")
            continue
        ha_ds = xr.open_dataset(ha_file)
        harvest_area = ha_ds["Harvest_Area"].values  # in ha

        # ======= Initialize storage for weighted averages =======
        scenario_weighted = {}

        for scen_name, csv_dir in all_csv_dirs:
            # ======== Load model output =========
            base_csv_file = os.path.join(csv_dir, f"{basin}_{crop}_annual.csv")
            if not os.path.exists(base_csv_file):
                print(f"!!! Baseline CSV missing for {basin} - {crop}, skipping...")
                continue
            base_df = pd.read_csv(base_csv_file)

            # Calculate baseline total N losses through runoff, and fertilizer input
            base_df["N_runoff"] = (base_df.get("N_surf", 0) + base_df.get("N_sub", 0))
            base_df["N_fert_input"] = (base_df.get("N_fert", 0) + base_df.get("N_surf", 0) + base_df.get("NH3", 0) + base_df.get("N2O", 0) + base_df.get("NOx", 0))
            base_df = base_df[(base_df["Year"] >= 2010) & (base_df["Year"] <= 2019)]
            if base_df.empty:
                continue

            # Average across years per pixel
            avg_df = base_df.groupby(["Lat", "Lon"])[vars].mean().reset_index()

            # Merge HA with avg_df
            ha_df = ha_ds.to_dataframe().reset_index()
            ha_valid = ha_df[~ha_df["Harvest_Area"].isna()][["lat", "lon", "Harvest_Area"]]
            merged = avg_df.merge(
                ha_valid, left_on=["Lat", "Lon"], right_on=["lat", "lon"], how="inner")
            if merged.empty:
                continue
            # Compute weighted averages
            total_ha = merged["Harvest_Area"].sum()

            weighted = {}
            for var in vars:
                weighted[var] = (merged[var] * merged["Harvest_Area"]).sum() / total_ha

            scenario_weighted[scen_name] = weighted

        # ======= Plotting =======
        if scenario_weighted:
            scen_names = list(scenario_weighted.keys())
            xs = [float(scenario_weighted[s]["N_fert_input"]) for s in scen_names]
            ys = [float(scenario_weighted[s]["N_runoff"]) for s in scen_names]

            # sort by fertilizer input for a nice line plot
            order = np.argsort(xs)
            xs_s = np.array(xs)[order]
            ys_s = np.array(ys)[order]
            names_s = [scen_names[i] for i in order]

            plt.figure(figsize=(6, 5))
            plt.plot(xs_s, ys_s, linestyle="--", marker="o", color="C0")
            for x, y, n in zip(xs_s, ys_s, names_s):
                plt.annotate(n, (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8)

            plt.xlabel("N fertilizer input (kg N/ha)")
            plt.ylabel("N runoff (kg N/ha)")
            plt.title(f"{basin} - {crop} (avg 2010-2019)")
            plt.xlim(1.5, 6.0)
            plt.ylim(40.70, 41.10)
            plt.grid(True)

            out_png = os.path.join(output_dir, f"{basin}_{crop}_{cropland_type}_Nrunoff_vs_Nfert.png")
            plt.tight_layout()
            plt.savefig(out_png, dpi=300)
            plt.close()
            print(f"Saved sensitivity plot to {out_png}")          