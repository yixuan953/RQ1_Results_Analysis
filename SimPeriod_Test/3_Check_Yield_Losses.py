import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import geopandas as gpd
from matplotlib import colors
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Define basins and crops
basins = ['LaPlata', 'Indus', 'Yangtze', 'Rhine']
all_crops = ['winterwheat', 'maize', 'mainrice', 'secondrice', 'soybean']

# Base paths
model_output_base = '/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/3_Scenarios/2_1_Baseline'
mask_base = '/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea'
shp_base = '/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_shp_StudyArea'
output_base = '/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/Warm_Up_test'
critical_NP_losses_base = "/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1"

# Create output directory
Path(output_base).mkdir(parents=True, exist_ok=True)

def load_and_process_data(basin, crop):
    """Load all necessary data for a basin-crop combination"""
    
    # Load crop model output (this defines the spatial extent)
    model_file = f"{model_output_base}/{basin}_{crop}_annual.nc"
    if not os.path.exists(model_file):
        return None
    ds = xr.open_dataset(model_file)
    
    # Get the spatial extent from model output
    model_lats = ds['lat']
    model_lons = ds['lon']
    
    # Load crop mask
    mask_file = f"{mask_base}/{basin}/Mask/{basin}_{crop}_mask.nc"
    if not os.path.exists(mask_file):
        return None
    mask_ds = xr.open_dataset(mask_file)
    
    # Select mask data to match model spatial extent
    ha_mask_da = mask_ds['HA'].sel(lat=model_lats, lon=model_lons, method='nearest')
    ha_mask = ha_mask_da.values
    
    # Apply HA > 2500 filter
    ha_mask_filtered = np.where(ha_mask > 2500, ha_mask, np.nan)
    ds_period = ds.sel(year=slice('2010', '2019'))  

    # Load critical N and P files
    n_crit_runoff_file = f"{critical_NP_losses_base}/{basin}_crit_N_runoff_kgperha.nc"
    p_crit_runoff_file = f"{critical_NP_losses_base}/{basin}_crit_P_runoff_kgperha.nc"
    
    n_crit_runoff_ds = xr.open_dataset(n_crit_runoff_file)
    p_crit_runoff_ds = xr.open_dataset(p_crit_runoff_file)
    
    #  Select critical data to match model spatial extent
    n_crit_runoff = n_crit_runoff_ds['critical_maincrop_N_runoff'].sel(lat=model_lats, lon=model_lons, method='nearest')
    n_crit_runoff_vals = n_crit_runoff.values
    p_crit_runoff = p_crit_runoff_ds['critical_maincrop_P_runoff'].sel(lat=model_lats, lon=model_lons, method='nearest')
    p_crit_runoff_vals = p_crit_runoff.values
    
    # 1. Average Yield (kg/ha/yr)
    avg_yield = ds_period['Yield'].mean(dim='year').values
    avg_yield = np.where(np.isnan(ha_mask_filtered), np.nan, avg_yield)
    
    # 2. Crop production (kton/yr) = Storage * HA / 1000
    avg_production = avg_yield * ha_mask_filtered / 1000000  # Convert kg to kton

    # 3. N runoff [kg/ha/yr]
    n_runoff = (ds_period['N_Runoff'])
    avg_n_runoff = n_runoff.mean(dim='year').values
    avg_n_runoff = np.where(np.isnan(ha_mask_filtered), np.nan, avg_n_runoff)

    # 3. P runoff [kg/ha/yr]
    p_runoff = (ds_period['P_Runoff'])
    avg_p_runoff = p_runoff.mean(dim='year').values
    avg_p_runoff = np.where(np.isnan(ha_mask_filtered), np.nan, avg_p_runoff)

    # 5. N runoff exceedance
    n_runoff_exc = n_runoff - n_crit_runoff_vals
    avg_n_runoff_exc = np.nanmean(n_runoff_exc, axis=0)
    avg_n_runoff_exc = np.nanmean(n_runoff, axis=0)
    avg_n_runoff_exc = np.where(np.isnan(ha_mask_filtered), np.nan, avg_n_runoff_exc)
    
    # 6. P runoff exceedance
    p_runoff_exc = p_runoff - p_crit_runoff_vals
    avg_p_runoff_exc = np.nanmean(p_runoff_exc, axis=0)
    avg_p_runoff_exc = np.nanmean(p_runoff, axis=0)
    avg_p_runoff_exc = np.where(np.isnan(ha_mask_filtered), np.nan, avg_p_runoff_exc)
    
    # Get coordinates
    lats = ds['lat'].values
    lons = ds['lon'].values
    
    return {
        'avg_yield': avg_yield,
        'avg_production': avg_production,
        'avg_n_runoff': avg_n_runoff,
        'avg_p_runoff': avg_p_runoff,
        'avg_n_runoff_exc': avg_n_runoff_exc,
        'avg_p_runoff_exc': avg_p_runoff_exc,
        'lats': lats,
        'lons': lons
    }

def plot_basin_crops(basin):
    """Create plots for all crops in a basin"""
    
    # Find available crops for this basin
    available_crops = []
    for crop in all_crops:
        model_file = f"{model_output_base}/{basin}_{crop}_annual.nc"
        if os.path.exists(model_file):
            available_crops.append(crop)
    
    if not available_crops:
        print(f"No crops found for basin {basin}")
        return
    
    n_crops = len(available_crops)
    
    # Load shapefiles
    basin_shp_file = f"{shp_base}/{basin}/{basin}.shp"
    river_shp_file = f"{shp_base}/{basin}/{basin}_River.shp"
    
    basin_gdf = gpd.read_file(basin_shp_file)
    river_gdf = gpd.read_file(river_shp_file)
    
    # Create figure
    fig, axes = plt.subplots(n_crops, 6, figsize=(30, 6*n_crops))
    if n_crops == 1:
        axes = axes.reshape(1, -1)
    
    fig.suptitle(f'{basin} Basin - Crop Yield and Nutrient Loss Analysis (2010 - 2019)', 
                 fontsize=20, fontweight='bold', y=0.995)
    
    titles = [
        'Avg. Yield [kg/ha/yr]',
        'Crop Production [kton/yr]',
        'N Runoff [kg/ha/yr]',
        'P Runoff [kg/ha/yr]',
        'Exceedance of N Runoff [kg/ha/yr]',
        'Exceedance of P Runoff [kg/ha/yr]',
    ]
    
    for i, crop in enumerate(available_crops):
        print(f"Processing {basin} - {crop}")
        
        # Load and process data
        data = load_and_process_data(basin, crop)
        if data is None:
            continue
        
        datasets = [
            data['avg_yield'],
            data['avg_production'],
            data['avg_n_runoff'],
            data['avg_p_runoff'],
            data['avg_n_runoff_exc'],
            data['avg_p_runoff_exc']
        ]
        
        lats = data['lats']
        lons = data['lons']
        
        for j, (dataset, title) in enumerate(zip(datasets, titles)):
            ax = axes[i, j]
            
            # Plot data
            im = ax.pcolormesh(lons, lats, dataset, shading='auto', cmap='YlOrRd')
            
            # Add basin boundary
            basin_gdf.boundary.plot(ax=ax, color='black', linewidth=1.5)
            
            # Add river
            river_gdf.plot(ax=ax, color='blue', linewidth=0.8, alpha=0.6)
            
            # Set title
            if j == 0:
                ax.set_title(f'{crop.capitalize()}\n{title}', fontsize=12, fontweight='bold')
            else:
                ax.set_title(title, fontsize=12)
            
            # Remove frame
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            
            # Add colorbar
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            
            # Set aspect ratio
            ax.set_aspect('equal', adjustable='box')
    
    plt.tight_layout()
    
    # Save figure
    output_file = f"{output_base}/{basin}_avg_Yield_ExcLoss.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

# Process all basins
for basin in basins:
    print(f"\n{'='*60}")
    print(f"Processing basin: {basin}")
    print(f"{'='*60}")
    try:
        plot_basin_crops(basin)
    except Exception as e:
        print(f"Error processing {basin}: {str(e)}")
        import traceback
        traceback.print_exc()

print("\nAll basins processed!")