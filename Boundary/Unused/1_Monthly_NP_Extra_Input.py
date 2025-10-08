import os
import glob
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from tqdm import tqdm

# ---------------- USER CONFIG ----------------
ROOT_CSV = Path('/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs')
ROOT_MASK = Path('/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea')
ROOT_SHP = Path('/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_shp_StudyArea')
OUT_ROOT = Path('/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/3_Required_Extra_Input')
OUT_ROOT.mkdir(parents=True, exist_ok=True)

scenarios = ['Yp-Irrigated', 'Yp-Limited-Irrigation', 'Yp-Rainfed']
basins = ['LaPlata', 'Indus', 'Yangtze', 'Rhine']
crops = ['winterwheat', 'maize', 'mainrice', 'secondrice', 'soybean']

# years to average
YEAR_START = 1986
YEAR_END = 2015
YEARS = list(range(YEAR_START, YEAR_END + 1))

# mask threshold
HA_THRESHOLD = 2500

# variable names expected in CSVs
VARS = ['Lat','Lon','Year','Month','SurfaceRunoff','SubsurfaceRunoff','Percolation',
        'Days_Fertilization','N_uptake','P_uptake','N_deficit','P_deficit','N_decomp','P_decomp',
        'P_Surf','P_Sub','P_Leaching','NH3_ds','N2O_ds','NOx_ds','N_surf_ds','N_sub_ds','N_leach_ds']

# ---------------- helper functions ----------------

def find_mask_variable(ds):
    # Return the variable name in mask that looks like HA or 'HA'
    for v in ds.data_vars:
        if 'HA' in v or 'ha' in v or 'area' in v.lower():
            return v
    # fallback: first data var
    return list(ds.data_vars)[0]


def load_mask(basin, crop):
    """Load crop mask NetCDF and return boolean mask where HA>threshold, plus lat/lon arrays."""
    mask_path = ROOT_MASK / basin / 'Mask' / f"{basin}_{crop}_mask.nc"
    if not mask_path.exists():
        raise FileNotFoundError(f"Mask not found: {mask_path}")
    ds = xr.open_dataset(mask_path)
    var = find_mask_variable(ds)
    ha = ds[var]
    # try to find lat/lon dims/coords
    if 'lat' in ha.coords:
        lat = ha['lat'].values
        lon = ha['lon'].values
    elif 'y' in ha.coords and 'x' in ha.coords:
        lat = ha['y'].values
        lon = ha['x'].values
    else:
        # fallback to dimensions
        coords = {c: ha.coords[c].values for c in ha.coords}
        lat = coords.get('lat') or coords.get('latitude') or coords.get('y')
        lon = coords.get('lon') or coords.get('longitude') or coords.get('x')
    mask = (ha.values > HA_THRESHOLD)
    return mask, lat, lon


def read_csv_files_for(basin, crop, scenario):
    """Read all monthly CSV files for this triple. Returns a DataFrame filtered for years.
       Assumes files are in: ROOT_CSV/{scenario}/{basin}_{crop}_monthly.csv
       If file not exists, raise.
    """
    csv_path = ROOT_CSV / scenario / f"{basin}_{crop}_monthly.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    # read CSV
    df = pd.read_csv(csv_path)
    # keep only desired years
    df = df[df['Year'].isin(YEARS)].copy()
    # ensure necessary columns
    for v in ['N_uptake','P_uptake','N_decomp','P_decomp','N_deficit','P_deficit']:
        if v not in df.columns:
            df[v] = np.nan
    return df


def aggregate_pixel_monthly(df):
    """Compute monthly average per pixel (lat,lon,month) across years in df."""
    # compute extra demands
    df['N_extra_input_demand'] = df['N_uptake'] - df['N_decomp']
    df['P_extra_input_demand'] = df['P_uptake'] - df['P_decomp']
    # group by lat lon month
    grouped = df.groupby(['Lat','Lon','Month'])
    agg = grouped.agg({
        'N_uptake':'mean', 'N_decomp':'mean', 'P_uptake':'mean', 'P_decomp':'mean',
        'N_deficit':'mean', 'P_deficit':'mean', 'N_extra_input_demand':'mean', 'P_extra_input_demand':'mean'
    }).reset_index()
    return agg


def pivot_to_grid(agg, lat_vals, lon_vals, varname):
    """Pivot aggregated point data to 2D grid for plotting. lat_vals and lon_vals should be 1D arrays.
       Returns grid (ny, nx) with np.nan where missing.
    """
    lat_sorted = np.sort(lat_vals)
    lon_sorted = np.sort(lon_vals)
    # create mesh
    Lon, Lat = np.meshgrid(lon_sorted, lat_sorted)
    # prepare points
    points = agg[['Lon','Lat']].values
    values = agg[varname].values
    # griddata interpolation (nearest) to fill grid points
    grid = griddata(points, values, (Lon, Lat), method='nearest')
    return lat_sorted, lon_sorted, grid


def plot_monthly_maps(lat_grid, lon_grid, grids_by_month, basin_shp, title_prefix, outpath):
    """plots 12-panel monthly maps given a dict month->2D grid (ny,nx)"""
    fig, axes = plt.subplots(3,4, figsize=(20,12), constrained_layout=True)
    axes = axes.flatten()
    vmin = np.nanpercentile(np.concatenate([g.flatten() for g in grids_by_month.values() if g is not None]), 2)
    vmax = np.nanpercentile(np.concatenate([g.flatten() for g in grids_by_month.values() if g is not None]), 98)
    for m in range(1,13):
        ax = axes[m-1]
        grid = grids_by_month.get(m)
        if grid is None:
            ax.set_title(f'Month {m} (no data)')
            ax.axis('off')
            continue
        pcm = ax.pcolormesh(lon_grid, lat_grid, grid, shading='auto', vmin=vmin, vmax=vmax)
        ax.set_title(f'{title_prefix} - Month {m}')
        ax.set_xlabel('Lon')
        ax.set_ylabel('Lat')
        # overlay shapefile
        try:
            basin_shp.boundary.plot(ax=ax, linewidth=1)
        except Exception:
            pass
    fig.colorbar(pcm, ax=axes.tolist(), orientation='vertical', fraction=0.02)
    fig.suptitle(title_prefix)
    fig.savefig(outpath, dpi=200)
    plt.close(fig)


def plot_basin_monthly_series(monthly_median_df, title, outpath):
    """monthly_median_df: DataFrame indexed by Month (1..12) with columns to plot"""
    fig, axes = plt.subplots(1,2, figsize=(14,5), constrained_layout=True)
    # Left: N variables
    ax = axes[0]
    ax.plot(monthly_median_df.index, monthly_median_df['N_uptake'], marker='o', label='Crop N demand from the soil')
    ax.plot(monthly_median_df.index, monthly_median_df['N_decomp'], marker='o', label='N_decomp')
    ax.plot(monthly_median_df.index, monthly_median_df['N_deficit'], marker='o', label='N_deficit')
    ax.plot(monthly_median_df.index, monthly_median_df['N_extra_input_demand'], marker='o', label='N_extra_input_demand')
    ax.set_xlabel('Month')
    ax.set_ylabel('Median across HA>2500 pixels')
    ax.set_title('Nitrogen monthly (median)')
    ax.legend()
    # Right: P variables
    ax = axes[1]
    ax.plot(monthly_median_df.index, monthly_median_df['P_uptake'], marker='o', label='Crop P demand from the soil')
    ax.plot(monthly_median_df.index, monthly_median_df['P_decomp'], marker='o', label='P_decomp')
    ax.plot(monthly_median_df.index, monthly_median_df['P_deficit'], marker='o', label='P_deficit')
    ax.plot(monthly_median_df.index, monthly_median_df['P_extra_input_demand'], marker='o', label='P_extra_input_demand')
    ax.set_xlabel('Month')
    ax.set_ylabel('Median across HA>2500 pixels')
    ax.set_title('Phosphorus monthly (median)')
    ax.legend()
    fig.suptitle(title)
    fig.savefig(outpath, dpi=200)
    plt.close(fig)

# ---------------- main processing ----------------

for scenario in scenarios:
    scenario_dir = ROOT_CSV / scenario
    if not scenario_dir.exists():
        print(f"Scenario folder missing: {scenario_dir}, skipping")
        continue
    for basin in basins:
        # load basin shapefile for overlay
        shp_path = ROOT_SHP / basin / f"{basin}.shp"
        basin_shp = None
        if shp_path.exists():
            try:
                basin_shp = gpd.read_file(shp_path)
            except Exception as e:
                print(f"Warning: could not read shapefile {shp_path}: {e}")
        for crop in crops:
            try:
                df = read_csv_files_for(basin, crop, scenario)
            except FileNotFoundError:
                # skip missing crop in basin
                print(f"Missing CSV for {basin} {crop} {scenario}, skipping.")
                continue
            if df.empty:
                print(f"No data for years {YEAR_START}-{YEAR_END} in {basin} {crop} {scenario}")
                continue
            # compute aggregates
            agg = aggregate_pixel_monthly(df)
            # load mask
            try:
                mask, mask_lat, mask_lon = load_mask(basin, crop)
            except Exception as e:
                print(f"Could not load mask for {basin} {crop}: {e}")
                continue
            # create a fast lookup set of valid (lat,lon) where mask True
            # The mask may be 2D: (lat,lon). We need to map coords to values.
            # We assume mask_lat, mask_lon are 1D arrays matching mask dims (ny,nx)
            try:
                lat_vals = np.sort(mask_lat)
                lon_vals = np.sort(mask_lon)
                Lon, Lat = np.meshgrid(lon_vals, lat_vals)
                mask_flat = mask.flatten()
                points_mask = np.column_stack([Lon.flatten(), Lat.flatten()])
                valid_points = set(map(tuple, points_mask[mask_flat==True]))
            except Exception:
                valid_points = set()

            # apply mask: keep only agg rows with (Lon,Lat) in valid_points
            def is_valid_row(row):
                return (row['Lon'], row['Lat']) in valid_points
            if valid_points:
                agg['valid'] = agg.apply(is_valid_row, axis=1)
                agg_valid = agg[agg['valid']].copy()
            else:
                # no valid points found from mask - fallback to using HA threshold on agg lat/lon via grid interpolation
                agg_valid = agg.copy()

            # --- Spatial monthly maps for N_extra_input_demand and P_extra_input_demand ---
            # For each month, pivot to grid
            grids_N = {}
            grids_P = {}
            for m in range(1,13):
                sub = agg_valid[agg_valid['Month']==m]
                if sub.empty:
                    grids_N[m] = None
                    grids_P[m] = None
                    continue
                try:
                    lat_grid, lon_grid, gridN = pivot_to_grid(sub, mask_lat, mask_lon, 'N_extra_input_demand')
                    _, _, gridP = pivot_to_grid(sub, mask_lat, mask_lon, 'P_extra_input_demand')
                except Exception:
                    # fallback: produce scatter-filled grid by nearest
                    points = sub[['Lon','Lat']].values
                    valuesN = sub['N_extra_input_demand'].values
                    valuesP = sub['P_extra_input_demand'].values
                    Lon2, Lat2 = np.meshgrid(np.sort(mask_lon), np.sort(mask_lat))
                    gridN = griddata(points, valuesN, (Lon2, Lat2), method='nearest')
                    gridP = griddata(points, valuesP, (Lon2, Lat2), method='nearest')
                    lat_grid = np.sort(mask_lat)
                    lon_grid = np.sort(mask_lon)
                grids_N[m] = gridN
                grids_P[m] = gridP

            # Save maps
            out_map_N = OUT_ROOT / f"{basin}_{crop}_N_DemandMap_{scenario}.png"
            out_map_P = OUT_ROOT / f"{basin}_{crop}_P_DemandMap_{scenario}.png"
            titleN = f"{basin} {crop} N_extra_input_demand ({scenario})"
            titleP = f"{basin} {crop} P_extra_input_demand ({scenario})"
            plot_monthly_maps(lat_grid, lon_grid, grids_N, basin_shp, titleN, out_map_N)
            plot_monthly_maps(lat_grid, lon_grid, grids_P, basin_shp, titleP, out_map_P)
            print(f"Saved maps: {out_map_N} , {out_map_P}")

            # --- Basin median monthly series for pixels where HA>threshold ---
            # We compute per-pixel monthly means already in agg_valid. Now compute median across pixels per month
            # ensure needed columns
            cols_needed = ['N_uptake','N_decomp','N_deficit','N_extra_input_demand',
                           'P_uptake','P_decomp','P_deficit','P_extra_input_demand']
            monthly_medians = agg_valid.groupby('Month')[cols_needed].median()
            # ensure months 1..12 present
            for m in range(1,13):
                if m not in monthly_medians.index:
                    monthly_medians.loc[m] = np.nan
            monthly_medians = monthly_medians.sort_index()

            out_series_N = OUT_ROOT / f"{basin}_{crop}_N_Demand_monthly_{scenario}.png"
            out_series_P = OUT_ROOT / f"{basin}_{crop}_P_Demand_monthly_{scenario}.png"
            # Both N and P in one figure per user's description (two subplots)
            title_series = f"{basin} {crop} monthly medians ({scenario})"
            plot_basin_monthly_series(monthly_medians, title_series, OUT_ROOT / f"{basin}_{crop}_Demand_monthly_{scenario}.png")
            print(f"Saved monthly median figure: {OUT_ROOT / f'{basin}_{crop}_Demand_monthly_{scenario}.png'}")

print('Processing completed.')
