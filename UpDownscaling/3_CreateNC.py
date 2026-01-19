import pandas as pd
import numpy as np
import xarray as xr
import os

# ---------------------------- #
# User settings
# ---------------------------- #
data_path = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_1_Baseline2"
output_dir = data_path  # save in same folder
os.makedirs(output_dir, exist_ok=True)

basins = ["LaPlata", "Indus", "Yangtze", "Rhine"] # ["LaPlata", "Indus", "Yangtze", "Rhine"]
crops = ["winterwheat", "maize", "mainrice", "secondrice", "soybean"] # ["winterwheat", "maize", "mainrice", "secondrice", "soybean"]

# ---------------------------- #
# Loop over basins and crops
# ---------------------------- #
for basin in basins:
    for crop in crops:
        csv_file = f"{data_path}/{basin}_{crop}_annual.csv"
        if not os.path.exists(csv_file):
            print(f"File not found, skipping: {csv_file}")
            continue
        
        print(f"Processing: {csv_file}")
        df = pd.read_csv(csv_file)

        # Unique coordinates and times
        lat = np.sort(df['Lat'].unique())
        lon = np.sort(df['Lon'].unique())
        time = np.sort(df['Year'].unique())

        # Variables to store
        var_names = [v for v in df.columns if v not in ['Lat','Lon','Year']]

        # Initialize empty arrays
        data_vars = {}
        for var in var_names:
            data_vars[var] = (('Year','lat','lon'), np.full((len(time), len(lat), len(lon)), np.nan))

        # Fill arrays
        for t_idx, yr in enumerate(time):
            df_year = df[df['Year']==yr]
            for j, la in enumerate(lat):
                for k, lo in enumerate(lon):
                    df_cell = df_year[(df_year['Lat']==la)&(df_year['Lon']==lo)]
                    if not df_cell.empty:
                        for var in var_names:
                            data_vars[var][1][t_idx,j,k] = df_cell[var].values[0]

        # Create xarray Dataset
        ds = xr.Dataset(
            {var: xr.DataArray(data_vars[var][1], coords={'Year':time,'lat':lat,'lon':lon}, dims=('Year','lat','lon'))
             for var in var_names},
            coords={'Year':time, 'lat':lat, 'lon':lon}
        )

        # Save NetCDF
        nc_file = f"{output_dir}/{basin}_{crop}_annual.nc"
        ds.to_netcdf(nc_file)
        print(f"Saved: {nc_file}")
