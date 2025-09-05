import os
import pandas as pd
import matplotlib.pyplot as plt

# Paths
input_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_Decomp_off"
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/P_Check"
os.makedirs(output_dir, exist_ok=True)

# Target points
targets = {
    "Indus": {
        "mainrice": (32.25, 75.75),
        "maize": (31.75, 74.25),
        "wheat": (32.75, 71.25),
    },
    "LaPlata": {
        "mainrice": (-26.25, -48.75),
        "maize": (-23.75, -48.25),
        "soybean": (-22.75, -47.75),
        "wheat": (-26.25, -52.25),
    },
    "Rhine": {
        "maize": (52.25, 4.75),
        "wheat": (48.75, 8.25),
    },
    "Yangtze": {
        "mainrice": (26.75, 114.25),
        "secondrice": (27.25, 117.25),
        "maize": (31.25, 117.75),
        "soybean": (33.75, 109.75),
        "wheat": (29.75, 114.75),
    }
}

# Variables and titles
varlist = ["P_demand", "Transpiration", "cPi", "RootDepth"]
titles = ["P demand (kg/ha)", "Transpiration & SoilMoisture", "cPi", "Root depth (m)"]

# Years of interest
start_year, end_year = 1989, 1990

for studyarea, crops in targets.items():
    for crop, (lat, lon) in crops.items():
        filename = f"{studyarea}_{crop}_daily.csv"
        filepath = os.path.join(input_dir, filename)
        if not os.path.exists(filepath):
            print(f"⚠️ Missing file: {filepath}")
            continue

        # Load data
        df = pd.read_csv(filepath)

        # Extract the point
        point_df = df[(df["Lat"] == lat) & (df["Lon"] == lon)]
        if point_df.empty:
            print(f"⚠️ No data for {studyarea} {crop} at ({lat}, {lon})")
            continue

        # Restrict to years
        point_df = point_df[(point_df["Year"] >= start_year) & (point_df["Year"] <= end_year)]

        # Make a datetime index
        point_df["Date"] = pd.to_datetime(point_df["Year"].astype(str), format="%Y") + \
                           pd.to_timedelta(point_df["Day"] - 1, unit="D")

        # Plot
        fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

        # 1. P_demand (only when Dev_Stage between 0.0 and 1.3)
        # Define crop-specific Dev_Stage cutoffs
        stage_cutoffs = {
            "soybean": 1.5
        }
        default_cutoff = 1.3

        # Inside your loop, after filtering df_sel
        cutoff = stage_cutoffs.get(crop, default_cutoff)

        df["P_demand_cond"] = df["P_demand"].where((df["Dev_Stage"] >= 0.0) & (df["Dev_Stage"] <= cutoff), 0)

        axes[0].plot(point_df.loc["Date"], point_df.loc["P_demand_cond"], label="P_demand", color="tab:blue")
        axes[0].set_ylabel(titles[0])
        axes[0].legend(loc="upper right", fontsize=8)
        axes[0].grid(True, linestyle="--", alpha=0.5)

        # 2. Transpiration + SoilMoisture
        axes[1].plot(point_df["Date"], point_df["Transpiration"], label="Transpiration", color="tab:green")
        axes[1].plot(point_df["Date"], point_df["SoilMoisture"], label="SoilMoisture", color="tab:orange")
        axes[1].set_ylabel(titles[1])
        axes[1].legend(loc="upper right", fontsize=8)
        axes[1].grid(True, linestyle="--", alpha=0.5)

        # 3. cPi
        axes[2].plot(point_df["Date"], point_df["cPi"], label="cPi", color="tab:red")
        axes[2].set_ylabel(titles[2])
        axes[2].legend(loc="upper right", fontsize=8)
        axes[2].grid(True, linestyle="--", alpha=0.5)

        # 4. RootDepth
        axes[3].plot(point_df["Date"], point_df["RootDepth"], label="RootDepth", color="tab:purple")
        axes[3].set_ylabel(titles[3])
        axes[3].legend(loc="upper right", fontsize=8)
        axes[3].grid(True, linestyle="--", alpha=0.5)

        axes[-1].set_xlabel("Date")
        fig.suptitle(f"{studyarea} - {crop} ({lat}, {lon}) | {start_year}-{end_year}", fontsize=14)

        # Save
        outpath = os.path.join(output_dir, f"{studyarea}_{crop}_P_demand_supply_{start_year}-{end_year}.png")
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(outpath, dpi=300)
        plt.close()

        print(f"✅ Saved: {outpath}")
