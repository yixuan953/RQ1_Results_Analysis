import pandas as pd
import xarray as xr
import numpy as np
import os

# study areas and crop types
studyareas = ["Indus"] # ["Indus", "Rhine", "LaPlata", "Yangtze"]
croptypes = ["Mainrice"]# ["Mainrice", "Secondrice", "Maize", "Soybean", "Wheat"]

# base paths
csv_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/S0"
range_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
out_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/S0"

for studyarea in studyareas:
    # load reference grid for this study area
    range_file = f"{range_dir}/{studyarea}/range.nc"
    if not os.path.exists(range_file):
        print(f"!!! range.nc missing for {studyarea}, skipping...")
        continue

    ref = xr.open_dataset(range_file)
    lat = ref["lat"].values
    lon = ref["lon"].values

    # precompute index maps
    lat_index = {v: i for i, v in enumerate(lat)}
    lon_index = {v: j for j, v in enumerate(lon)}

    for croptype in croptypes:
        csv_file = f"{csv_dir}/{studyarea}_{croptype}_Avg_Yp_1981-2016.csv"
        output_file = f"{out_dir}/{studyarea}_{croptype}_MaxAvg.nc"

        if not os.path.exists(csv_file):
            print(f" No CSV for {studyarea} - {croptype}, skipping...")
            continue

        print(f"Processing {studyarea} - {croptype} ...")

        # read CSV
        df = pd.read_csv(csv_file)

        # keep max Avg per pixel
        df_max = df.loc[df.groupby(["Lat", "Lon"])["Avg"].idxmax()]

        # init arrays
        shape = (len(lat), len(lon))
        sowingday_arr = np.full(shape, np.nan)
        growingdays_arr = np.full(shape, np.nan)
        tsm1_arr = np.full(shape, np.nan)
        tsm2_arr = np.full(shape, np.nan)
        avg_arr = np.full(shape, np.nan)

        # fill arrays
        for _, row in df_max.iterrows():
            i = lat_index.get(row["Lat"])
            j = lon_index.get(row["Lon"])
            if i is not None and j is not None:
                sowingday_arr[i, j] = row["SowingDay"]
                growingdays_arr[i, j] = row["GrowingDays"]
                tsm1_arr[i, j] = row["TSM1"]
                tsm2_arr[i, j] = row["TSM2"]
                avg_arr[i, j] = row["Avg"]

        # make Dataset
        ds = xr.Dataset(
            {
                "Sow_date": (("lat", "lon"), sowingday_arr),
                "Growing_length": (("lat", "lon"), growingdays_arr),
                "TSUM1": (("lat", "lon"), tsm1_arr),
                "TSUM2": (("lat", "lon"), tsm2_arr),
                "Yield": (("lat", "lon"), avg_arr),
            },
            coords={"lat": lat, "lon": lon}
        )

        # attributes
        ds.attrs["description"] = f"Best parameters for {croptype} in {studyarea} (max Avg)"
        for var in ds.data_vars:
            ds[var].attrs["_FillValue"] = 0.0

        # replace NaN with FillValue
        ds = ds.fillna(0.0)

        # save
        ds.to_netcdf(output_file)
        print(f" Saved {output_file}")
