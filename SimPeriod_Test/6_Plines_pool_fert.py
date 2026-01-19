import os
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

# Baseline scenario
csv_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_1_Baseline"
# out_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/Red_Fert_Test/Baseline"
out_dir = '/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/2_Model_Adj'

# # Fertilizer reduction scenario
# csv_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_3_Sus_Irri_Red_Fert/Red_org"
# out_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/Red_Fert_Test/Red_org"

mask_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"

studyareas = ["Yangtze"] # ["LaPlata", "Yangtze", "Indus", "Rhine"]
crops = ["mainrice"] # ["mainrice", "secondrice", "winterwheat", "soybean", "maize"]

for basin in studyareas:
    for crop in crops:
        mask_crop = "winterwheat" if crop == "wheat" else crop

        csv_file = os.path.join(csv_dir, f"{basin}_{crop}_annual.csv")
        mask_file = os.path.join(mask_dir, basin, "Mask", f"{basin}_{mask_crop}_mask.nc")
        if not os.path.exists(csv_file) or not os.path.exists(mask_file):
            continue

        print(f"Processing {basin} - {crop}")

        # Load CSV
        df = pd.read_csv(csv_file, delimiter=",", skipinitialspace=True)
        vars_pool = ["LabileP", "StableP"]
        vars_flux = ["P_decomp", "P_fert"]

        for col in vars_pool + vars_flux:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Keep 1986–2015
        df = df[(df["Year"] >= 2005) & (df["Year"] <= 2019)]

        # Load mask
        mask = xr.open_dataset(mask_file)
        ha = mask["HA"].load()   # ha per pixel
        bd = mask["bulk_density"].load()  # kg/dm³ per pixel

        # Merge HA & BD with df
        mask_df = xr.merge([ha, bd]).to_dataframe().reset_index()
        mask_df = mask_df.dropna(subset=["HA", "bulk_density"])

        merged = df.merge(mask_df, left_on=["Lat","Lon"], right_on=["lat","lon"], how="inner")

        if merged.empty:
            continue

        results = []
        for year, g in merged.groupby("Year"):
            # Pools: area‐weighted with HA*BD
            pool_den = (g["HA"] * g["bulk_density"]).sum()
            labile_avg = (g["LabileP"] * g["HA"] * g["bulk_density"]).sum() / pool_den
            stable_avg = (g["StableP"] * g["HA"] * g["bulk_density"]).sum() / pool_den

            # Fluxes: area‐weighted with HA
            ha_tot = g["HA"].sum()
            p_decomp_avg = (g["P_decomp"] * g["HA"]).sum() / ha_tot
            p_fert_avg = (g["P_fert"] * g["HA"]).sum() / ha_tot

            results.append([year, labile_avg, stable_avg, p_decomp_avg, p_fert_avg])

        ts = pd.DataFrame(results, columns=["Year","LabileP","StableP","P_decomp","P_fert"])


        # ---- Plot ----
        fig, ax1 = plt.subplots(figsize=(9,6))

        # Pools (greens)
        ax1.plot(ts["Year"], ts["LabileP"], label="LabileP", color="#23bb97", lw=2)
        ax1.plot(ts["Year"], ts["StableP"], label="StableP", color="#1A8361", lw=2)
        ax1.set_ylabel("Soil P pools (mmol/kg)")
        ax1.set_xlabel("Year")
        ax1.set_ylim(0, 13)

        # Inputs (reds)
        ax2 = ax1.twinx()
        ax2.plot(ts["Year"], ts["P_decomp"], label="P_decomp", color="#e7b41c", lw=2, ls="--")
        ax2.plot(ts["Year"], ts["P_fert"], label="P_fert", color="#f15627", lw=2, ls="--")
        ax2.set_ylabel("P inputs (kg/ha/yr)")
        ax2.set_ylim(0, 30)

        # Combine legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1+lines2, labels1+labels2, bbox_to_anchor=(1.05,1), loc="upper left")

        plt.title(f"{basin} - {crop} Basin Average", y=1.02)
        plt.tight_layout()

        out_file = os.path.join(out_dir, f"{basin}_{crop}_Plines_pools_fert_Annual.png")
        plt.savefig(out_file, dpi=300, bbox_inches="tight")
        plt.close()

