#  This code is used to calculate the critical N, P loss (kg N) for cropland and grassland

import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import os
import numpy as np 

pasture_N_file = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE/Output-IMAGE_GNM-SSP5_oct2020-Nitrogen_PastureBudget-v2.nc"
cropland_N_file = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE/Output-IMAGE_GNM-SSP5_oct2020-Nitrogen_CroplandBudget-v2.nc"
agricul_N_file = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/Global_crit_N_conc_load_agri.nc"

pasture_P_file = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE/Output-IMAGE_GNM-SSP5_oct2020-Phosphate_PastureBudget-v2.nc"
cropland_P_file = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/IMAGE/Output-IMAGE_GNM-SSP1_oct2020-Phosphate_CroplandBudget-v2.nc"
agricul_P_file = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/Global_crit_P_conc_load_agri.nc"

output_dir = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3"

# Calculate the critical N loss for cropland
ds_agri_N = xr.open_dataset(agricul_N_file)
lat = ds_agri_N["lat"].values
lon = ds_agri_N["lon"].values
Crit_N_load_agri = ds_agri_N["Crit_N_load_agri"] 

ds_pasture_input = xr.open_dataset(pasture_N_file)
Fert_input_pasture = ds_pasture_input["Fertilizer"].sel(time = "2015-05-01")
Manure_input_pasture = ds_pasture_input["ManureRecycledFromConfinement"].sel(time = "2015-05-01")
pasture_input = Fert_input_pasture + Manure_input_pasture

ds_cropland_input = xr.open_dataset(cropland_N_file)
Fert_input_cropland = ds_cropland_input["Fertilizer"].sel(time = "2015-05-01")
Manure_input_cropland = ds_cropland_input["ManureRecycledFromConfinement"].sel(time = "2015-05-01")
cropland_input = Fert_input_cropland + Manure_input_cropland

total_input = pasture_input + cropland_input
crit_N_cropland = xr.where(total_input>0, Crit_N_load_agri*cropland_input/total_input, Crit_N_load_agri)

ds_crit_N_cropland = xr.Dataset(
    {
       "Crit_N_cropland": (("lat", "lon"), crit_N_cropland.values),  
    },
    coords = {"lat": lat, "lon": lon}
)
ds_crit_N_cropland["Crit_N_cropland"].attrs["units"] = "kg N"
output_file = os.path.join(output_dir, f"Global_crit_N_runoff_cropland.nc")
ds_crit_N_cropland.to_netcdf(output_file)
print(f"Computed and saved {output_file}")

# Calculate the critical P loss for cropland
ds_agri_P = xr.open_dataset(agricul_P_file)
Crit_P_load_agri = ds_agri_P["Crit_P_load_agri"] 

ds_pasture_input = xr.open_dataset(pasture_P_file)
Fert_input_pasture = ds_pasture_input["Fertilizer"].sel(time = "2015-05-01")
Manure_input_pasture = ds_pasture_input["Manure"].sel(time ="2015-05-01")
pasture_input = Fert_input_pasture + Manure_input_pasture

ds_cropland_input = xr.open_dataset(cropland_P_file)
Fert_input_cropland = ds_cropland_input["Fertilizer"].sel(time = "2015-05-01")
Manure_input_cropland = ds_cropland_input["ManureRecycledFromConfinement"].sel(time = "2015-05-01")
cropland_input = Fert_input_cropland + Manure_input_cropland

total_input = pasture_input + cropland_input
crit_P_cropland = xr.where(total_input>0, Crit_P_load_agri*cropland_input/total_input, Crit_P_load_agri)

ds_crit_P_cropland = xr.Dataset(
    {
       "Crit_P_cropland": (("lat", "lon"), crit_P_cropland.values),  
    },
    coords = {"lat": lat, "lon": lon}
)
ds_crit_P_cropland["Crit_P_cropland"].attrs["units"] = "kg P"
output_file = os.path.join(output_dir, f"Global_crit_P_runoff_cropland.nc")
ds_crit_P_cropland.to_netcdf(output_file)
print(f"Computed and saved {output_file}")

# =============== Plotting starts (optional) ================
fig = plt.figure(figsize=(20, 10))
projection = ccrs.PlateCarree()

# Define plot data with custom vmin/vmax for load (using previous load ranges)
plot_data = [
    (ds_crit_N_cropland["Crit_N_cropland"], 
     "Critical N Runoff Loss (Cropland)", 
     ds_crit_N_cropland["Crit_N_cropland"].attrs.get("units", "kg N"), 121, 
     0, 5000000),     
    
    (ds_crit_P_cropland["Crit_P_cropland"], 
     "Critical P Runoff Loss (Cropland)", 
     ds_crit_P_cropland["Crit_P_cropland"].attrs.get("units", "kg P"), 122, 
     0, 200000)        
]

# --- 4. Loop Through and Create Each Subplot ---
for data_array, title, cbar_label, pos, vmin_val, vmax_val in plot_data:
    ax = fig.add_subplot(pos, projection=projection)
    
    ax.set_global() 
    
    p = data_array.plot.pcolormesh(
        ax=ax, 
        transform=projection,
        vmin=vmin_val,         
        vmax=vmax_val,         
        cbar_kwargs={
            'label': cbar_label,
            'orientation': 'vertical',
            'shrink': 0.8 
        },
        cmap='Spectral_r', 
        extend='both' 
    )
    
    # Add map features for context
    ax.coastlines(resolution='50m', color='black', linewidth=0.8)
    
    # Add gridlines
    gl = ax.gridlines(crs=projection, draw_labels=True, linewidth=1, 
                      color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False 
    gl.right_labels = False 

    # Set the title
    ax.set_title(title, fontsize=14)

# Adjust the layout
fig.suptitle("Global Critical N and P Runoff Losses from Cropland", fontsize=18, y=0.98)
plt.tight_layout(rect=[0, 0.03, 1, 0.95]) 

# --- 5. Save and Show the Figure ---
output_plot_file = os.path.join(output_dir, "Global_Cropland_Crit_NP_Runoff_Maps.png")
plt.savefig(output_plot_file, dpi=300, bbox_inches='tight')
print(f"\nSuccessfully generated and saved map to: {output_plot_file}")

print(f"Good luck for the next step!")