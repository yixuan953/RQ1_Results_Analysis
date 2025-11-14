# This code is used to calculate the critical <Cropland> N, P losses through runoff 

import xarray as xr

output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1"

# Load agricultural N, P runoff: Monthly
Agri_N_loss_nc = f"{output_dir}/Global_agri_critical_N_load.nc"
Agri_P_loss_nc = f"{output_dir}/Global_agri_critical_P_load.nc"

ds_Agri_N_loss = xr.open_dataset(Agri_N_loss_nc)
ds_Agri_P_loss = xr.open_dataset(Agri_P_loss_nc)

Agri_N_loss = ds_Agri_N_loss["critical_agri_N_load"]
Agri_P_loss = ds_Agri_P_loss["critical_agri_P_load"]

# Load cropland and grassland N, P input
Cropland_N_input_nc = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE/Output-IMAGE_GNM-SSP1_oct2020-Nitrogen_CroplandBudget-v2.nc"
ds_Crop_N_input_all = xr.open_dataset(Cropland_N_input_nc)
ds_Crop_N_input = ds_Crop_N_input_all.sel(time = "2015")
Cropland_N_input = (ds_Crop_N_input["Fertilizer"] 
                    + ds_Crop_N_input["AtmosphericDeposition"] 
                    + ds_Crop_N_input ["ManureRecycledFromConfinement"])

Grassland_N_input_nc = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE/Output-IMAGE_GNM-SSP1_oct2020-Nitrogen_PastureBudget-v2.nc"
ds_Grass_N_input_all = xr.open_dataset(Grassland_N_input_nc)
ds_Grass_N_input = ds_Grass_N_input_all.sel(time = "2015")
Grassland_N_input = ( ds_Grass_N_input["Fertilizer"]
                     + ds_Grass_N_input["AtmosphericDeposition"]
                     + ds_Grass_N_input ["Manure"])

Cropland_P_input_nc = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE/Output-IMAGE_GNM-SSP1_oct2020-Phosphate_CroplandBudget-v2.nc"
ds_Crop_P_input_all = xr.open_dataset(Cropland_P_input_nc)
ds_Crop_P_input = ds_Crop_P_input_all.sel(time = "2015")
Cropland_P_input = (ds_Crop_P_input["Fertilizer"] 
                    + ds_Crop_P_input ["ManureRecycledFromConfinement"])

Grassland_P_input_nc = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE/Output-IMAGE_GNM-SSP1_oct2020-Phosphate_PastureBudget-v2.nc"
ds_Grass_P_input_all = xr.open_dataset(Grassland_P_input_nc)
ds_Grass_P_input = ds_Grass_P_input_all.sel(time = "2015")
Grassland_P_input = (ds_Grass_P_input["Fertilizer"]
                     + ds_Grass_P_input ["Manure"])

prop_cropland_N = Cropland_N_input/(Cropland_N_input + Grassland_N_input)
prop_cropland_P = Cropland_P_input/(Cropland_P_input + Grassland_P_input)

#  Drop the time coordinate so it won't interfere with broadcasting
if "time" in prop_cropland_N.dims:
    prop_cropland_N = prop_cropland_N.squeeze("time", drop=True)
if "time" in prop_cropland_P.dims:
    prop_cropland_P = prop_cropland_P.squeeze("time", drop=True)
if "time" in prop_cropland_N.coords:
    prop_cropland_N = prop_cropland_N.drop_vars("time")
if "time" in prop_cropland_P.coords:
    prop_cropland_P = prop_cropland_P.drop_vars("time")

Cropland_N_loss = Agri_N_loss * prop_cropland_N
Cropland_P_loss = Agri_P_loss * prop_cropland_P 

Cropland_N_loss = Cropland_N_loss.rename("critical_cropland_N_load")
Cropland_P_loss = Cropland_P_loss.rename("critical_cropland_P_load")

Cropland_N_loss.to_netcdf(f"{output_dir}/Global_cropland_critical_N_load.nc")
Cropland_P_loss.to_netcdf(f"{output_dir}/Global_cropland_critical_P_load.nc")