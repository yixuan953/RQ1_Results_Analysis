# This script is used to get the mask of areas where annual runoff < 3 mm

import xarray as xr
import numpy as np
import os

VIC_runoff_file = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/VIC_runoff/annual_runoff_mean_ssp585_inverted.nc"
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
Basins = ["Indus", "Rhine", "LaPlata", "Yangtze"]

# Load the runoff data
ds_runoff = xr.open_dataset(VIC_runoff_file)
runoff_raw = ds_runoff["OUT_RUNOFF"].sel(year="2014").squeeze(drop=True)

for basin in Basins:
    range_dir = os.path.join(output_dir, basin, "range.nc")
    ds_range = xr.open_dataset(range_dir)
    
    if 'latitude' in ds_range.coords:
        ds_range = ds_range.rename({'latitude': 'lat', 'longitude': 'lon'})
    
    mask = ds_range["mask"].squeeze()

    # Instead of interp_like, we reindex. 
    # This forces the global runoff to match the basin's grid exactly.
    # method="nearest" handles tiny floating point differences in coordinates.
    runoff_aligned = runoff_raw.reindex_like(mask, method="nearest")

    # Now that they share the exact same coordinates, 
    # we can use a simple logical filter.
    result = xr.DataArray(
        np.where((runoff_aligned < 3) & (mask == 1), 1, np.nan),
        coords=mask.coords,
        dims=mask.dims
    )

    ds_output = result.to_dataset(name="Low_Runoff")
    output_path = os.path.join(output_dir, basin, f"low_runoff_mask.nc")
    ds_output.to_netcdf(output_path)
    
    print(f"Processed {basin} successfully.")