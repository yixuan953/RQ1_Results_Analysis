import pandas as pd
import os
import numpy as np

def downscale_basin_crop(basin, crop, annual_dir, monthly_dir):

    # File paths
    annual_file = os.path.join(annual_dir, f"{basin}_{crop}_annual.csv")
    monthly_file = os.path.join(monthly_dir, f"{basin}_{crop}_monthly.csv")

    # Load CSVs
    annual_df = pd.read_csv(annual_file)
    annual_df.columns = annual_df.columns.str.strip()
    monthly_df = pd.read_csv(monthly_file)

    # Initialize downscaled columns
    for col in ["NH3_ds", "N2O_ds", "NOx_ds", "N_surf_ds", "N_sub_ds", "N_leach_ds"]:
        monthly_df[col] = 0.0

    # Helper functions
    def safe_sum(df, col):
        return df[col].sum() if col in df.columns else 0.0

    def distribute(total, weights):
        s = weights.sum()
        return (total * weights / s) if s > 0 else np.zeros_like(weights)

    # Loop over each grid cell and year
    for (lat, lon, year), ann_grp in annual_df.groupby(["Lat", "Lon", "Year"]):
        # Annual totals
        NH3_yr    = safe_sum(ann_grp, "NH3")
        N2O_yr    = safe_sum(ann_grp, "N2O")
        NOx_yr    = safe_sum(ann_grp, "NOx")
        Nsurf_yr  = safe_sum(ann_grp, "N_surf")
        Nsub_yr   = safe_sum(ann_grp, "N_sub")
        Nleach_yr = safe_sum(ann_grp, "N_leach")

        # Select monthly rows for this cell/year
        mask = (monthly_df["Lat"] == lat) & (monthly_df["Lon"] == lon) & (monthly_df["Year"] == year)
        mon_grp = monthly_df.loc[mask].copy()
        if mon_grp.empty:
            continue

        # Compute weights
        w_fert  = mon_grp["Days_Fertilization"].fillna(0).values
        w_surf  = (mon_grp["SurfaceRunoff"].fillna(0) * mon_grp["Days_Fertilization"].fillna(0)).values
        w_sub   = (mon_grp["SubsurfaceRunoff"].fillna(0) * mon_grp["Days_Fertilization"].fillna(0)).values
        w_leach = mon_grp["Percolation"].fillna(0).values

        # Distribute annual totals to monthly
        monthly_df.loc[mask, "NH3_ds"]    = distribute(NH3_yr, w_fert)
        monthly_df.loc[mask, "N2O_ds"]    = distribute(N2O_yr, w_fert)
        monthly_df.loc[mask, "NOx_ds"]    = distribute(NOx_yr, w_fert)
        monthly_df.loc[mask, "N_surf_ds"] = distribute(Nsurf_yr, w_surf)
        monthly_df.loc[mask, "N_sub_ds"]  = distribute(Nsub_yr, w_sub)
        monthly_df.loc[mask, "N_leach_ds"]= distribute(Nleach_yr, w_leach)

    # Save updated monthly CSV
    monthly_df.to_csv(monthly_file, index=False)
    print(f"✅ Updated {monthly_file}")

# Example usage
basins = ["LaPlata", "Indus", "Yangtze", "Rhine"]
crops = ["winterwheat", "maize", "mainrice", "secondrice", "soybean"]

annual_dir="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Output_Rainfed"

for basin in basins:
    for crop in crops:
        annual_fp = os.path.join(annual_dir, f"{basin}_{crop}_annual.csv")
        if not os.path.exists(annual_fp):
            print(f"{annual_fp} does not exist, skipping.")
            continue
        
        downscale_basin_crop(basin, crop, annual_dir, annual_dir)