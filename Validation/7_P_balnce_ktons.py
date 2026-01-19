import os 
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

# Input/output directories
# # Baseline scenario
# csv_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_1_Baseline"
# out_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/Red_Fert_Test/Baseline"

# # Sustainable irrigation scenario
# csv_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_2_Sus_Irrigation"
# out_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/Red_Fert_Test/Sus_Irri"

# # Reduced fertilizer scenario
# csv_dir = '/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_3_Sus_Irri_Red_Fert/Red_org'
# out_dir = '/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/Red_Fert_Test/Red_org'

csv_dir = '/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_1_Baseline'
out_dir = '/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/2_Model_Adj'

mask_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"

# P flux variables
p_inputs = ["P_decomp", "P_dep", "P_fert"]
p_outputs = ["P_uptake", "P_surf", "P_sub", "P_leach", "P_pool_acc"]
p_vars = p_inputs + p_outputs 

studyareas = ["LaPlata"] # ["LaPlata", "Yangtze", "Indus", "Rhine"]
crops = ["maize"] # ["mainrice", "secondrice", "winterwheat", "soybean", "maize"]


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
        df["P_pool_acc"] = df.get("P_fert") + df.get("P_decomp") + df.get("P_dep") - df.get("P_uptake") - df.get("P_surf") - df.get("P_sub") - df.get("P_leach")
        
        # Convert P variables to numeric
        for col in p_vars:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Filter years
        df = df[(df["Year"] >= 2010) & (df["Year"] <= 2019)]
        df = df.dropna(subset=p_vars)
        if df.empty:
            continue

        # Average across years per pixel
        avg_df = df.groupby(["Lat", "Lon"])[p_vars].mean().reset_index()

        # Load mask
        mask = xr.open_dataset(mask_file)
        ha = mask["HA"].load()
        ha_df = ha.to_dataframe().reset_index()
        ha_valid = ha_df[~ha_df["HA"].isna()][["lat", "lon", "HA"]]

        # Merge with avg_df
        merged = avg_df.merge(
            ha_valid, left_on=["Lat", "Lon"], right_on=["lat", "lon"], how="inner"
        )
        if merged.empty:
            continue

        # Compute area-weighted averages
        total_ha = merged["HA"].sum()
        weighted = {}
        for group, cols in [("Inputs", p_inputs), ("Uptake, losses & accumulation", p_outputs)]:
            weighted[group] = {}
            for col in cols:
                # weighted[group][col] = (merged[col] * merged["HA"]).sum() / total_ha
                weighted[group][col] = (merged[col] * merged["HA"] * 0.000001).sum() # Transform to ktons

        #  Print values
        print(f"\nArea-weighted averages for {basin} - {crop}:")
        for group, vals in weighted.items():
            print(f"  {group}:")
            for col, val in vals.items():
                print(f"    {col}: {val:.3f}")

        # Colors
        colors = {
            # Inputs (reddish)
            "P_decomp": "#ffcc66",  # light orange
            "P_dep": "#744714",     # medium orange
            "P_fert": "#f86b3c",    # dark red-orange

            # Water (blueish)
            "P_surf": "#a9d2fa",
            "P_sub": "#3399ff",
            "P_leach": "#003366",

            # Uptake (green)
            "P_uptake": "#377d37",

            # Accumulation (purple)
            "P_pool_acc": "#F0A6EBD5"
        }

        # Plot stacked bar chart
        fig, ax = plt.subplots(figsize=(7, 6))

        categories = ["Inputs", "Uptake, losses & accumulation"]
        bottom = [0, 0]

        for i, cat in enumerate(categories):
            for comp, val in weighted[cat].items():
                # Adjust legend for P_acc
                label = comp
                if comp == "P_acc":
                    label = "P_acc (±)"
                # Handle negative bars properly
                ax.bar(
                    cat, val,
                    bottom=bottom[i] if val >= 0 else 0,
                    label=label if label not in ax.get_legend_handles_labels()[1] else "",
                    color=colors.get(comp, None)
                )
                if val >= 0:
                    bottom[i] += val

        ax.set_ylabel("ktons P yr⁻¹")

        ax.set_title(f"{basin} - {crop} (2010 - 2019 average)")
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        # ax.set_ylim(-5, 30)

        plt.tight_layout()

        out_file = os.path.join(out_dir, f"{basin}_{crop}_PbarCharts_Avg.png")
        plt.savefig(out_file, dpi=300, bbox_inches="tight")
        plt.close()