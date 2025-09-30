import os
import numpy as np
import pandas as pd
import xarray as xr

# ------------------- USER SETTINGS -------------------
basins = ["LaPlata", "Indus", "Yangtze", "Rhine"]
crops = ["winterwheat", "maize", "mainrice", "secondrice", "soybean"]

base_model_path = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs"
mask_base = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
out_base = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/1_Validation/GYGA-minNPinput"
os.makedirs(out_base, exist_ok=True)

mask_var = "HA"
mask_threshold = 2500
year_min, year_max = 1986, 2015

scenario_paths = {
    "Yp": os.path.join(base_model_path, "Yp-Irrigated", "{basin}_{crop}_annual.csv"),
    "Irrigated": os.path.join(base_model_path, "Ya-Irrigated", "{basin}_{crop}_annual.csv"),
    "Limited-Irrigated": os.path.join(base_model_path, "Ya-Limited-Irrigation", "{basin}_{crop}_annual.csv"),
    "Rainfed": os.path.join(base_model_path, "Ya-Rainfed", "{basin}_{crop}_annual.csv"),
}
# -----------------------------------------------------

def read_mask(basin, crop):
    mask_path = os.path.join(mask_base, basin, "Mask", f"{basin}_{crop}_mask.nc")
    ds = xr.open_dataset(mask_path)
    ha = ds[mask_var]
    lat_name = [d for d in ha.dims if "lat" in d.lower()][0]
    lon_name = [d for d in ha.dims if "lon" in d.lower()][0]
    lat_vals = ds[lat_name].values
    lon_vals = ds[lon_name].values
    ha_vals = ha.values
    lat_grid, lon_grid = np.meshgrid(lat_vals, lon_vals, indexing="ij")
    flat = pd.DataFrame({
        "Lat": lat_grid.ravel(),
        "Lon": lon_grid.ravel(),
        "HA": ha_vals.ravel()
    })
    valid = flat[flat["HA"] > mask_threshold].drop(columns="HA").drop_duplicates()
    return valid

def read_scenario(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"lat":"Lat","latitude":"Lat","y":"Lat",
                            "lon":"Lon","longitude":"Lon","x":"Lon"})
    df = df[(df["Year"] >= year_min) & (df["Year"] <= year_max)]

    # Force numeric for relevant columns
    for col in ["Storage","N_uptake","P_leach","N_fert","N_dep","P_fert","P_dep"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

def compute_summary(basin, crop):
    print(f"Processing {basin}-{crop}...")
    try:
        valid_pixels = read_mask(basin, crop)
    except Exception as e:
        print(f"  [WARN] Mask not found/invalid: {e}")
        return

    dfs = {key: read_scenario(path.format(basin=basin,crop=crop)) 
           for key,path in scenario_paths.items()}
    if dfs["Yp"].empty:
        print(f"  [SKIP] No Yp data for {basin}-{crop}")
        return

    yp_mean = dfs["Yp"].groupby(["Lat","Lon"])["Storage"].mean().reset_index(name="Yp_mean")
    records = []

    for scenario in ["Irrigated","Limited-Irrigated","Rainfed"]:
        df = dfs[scenario]
        if df.empty:
            continue

        df["N_input"] = df["N_fert"] + df["N_dep"]
        df["P_input"] = df["P_fert"] + df["P_dep"]
        df["P_uptake"] = df["P_leach"]

        # 🔎 Quick diagnostic BEFORE grouping
        print(f"\n--- Diagnostic for {basin}-{crop}-{scenario} ---")
        print("Head of N_uptake & P_uptake:")
        print(df[["Year","Lat","Lon","N_uptake","P_uptake"]].head(10))
        print("Non-NaN counts:")
        print(df[["N_uptake","P_uptake"]].notna().sum())
        print("-----------------------------------------------\n")

        mean_vars = df.groupby(["Lat","Lon"])[
            ["Storage","N_uptake","P_uptake","N_input","P_input"]
        ].mean().reset_index()

        merged = mean_vars.merge(yp_mean, on=["Lat","Lon"], how="inner")
        merged = merged.merge(valid_pixels, on=["Lat","Lon"], how="inner")

        merged["Category"] = np.nan
        merged.loc[merged["Storage"] > 0.8*merged["Yp_mean"], "Category"] = 1
        merged.loc[(merged["Storage"] <= 0.8*merged["Yp_mean"]) & 
                   (merged["Storage"] > 0.5*merged["Yp_mean"]), "Category"] = 2
        merged.loc[(merged["Storage"] <= 0.5*merged["Yp_mean"]) & 
                   (merged["Storage"] > 0.3*merged["Yp_mean"]), "Category"] = 3

        for cat in [1,2,3]:
            subset = merged[merged["Category"]==cat]
            if subset.empty:
                continue
            for var in ["N_uptake","N_input","P_input","P_uptake"]:
                vals = subset[var].dropna().values
                if vals.size == 0:
                    continue
                p10, p90 = np.percentile(vals,[10,90])
                records.append([scenario, cat, var, 10, p10])
                records.append([scenario, cat, var, 90, p90])

        print(f"{basin}-{crop}-{scenario} pixel counts:",
              merged["Category"].value_counts().to_dict())

    if not records:
        print(f"[NO DATA] {basin}-{crop}")
        return

    out_df = pd.DataFrame(records, columns=["Scenario","Category","Variable","Percentile","Value"])
    out_path = os.path.join(out_base, f"{basin}_{crop}_NPInput_Demand.csv")
    out_df.to_csv(out_path, index=False)
    print(f"  Saved {out_path}")

# ------------------- MAIN -------------------
if __name__ == "__main__":
    for basin in basins:
        for crop in crops:
            compute_summary(basin, crop)
