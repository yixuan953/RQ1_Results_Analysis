#  This code is used to calculate the total N input for each crop

import os
import xarray as xr
import numpy as np

fertilizer_input_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Fertilization/N_Fert_Man_Inorg_1961-2020"
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/Data/Fertilization/N_Total_Input_2015"

crop_namelist = ['Barley', 'Cassava', 'Cotton', 'Fruits', 'Groundnut', 'Maize', 'Millet', 'Oilpalm', 'Others crops', 'Potato', 'Rapeseed', 'Rice', 'Rye', 'Sorghum', 'Soybean', 'Sugarbeet', 'Sunflower', 'Sugarcane', 'Sweetpotato', 'Vegetables', 'Wheat']

for crop in crop_namelist:
    Inorg_file = os.path.join(fertilizer_input_dir, f"N_Inorg_amount_05d/N_Inorg_amount_{crop}_1961-2020.nc")
    Urea_file = os.path.join(fertilizer_input_dir, f"N_Inorg_amount_05d/N_Urea_amount_{crop}_1961-2020.nc")
    Manure_file = os.path.join(fertilizer_input_dir, f"N_Manure_amount_05d/N_manure_input_amount_{crop}_1961-2020.nc")

    if not os.path.exists(Inorg_file) or not os.path.exists(Urea_file) or not os.path.exists(Urea_file):
        print(f"Fertilizer data for {crop} is missing")
        continue

    ds_inorganic = xr.open_dataset(Inorg_file)
    Inorg_input = ds_inorganic["Inorg_N_amount"].sel(year=2015)
    ds_urea = xr.open_dataset(Urea_file)
    Urea_input = ds_urea["Urea_N_amount"].sel(year=2015)
    ds_manure = xr.open_dataset(Manure_file)
    Manure_input = ds_manure["N_manure_amount"].sel(year=2015)
    lat = ds_manure["lat"] 
    lon = ds_manure["lon"]

    crop_total_N_input = Inorg_input + Urea_input +  Manure_input   

    ds_crop_total_N_input = xr.Dataset(
    {
       "Total_N_input": (("lat", "lon"), crop_total_N_input.values),  
    },
    coords = {"lat": lat, "lon": lon}
    )
    ds_crop_total_N_input["Total_N_input"].attrs["units"] = "kg N"
    ds_crop_total_N_input["Total_N_input"].attrs["Descriptions"] = "= Chemical fertilizer + manure"
    
    output_file = os.path.join(output_dir, f"{crop}_total_N_input_2015.nc")
    ds_crop_total_N_input.to_netcdf(output_file)
    print(f"Successfully calcualted and saved total N input for {crop}")

print("Good luck for the next step!")