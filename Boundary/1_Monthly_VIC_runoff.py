import xarray as xr
import glob

# path pattern
path = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/VIC_baseflow/"

# all models
models = ['GFDL-ESM4','IPSL-CM6A-LR','MPI-ESM1-2-HR','MRI-ESM2-0','UKESM1-0-LL']

datasets = {}


for model in models:
    files = sorted(glob.glob(f"{path}monthly_baseflow_{model}_*.nc"))
    dsets = [xr.open_dataset(f) for f in files]
    ds = xr.concat(dsets, dim="time")                      # concatenate along time
    ds = ds.sel(time=slice("1986-01-01","2015-12-31"))     # subset time
    datasets[model] = ds

for model, ds in datasets.items():
    out = f"{path}monthly_baseflow_{model}_1986-2015.nc"
    ds.to_netcdf(out)


# add a model dimension to each dataset
datasets_expanded = []
for model, ds in datasets.items():
    datasets_expanded.append(ds.expand_dims(model=[model]))

# concatenate along model
combined = xr.concat(datasets_expanded, dim="model")

# ensemble mean across models
ensemble_mean = combined.mean(dim="model")

# save
combined.to_netcdf(f"{path}monthly_baseflow_allModels_1986-2015.nc")
ensemble_mean.to_netcdf(f"{path}monthly_baseflow_ensembleMean_1986-2015.nc")
