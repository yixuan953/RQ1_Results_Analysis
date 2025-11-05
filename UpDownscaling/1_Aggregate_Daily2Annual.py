import pandas as pd
import numpy as np
import xarray as xr
from pathlib import Path

basins = ["LaPlata", "Indus", "Yangtze", "Rhine"]
crops = ["winterwheat", "maize", "mainrice", "secondrice", "soybean"]

daily_dir_tpl = Path("/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Output_Rainfed/{basin}_{crop}_daily.csv")

for basin in basins:
    for crop in crops:
        daily_fp = daily_dir_tpl.with_name(f"{basin}_{crop}_daily.csv")
        if not daily_fp.exists():
            print(f"{daily_fp} does not exist, skipping.")
            continue

        df = pd.read_csv(daily_fp)
        df['Date'] = pd.to_datetime(df['Year'].astype(str), format='%Y') + pd.to_timedelta(df['Day'] - 1, unit='D')
        df['Month'] = df['Date'].dt.month
        df['Year'] = df['Date'].dt.year

        # Compute total runoff
        df['Runoff'] = df['SurfaceRunoff'] + df['SubsurfaceRunoff']

        # Annual aggregation
        sum_cols_all = ['SurfaceRunoff', 'SubsurfaceRunoff', 'Runoff']
        annual_all = df.groupby(['Lat', 'Lon', 'Year'])[sum_cols_all].sum().reset_index()

        # Convert to xarray Dataset
        ds = annual_all.set_index(['Year', 'Lat', 'Lon']).to_xarray()

        # Assign attributes
        for var in sum_cols_all:
            ds[var].attrs['units'] = 'cm'  # or the correct unit for your runoff
            ds[var].attrs['long_name'] = var

        ds.attrs['description'] = f"Annual agricultural runoff for {crop} in {basin}"
        ds.attrs['source'] = "Model output processed from daily WOFOST simulations"
        ds.attrs['creator'] = "Yixuan Zhou"

        # Save as NetCDF
        nc_fp = f"/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/WOFOST_Runoff/Rainfed/{basin}_{crop}_runoff.nc"
        ds.to_netcdf(nc_fp)
        print(f"Saved annual NetCDF: {nc_fp}")