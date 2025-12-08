import xarray as xr
import os
import matplotlib.pyplot as plt
import geopandas as gpd

input_dir = "/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
output_dir = "/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/Warm_Up_test" 

basins = ["Yangtze", "Indus", "LaPlata", "Rhine"]

for basin in basins:


    ds = xr.open_dataset(f"{input_dir}/{basin}/Mask/{basin}_maize_mask.nc")
    OC = ds['oc'].values
    PC_ratio = ds["PC_ratio"].values
    bulk_density = ds["bulk_density"].values # kg/dm-1
    SOC = OC * bulk_density * 3000  # convert to kg

    fig, ax = plt.subplots(1, 2, figsize=(12, 6))

    im1 = ax[0].imshow(SOC, cmap='YlGn')
    ax[0].set_title(f"SOC [tons/ha] - top 30 cm")
    fig.colorbar(im1, ax=ax[0], orientation='vertical')

    im2 = ax[1].imshow(PC_ratio, cmap='YlGn')
    ax[1].set_title(f" P to C ratio")
    fig.colorbar(im2, ax=ax[1], orientation='vertical')

    plt.suptitle(f"{basin} SOC and P to C ratio")
    plt.tight_layout()
    output_dir_path = os.path.join(output_dir, f"{basin}_SOC_PC_ratio.png") 
    plt.savefig(f"{output_dir_path}")
    