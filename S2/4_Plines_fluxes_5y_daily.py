import os
import pandas as pd
import matplotlib.pyplot as plt

# Input/output directories
indir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_Decomp_off"
outdir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/Test_Decomp_off"
os.makedirs(outdir, exist_ok=True)

# Define target points for each basin/crop
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

for basin, crops in targets.items():
    for crop, (lat, lon) in crops.items():
        infile = os.path.join(indir, f"{basin}_{crop}_daily.csv")
        if not os.path.exists(infile):
            print(f"⚠️ File not found: {infile}")
            continue

        # Load data
        df = pd.read_csv(infile)

        # Select the grid cell (exact lat/lon match assumed)
        df_sel = df[(df["Lat"] == lat) & (df["Lon"] == lon)]
        df_sel = df_sel[(df_sel["Year"] >= 1989) & (df_sel["Year"] <= 1990)]

        if df_sel.empty:
            print(f"⚠️ No data found for {basin} {crop} at ({lat},{lon})")
            continue

        # Construct a daily datetime index
        df_sel["Date"] = pd.to_datetime(df_sel["Year"].astype(str), format="%Y") + pd.to_timedelta(df_sel["Day"] - 1, unit="D")

        # Apply condition for P_demand (set to 0 outside dev stage range)
        df_sel["P_demand_cond"] = df_sel.apply(lambda r: r["P_demand"] if 0.0 <= r["Dev_Stage"] <= 1.3 else 0, axis=1)

        # === Plot ===
        fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

        # Subplot 1: Lpool, Spool
        axes[0].plot(df_sel["Date"], df_sel["Lpool"], label="Lpool")
        axes[0].plot(df_sel["Date"], df_sel["Spool"], label="Spool")
        axes[0].set_ylabel("mmol/kg soil")
        axes[0].legend()
        axes[0].set_title(f"{basin} - {crop} ({lat}, {lon})")

        # Subplot 2: P_demand, P_avail
        axes[1].plot(df_sel["Date"], df_sel["P_demand_cond"], label="P_demand")
        axes[1].plot(df_sel["Date"], df_sel["P_avail"], label="P_avail")
        axes[1].set_ylabel("P (kg/ha)")
        axes[1].legend()

        # Subplot 3: P_Uptake, P_Surf, P_Sub, P_Leaching
        axes[2].plot(df_sel["Date"], df_sel["P_Uptake"], label="P_Uptake")
        axes[2].plot(df_sel["Date"], df_sel["P_Surf"], label="P_Surf")
        axes[2].plot(df_sel["Date"], df_sel["P_Sub"], label="P_Sub")
        axes[2].plot(df_sel["Date"], df_sel["P_Leaching"], label="P_Leaching")
        axes[2].set_ylabel("P flux (kg/ha)")
        axes[2].legend()

        plt.xlabel("Date")
        plt.tight_layout()

        # Save
        outfile = os.path.join(outdir, f"{basin}_{crop}_Pdaily_1981-1990.png")
        plt.savefig(outfile, dpi=300)
        plt.close()

        print(f"✅ Saved: {outfile}")
