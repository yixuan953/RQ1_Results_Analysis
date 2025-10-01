import pandas as pd
import xarray as xr
import numpy as np
from pathlib import Path

# Parameters
basins = ["Indus", "Yangtze", "LaPlata", "Rhine"]
crops = ["winterwheat", "maize", "mainrice", "soybean", "secondrice"]
years = range(1986, 2016)
threshold = 250  # HA threshold for masking

# Base paths
base_mask = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
base_out = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/2_Focus_Masks"

base_yp   = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Yp-Irrigated"
base_ypl  = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Yp-Limited-Irrigation"
base_ypr  = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Yp-Rainfed"

base_yaf  = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Ya-Irrigated"
base_yal  = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Ya-Limited-Irrigation"
base_yar  = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Ya-Rainfed"

# Helper: load and average
def load_avg(path):
    df = pd.read_csv(path)
    df = df[df["Year"].between(1986, 2015)]
    grouped = df.groupby(["Lat", "Lon"])["Storage"].mean().reset_index()
    return grouped

for basin in basins:
    for crop in crops:
        print(f"Processing {basin} - {crop}...")
        
        # File paths
        mask_path = f"{base_mask}/{basin}/Mask/{basin}_{crop}_mask.nc"
        paths = {
            "Yp":      f"{base_yp}/{basin}_{crop}_annual.csv",
            "Yp_lim":  f"{base_ypl}/{basin}_{crop}_annual.csv",
            "Yp_rain": f"{base_ypr}/{basin}_{crop}_annual.csv",
            "Ya_full": f"{base_yaf}/{basin}_{crop}_annual.csv",
            "Ya_lim":  f"{base_yal}/{basin}_{crop}_annual.csv",
            "Ya_rain": f"{base_yar}/{basin}_{crop}_annual.csv"
        }
        out_path = f"{base_out}/{basin}_{crop}_mask_80Yp.nc"

        # Check if mask + all input files exist
        if not Path(mask_path).is_file():
            print(f"  ⚠️ Skipping {basin}-{crop}: no mask")
            continue
        if not all(Path(p).is_file() for p in paths.values()):
            print(f"  ⚠️ Skipping {basin}-{crop}: missing yield files")
            continue

        # Load mask
        mask_ds = xr.open_dataset(mask_path)
        HA = mask_ds["HA"]
        lats, lons = HA.lat.values, HA.lon.values

        # Load and rename yields immediately
        try:
            Yp = load_avg(paths["Yp"])
            Yp["Storage_Yp"] = Yp["Storage"]; Yp = Yp.drop(columns=["Storage"])
            
            Yp_lim = load_avg(paths["Yp_lim"])
            Yp_lim["Storage_Yp_lim"] = Yp_lim["Storage"]; Yp_lim = Yp_lim.drop(columns=["Storage"])
            
            Yp_rain = load_avg(paths["Yp_rain"])
            Yp_rain["Storage_Yp_rain"] = Yp_rain["Storage"]; Yp_rain = Yp_rain.drop(columns=["Storage"])
            
            Ya_full = load_avg(paths["Ya_full"])
            Ya_full["Storage_full"] = Ya_full["Storage"]; Ya_full = Ya_full.drop(columns=["Storage"])
            
            Ya_lim = load_avg(paths["Ya_lim"])
            Ya_lim["Storage_lim"] = Ya_lim["Storage"]; Ya_lim = Ya_lim.drop(columns=["Storage"])
            
            Ya_rain = load_avg(paths["Ya_rain"])
            Ya_rain["Storage_rain"] = Ya_rain["Storage"]; Ya_rain = Ya_rain.drop(columns=["Storage"])
        
        except Exception as e:
            print(f"  ⚠️ Failed to load CSVs for {basin}-{crop}: {e}")
            continue

        # Merge all on Lat/Lon without suffixes
        merged = Yp.merge(Ya_full, on=["Lat","Lon"])
        merged = merged.merge(Ya_lim, on=["Lat","Lon"])
        merged = merged.merge(Ya_rain, on=["Lat","Lon"])
        merged = merged.merge(Yp_lim, on=["Lat","Lon"])
        merged = merged.merge(Yp_rain, on=["Lat","Lon"])

        # Ensure unique pixels
        merged = merged.groupby(["Lat","Lon"]).mean().reset_index()

        # Init arrays
        mask_full            = np.full((len(lats), len(lons)), np.nan)
        mask_lim             = np.full_like(mask_full, np.nan)
        mask_rain_Yp         = np.full_like(mask_full, np.nan)
        mask_rain_Yp_rainfed = np.full_like(mask_full, np.nan)
        mask_yplim           = np.full_like(mask_full, np.nan)
        mask_yprain          = np.full_like(mask_full, np.nan)

        for _, row in merged.iterrows():
            lat, lon = float(row["Lat"]), float(row["Lon"])
            if lat in lats and lon in lons:
                i = np.where(lats == lat)[0][0]
                j = np.where(lons == lon)[0][0]

                ha_val = HA.sel(lat=lat, lon=lon).item()
                if np.isnan(ha_val) or ha_val <= threshold:
                    # explicitly assign NaN (though arrays are already initialized with NaN)
                    mask_full[i,j] = np.nan
                    mask_lim[i,j] = np.nan
                    mask_rain_Yp[i,j] = np.nan
                    mask_rain_Yp_rainfed[i,j] = np.nan
                    mask_yplim[i,j] = np.nan
                    mask_yprain[i,j] = np.nan
                    continue

                # Extract scalar values safely
                def scalar(val):
                    if isinstance(val, pd.Series):
                        val = val.iloc[0]
                    return float(val)

                Yp_val      = scalar(row["Storage_Yp"])
                Ya_full_val = scalar(row["Storage_full"])
                Ya_lim_val  = scalar(row["Storage_lim"])
                Ya_rain_val = scalar(row["Storage_rain"])
                Yp_lim_val  = scalar(row["Storage_Yp_lim"])
                Yp_rain_val = scalar(row["Storage_Yp_rain"])

                # Compare actual yields
                mask_full[i,j] = 1 if Ya_full_val > 0.8 * Yp_val else 0
                mask_lim[i,j]  = 1 if Ya_lim_val > 0.8 * Yp_val else 0
                mask_rain_Yp[i,j] = 1 if Ya_rain_val > 0.8 * Yp_val else 0
                mask_rain_Yp_rainfed[i,j] = 1 if Ya_rain_val > 0.8 * Yp_rain_val else 0

                # Compare potential yields
                mask_yplim[i,j]  = 1 if Yp_lim_val > 0.8 * Yp_val else 0
                mask_yprain[i,j] = 1 if Yp_rain_val > 0.8 * Yp_val else 0

        # Save
        out_ds = xr.Dataset(
            {
                "Full_irrigation_actual_fert": (("lat", "lon"), mask_full),
                "Limited_irrigation_actual_fert": (("lat", "lon"), mask_lim),
                "Rainfed_actual_fert_CompYp": (("lat", "lon"), mask_rain_Yp),
                "Rainfed_actual_fert_CompYpRainfed": (("lat", "lon"), mask_rain_Yp_rainfed),
                "Limited_irrigation_suff_fert": (("lat", "lon"), mask_yplim),
                "Rainfed_suff_fert": (("lat", "lon"), mask_yprain),
            },
            coords={"lat": lats, "lon": lons}
        )
        out_ds.to_netcdf(out_path)
        print(f" ✅ Saved {out_path}")
