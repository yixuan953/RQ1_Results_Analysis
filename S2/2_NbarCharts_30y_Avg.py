import os
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

# Input/output directories
csv_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_Decomp_off"
mask_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
out_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/0_NP_Balance/S1_WL"

# Groups
inputs = ["N_decomp", "N_dep", "N_fert"]
gaseous = ["NH3", "N2O", "NOx", "N2"]
water = ["N_surf", "N_sub", "N_leach"]
uptake = ["N_uptake"]
unused = ["N_unused_org_fert"]

studyareas = ["LaPlata", "Yangtze", "Indus", "Rhine"] # ["LaPlata", "Yangtze", "Indus", "Rhine"]
crops = ["maize"] # ["mainrice", "secondrice", "wheat", "soybean", "maize"]

for basin in studyareas:
    for crop in crops:
        mask_crop = "winterwheat" if crop == "wheat" else crop

        csv_file = os.path.join(csv_dir, f"{basin}_{crop}_annual.csv")
        mask_file = os.path.join(mask_dir, basin, "Mask", f"{basin}_{mask_crop}_mask.nc")
        if not os.path.exists(csv_file) or not os.path.exists(mask_file):
            continue

        print(f"Processing {basin} - {crop}")

        # Read CSV
        df = pd.read_csv(csv_file, delimiter=",", skipinitialspace=True)

        # Ensure numeric
        for col in inputs + gaseous + water + uptake + unused:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # >>> Recalculate N_fert here <<<
        df["N_fert"] = (
            df.get("N_fert", 0)
            + df.get("N_surf", 0)
            + df.get("NH3", 0)
            + df.get("N2O", 0)
            + df.get("NOx", 0)
        )

        # Filter years
        df = df[(df["Year"] >= 1986) & (df["Year"] <= 2015)]
        df = df.dropna(subset=inputs + gaseous + water + uptake + unused)
        if df.empty:
            continue

        # Average across years per pixel
        avg_df = df.groupby(["Lat", "Lon"])[inputs + gaseous + water + uptake + unused].mean().reset_index()

        # Load mask
        mask = xr.open_dataset(mask_file)
        ha = mask["HA"].load()

        ha_df = ha.to_dataframe().reset_index()
        ha_valid = ha_df[~ha_df["HA"].isna()][["lat", "lon", "HA"]]

        # Merge HA with avg_df
        merged = avg_df.merge(
            ha_valid, left_on=["Lat", "Lon"], right_on=["lat", "lon"], how="inner"
        )
        if merged.empty:
            continue

        # Compute weighted averages
        total_ha = merged["HA"].sum()
        weighted = {}
        for group, cols in [
            ("Inputs", inputs),
            ("Uptake & losses", gaseous + water + uptake)
        ]:
            weighted[group] = {}
            for col in cols:
                weighted[group][col] = (merged[col] * merged["HA"]).sum() / total_ha
                # weighted[group][col] = (merged[col] * merged["HA"]).sum()
        # Colors
        colors = {
            # Inputs
            "N_decomp": "#ffcc66",  # light orange
            "N_dep": "#744714",     # medium orange
            "N_fert": "#f86b3c",    # dark red-orange

            # Gaseous (pink/purple)
            "NH3": "#5d3951",
            "N2O": "#cc66cc",
            "NOx": "#F9CEF9",
            "N2": "#BD84BD",

            # Water (blueish)
            "N_surf": "#a9d2fa",
            "N_sub": "#3399ff",
            "N_leach": "#003366",

            # Uptake (green)
            "N_uptake": "#377d37"
        }

        # Plot stacked bar chart
        fig, ax = plt.subplots(figsize=(7, 6))

        categories = ["Inputs", "Uptake & losses"]
        bottom = [0, 0]

        for i, cat in enumerate(categories):
            for comp, val in weighted[cat].items():
                ax.bar(cat, val, bottom=bottom[i],
                       label=comp if comp not in ax.get_legend_handles_labels()[1] else "",
                       color=colors.get(comp, None))
                bottom[i] += val

        ax.set_ylabel("kg N  yr⁻¹ (basin average)")
        ax.set_title(f"{basin} - {crop} (1986-2015 average)")
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

        plt.tight_layout()

        out_file = os.path.join(out_dir, f"{basin}_{crop}_NbarCharts_30yAvg_totalN.png")
        plt.savefig(out_file, dpi=300, bbox_inches="tight")
        plt.close()