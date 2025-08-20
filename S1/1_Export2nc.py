import pandas as pd
import xarray as xr
import numpy as np
import os

# study areas and crop types
studyareas = ["Indus", "Rhine", "LaPlata", "Yangtze"]
croptypes = ["winterwheat"] # ["mainrice", "secondrice", "maize", "soybean", "wheat"]

# base paths
csv_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/S1"
range_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
out_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/S1"

for studyarea in studyareas:
    # load reference grid
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
        csv_file = f"{csv_dir}/{studyarea}_{croptype}_annual.csv"
        output_file = f"{out_dir}/{studyarea}_{croptype}_Yp.nc"

        if not os.path.exists(csv_file):
            print(f" No CSV for {studyarea} - {croptype}, skipping...")
            continue

        print(f"Processing {studyarea} - {croptype} ...")

        # read CSV
        df = pd.read_csv(csv_file)

        years = sorted(df["Year"].unique())
        year_index = {v: k for k, v in enumerate(years)}

        # init arrays (time, lat, lon)
        shape = (len(years), len(lat), len(lon))
        storage_arr = np.full(shape, np.nan)
        growthday_arr = np.full(shape, np.nan)
        nup_arr = np.full(shape, np.nan)
        pup_arr = np.full(shape, np.nan)

        # fill arrays
        for _, row in df.iterrows():
            i = lat_index.get(row["Lat"])
            j = lon_index.get(row["Lon"])
            t = year_index.get(row["Year"])
            if i is not None and j is not None and t is not None:
                storage_arr[t, i, j] = row["Storage"]
                growthday_arr[t, i, j] = row["GrowthDay"]
                nup_arr[t, i, j] = row["N_Uptake"]
                pup_arr[t, i, j] = row["P_Uptake"]

        # make Dataset
        ds = xr.Dataset(
            {
                "Yp": (("year", "lat", "lon"), storage_arr),
                "GrowthDay": (("year", "lat", "lon"), growthday_arr),
                "N_Uptake": (("year", "lat", "lon"), nup_arr),
                "P_Uptake": (("year", "lat", "lon"), pup_arr),
            },
            coords={"year": years, "lat": lat, "lon": lon}
        )

        # attributes
        ds.attrs["description"] = f"Annual N, P uptakes and yield for {croptype} in {studyarea}"
        for var in ds.data_vars:
            ds[var].attrs["_FillValue"] = -9999.0

        # replace NaN with FillValue
        ds = ds.fillna(-9999.0)

        # save
        ds.to_netcdf(output_file)
        print(f" Saved {output_file}")
