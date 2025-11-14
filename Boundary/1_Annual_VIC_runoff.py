import glob
import xarray as xr
import os

path = "/lustre/nobackup/WUR/ESG/zhou111/Data/VIC_monthly/VIC_annual_monthly/output_annual_nc"
models = ['GFDL-ESM4','IPSL-CM6A-LR','MPI-ESM1-2-HR','MRI-ESM2-0','UKESM1-0-LL']

outdir = f"/lustre/nobackup/WUR/ESG/zhou111/Data/VIC_monthly/VIC_annual_monthly/annual_runoff"
os.makedirs(outdir, exist_ok=True)

def open_and_concat(filelist):
    dsets = [xr.open_dataset(f) for f in filelist]
    return xr.concat(dsets, dim="year")

for model in models:
    print(f"Processing {model}...")

    hist_files = sorted(glob.glob(f"{path}/annual_runoff_{model}_*.nc"))
    hist_files = [f for f in hist_files if "ssp" not in f]  # keep only historical files
    ds_hist = open_and_concat(hist_files)

    ssp126_files = sorted(glob.glob(f"{path}/annual_runoff_{model}_ssp126_2015_2020*.nc"))
    ssp585_files = sorted(glob.glob(f"{path}/annual_runoff_{model}_ssp585_2015_2020*.nc"))

    if ssp126_files:
        ds_126 = open_and_concat(ssp126_files)
        ds_merge_126 = xr.concat([ds_hist, ds_126], dim="year")
        ds_merge_126 = ds_merge_126.sel(year=slice(1981, 2020))
        ds_merge_126.to_netcdf(f"{outdir}/annual_runoff_{model}_1981_2020_ssp126.nc")
        print(f"  saved annual_runoff_{model}_1981_2020_ssp126.nc")

    if ssp585_files:
        ds_585 = open_and_concat(ssp585_files)
        ds_merge_585 = xr.concat([ds_hist, ds_585], dim="year")
        ds_merge_585 = ds_merge_585.sel(year=slice(1981, 2020))
        ds_merge_585.to_netcdf(f"{outdir}/annual_runoff_{model}_1981_2020_ssp585.nc")
        print(f"  saved annual_runoff_{model}_1981_2020_ssp585.nc")

print("Done.")
