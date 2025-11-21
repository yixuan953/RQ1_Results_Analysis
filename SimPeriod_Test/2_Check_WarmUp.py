import pandas as pd
import matplotlib.pyplot as plt
import os

output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_1_Baseline"
plot_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/Warm_Up_test"

Basins = ["Rhine", "Indus", "Yangtze", "LaPlata"]
Crops = ["winterwheat", "maize", "mainrice", "secondrice", "soybean"]

checking_points = {
    "Indus": {
        "mainrice": (32.25, 75.75),
        "maize": (31.75, 74.25),
        "winterwheat": (32.75, 71.25),
    },
    "LaPlata": {
        "mainrice": (-26.25, -48.75),
        "maize": (-23.75, -48.25),
        "soybean": (-22.75, -47.75),
        "winterwheat": (-26.25, -52.25),
    },
    "Rhine": {
        "maize": (52.25, 4.75),
        "winterwheat": (48.75, 8.25),
    },
    "Yangtze": {
        "mainrice": (26.75, 114.25),
        "secondrice": (27.25, 117.25),
        "maize": (31.25, 117.75),
        "soybean": (33.75, 109.75),
        "winterwheat": (29.75, 114.75),
    }
}

os.makedirs(plot_dir, exist_ok=True)

for basin in Basins:
    for crop in Crops:
        # Skip crops without checkpoint
        if crop not in checking_points.get(basin, {}):
            continue

        lat_chk, lon_chk = checking_points[basin][crop]

        file = f"{output_dir}/{basin}_{crop}_daily.csv"
        if not os.path.exists(file):
            print(f"Missing file: {file}")
            continue

        ds = pd.read_csv(file)

        # Filter time range
        ds = ds[(ds["Year"] >= 2005) & (ds["Year"] <= 2019)]

        # Find closest grid cell to checkpoint
        ds["dist"] = (ds["Lat"] - lat_chk).abs() + (ds["Lon"] - lon_chk).abs()
        ds_point = ds.loc[ds["dist"].idxmin()].copy()  # single grid ID

        # Now filter dataset only for that grid
        lat_near = ds_point["Lat"]
        lon_near = ds_point["Lon"]
        df = ds[(ds["Lat"] == lat_near) & (ds["Lon"] == lon_near)]

        # Create a time axis (Year + Day of year)
        df["Date"] = pd.to_datetime(df["Year"].astype(str), format="%Y") + pd.to_timedelta(df["Day"] - 1, unit="D")

        # Plot
        fig, ax = plt.subplots(3, 1, figsize=(10, 9), sharex=True)

        ax[0].plot(df["Date"], df["SoilMoisture"], color="blue")
        ax[0].set_ylabel("Soil Moisture")

        ax[1].plot(df["Date"], df["Lpool"] * 30.974, color="red")
        ax[1].set_ylabel("Labile P pool (mg P/kg)")

        ax[2].plot(df["Date"], df["Spool"] * 30.974, color="green")
        ax[2].set_ylabel("Stable P pool (mg P/kg)")
        ax[2].set_xlabel("Time")

        fig.suptitle(f"{basin} - {crop} @ ({lat_near}, {lon_near})", fontsize=14, fontweight="bold")

        plt.tight_layout()
        plt.savefig(f"{plot_dir}/{basin}_{crop}_WarmUp_Check.png", dpi=300)
        plt.close()        

        
        
        


