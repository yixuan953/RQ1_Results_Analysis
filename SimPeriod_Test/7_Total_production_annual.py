# This code is used to plot how does the production change when reducing fertilization rate

import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

# === Paths ===
BaseDir = "/lustre/nobackup/WUR/ESG/zhou111"
DataDir = f"{BaseDir}/2_RQ1_Data/2_StudyArea"
BoundaryDir = f"{BaseDir}/3_RQ1_Model_Outputs/2_Critical_NP_losses"

Basins = ["Yangtze"] # ["Indus", "Rhine", "LaPlata", "Yangtze"]
CropTypes = ["mainrice"] # ["mainrice", "secondrice", "maize", "winterwheat", "soybean"]

start_year = 2010
end_year = 2019

# Baseline scenario
YieldDir= f"{BaseDir}/3_RQ1_Model_Outputs/3_Scenarios/2_1_Baseline"
PlotDir = f"{BaseDir}/4_RQ1_Analysis_Results/Red_Fert_Test/Baseline"

# # Fertilizer reduction scenario
# YieldDir= f"{BaseDir}/3_RQ1_Model_Outputs/3_Scenarios/2_3_Sus_Irri_Red_Fert/Red_org"
# PlotDir = f"{BaseDir}/4_RQ1_Analysis_Results/Red_Fert_Test/Red_org"

for basin in Basins:
    print(f"\n=== Processing {basin} ===")
    
    N_boundary_path = os.path.join(BoundaryDir, f"{basin}_crit_N_runoff_kgperha.nc")
    P_boundary_path = os.path.join(BoundaryDir, f"{basin}_crit_P_runoff_kgperha.nc")
    if not os.path.exists(N_boundary_path) or not os.path.exists(P_boundary_path):
        print(f"⚠️ Missing exceed file for {basin}, skipping.")
        continue
    N_boundary_ds = xr.open_dataset(N_boundary_path)
    P_boundary_ds = xr.open_dataset(P_boundary_path)

    for crop in CropTypes:
            print(f"  > {crop}")

            yield_path = os.path.join(YieldDir, f"{basin}_{crop}_annual.nc")
            if not os.path.exists(yield_path):
                print(f"    ⚠️ Missing yield file for {crop}, skipping.")
                continue
            yield_ds = xr.open_dataset(yield_path).sel(year=slice(start_year, end_year))
            yield_data = yield_ds["Yield"]
            N_runoff = yield_ds["N_Runoff"]
            P_runoff = yield_ds["P_Runoff"]

            exceed_mask = ((N_runoff > N_boundary_ds["critical_maincrop_N_runoff"]) |
                           (P_runoff > P_boundary_ds["critical_maincrop_P_runoff"])).astype(int)
            
            mask_file = os.path.join(DataDir, basin, "Mask", f"{basin}_{crop}_mask.nc")
            if not os.path.exists(mask_file):
                print(f"    ⚠️ Missing mask file for {crop}, skipping.")
                continue
            mask_ds = xr.open_dataset(mask_file)
            harvested_area = mask_ds["HA"]

            total_production = (yield_data * harvested_area).sum(dim=["lat", "lon"]) / 1000000  # In kilotons
            polluted_production = (yield_data * harvested_area * exceed_mask).sum(dim=["lat", "lon"]) / 1000000  # In kilotons
            years = total_production["year"].values

            # Plotting
            plt.figure(figsize=(8, 4))
            plt.plot(years, total_production, label="Total Production", linewidth=2)
            plt.ylim(37000,99000)
            plt.plot(years, polluted_production, label="Production contributed by area with excessive N, P losses", linewidth=2)
            plt.title(f"{basin} - {crop} (2010-2020)")
            plt.ylabel("Production (ktons/year)")
            plt.xlabel("Year")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            fig_path = os.path.join(PlotDir, f"{basin}_{crop}_production_2010-2020.png")
            plt.savefig(fig_path, dpi=300)
            plt.close()
            print(f"Saved yearly figure: {fig_path}")