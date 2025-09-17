import os
import pandas as pd
import matplotlib.pyplot as plt

# Paths
input_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_Decomp_off"
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/0_NP_Demand/S1_WL"
os.makedirs(output_dir, exist_ok=True)

# Target points
targets = {
     "Indus": {
        "mainrice": (32.25, 75.75),
        "maize": (31.75, 74.25),
         # "wheat": (32.75, 71.25),
     },
    "LaPlata": {
         "mainrice": (-26.25, -48.75),
         "maize": (-23.75, -48.25),
    #     "soybean": (-22.75, -47.75),
         # "wheat": (-26.25, -52.25),
     },
    "Rhine": {
        "maize": (51.75, 4.75),
        # "wheat": (48.75, 8.25),
    },
    "Yangtze": {
         "mainrice": (26.75, 114.25),
         "secondrice": (27.25, 117.25),
         "maize": (31.25, 117.75),
    #     "soybean": (33.75, 109.75),
         # "wheat": (29.75, 114.75),
    }
}

# Years of interest
start_year, end_year = 1996, 2015

# Crop-specific Dev_Stage cutoffs
stage_cutoffs = {"soybean": 1.5}
default_cutoff = 1.3

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

        # --- Data conditioning ---
        cutoff = stage_cutoffs.get(crop, default_cutoff)
        point_df["P_demand_cond"] = point_df["P_demand"].where(
            (point_df["Dev_Stage"] >= 0.0) & (point_df["Dev_Stage"] <= cutoff), 0
        )

        point_df["N_demand_cond"] = point_df["N_demand"].where(
            (point_df["Dev_Stage"] >= 0.0) & (point_df["Dev_Stage"] <= cutoff), 0
        )

        point_df["RootDepth_cond"] = point_df["RootDepth"].where(
            (point_df["Transpiration"] > 0.0), 0
        )

        point_df["Soil_Moisture_cond"] = point_df["SoilMoisture"].where(
            (point_df["SoilMoisture"] > 0.104), 0.104
        )

        point_df["P_supply2"] = point_df["P_avail"]                            
        point_df["N_supply"] = point_df["N_avail"]  

        # --- Figure 1: N Demand vs Supply (single plot) ---
        fig1, ax1 = plt.subplots(figsize=(12, 6))

        y_max = max(
            point_df["N_demand_cond"].max(),
            point_df["N_avail"].max()
        )

        ax1.plot(point_df["Date"], point_df["N_demand_cond"], color="tab:blue", label="N_demand")
        ax1.plot(point_df["Date"], point_df["N_supply"], color="tab:purple", label="N_availability = Remaining fertilization + decomposition + deposition")

        ax1.set_ylabel("Daily N demand and availability [kg/ha]")
        ax1.set_xlabel("Date")
        ax1.set_ylim(0, y_max * 1.1)
        ax1.legend(fontsize=8)
        ax1.grid(True, linestyle="--", alpha=0.5)

        fig1.suptitle(f"{studyarea} - {crop} P Demand vs Supply ({lat}, {lon}) | {start_year}-{end_year}", fontsize=14)
        fig1.tight_layout(rect=[0, 0, 1, 0.96])

        outpath1 = os.path.join(output_dir, f"{studyarea}_{crop}_N_{start_year}-{end_year}.png")
        fig1.savefig(outpath1, dpi=300)
        plt.close(fig1)



        # --- Figure 2: P Demand vs Supply (single plot) ---
        fig2, ax2 = plt.subplots(figsize=(12, 6))

        y_max = max(
            point_df["P_demand_cond"].max(),
            point_df["P_supply2"].max()
        )

        ax2.plot(point_df["Date"], point_df["P_demand_cond"], color="tab:blue", label="P_demand")
        ax2.plot(point_df["Date"], point_df["P_supply2"], color="tab:purple", label="P_availability = cPi * Soil moisture * Maximum root depth ")

        ax2.set_ylabel("Daily P demand and availability [kg/ha]")
        ax2.set_xlabel("Date")
        ax2.set_ylim(0, y_max * 1.1)
        ax2.legend(fontsize=8)
        ax2.grid(True, linestyle="--", alpha=0.5)

        fig2.suptitle(f"{studyarea} - {crop} P Demand vs availabiltiy ({lat}, {lon}) | {start_year}-{end_year}", fontsize=14)
        fig2.tight_layout(rect=[0, 0, 1, 0.96])

        outpath2 = os.path.join(output_dir, f"{studyarea}_{crop}_P_{start_year}-{end_year}.png")
        fig2.savefig(outpath2, dpi=300)
        plt.close(fig2)

        print(f"✅ Saved: {outpath1}")
        print(f"✅ Saved: {outpath2}")
