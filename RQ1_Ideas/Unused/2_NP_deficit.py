import os
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import calendar
from matplotlib import gridspec

warnings.simplefilter(action='ignore', category=FutureWarning)

basins = ['LaPlata','Indus','Yangtze','Rhine'] # ['LaPlata','Indus','Yangtze','Rhine']
crops = ['maize'] # ['wheat','maize','rice','soybean']

root_yp = Path('/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Yp')
root_wn = Path('/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Water-Nutrient-Limited')
mask_root = Path('/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea')
shp_root = Path('/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_shp_StudyArea')
out_root = Path('/lustre/nobackup/WUR/ESG/zhou111/4_RQ1_Analysis_Results/RQ1_Ideas/Figure2')

out_root.mkdir(parents=True, exist_ok=True)
HA_NAME = 'HA'

def load_mask_ha(basin, crop):
    mask_path = mask_root / basin / 'Mask' / f"{basin}_{crop}_mask.nc"
    ds = xr.open_dataset(mask_path)
    return ds[HA_NAME]

def read_monthly_csv(path):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    return df


def make_monthly_maps(basin, crop, ha_da, vals_df, varname, unit='kg/ha', cmap='GnBu', out_file=None):
    df = vals_df[(vals_df['Year']>=1986)&(vals_df['Year']<=2015)].copy()
    
    # Determine valid months based on demand
    valid_months = []
    for m in range(1,13):
        sub = df[df['Month']==m]
        if sub.empty:
            continue
        demand_col = 'N_demand' if 'N_demand' in sub.columns else ('P_demand' if 'P_demand' in sub.columns else None)
        if demand_col and sub[demand_col].replace(np.nan,0).sum()>0:
            valid_months.append(m)
    if not valid_months:
        print(f"No valid months for {basin} {crop} {varname}")
        return

    # Average over years for each pixel and month
    grouped = df.groupby(['Lat','Lon','Month'])[varname].mean().reset_index()
    grouped['Lat'] = grouped['Lat'].round(4)
    grouped['Lon'] = grouped['Lon'].round(4)

    mask_lats = np.round(ha_da['lat'].values,4) if 'lat' in ha_da.coords else np.round(ha_da['latitude'].values,4)
    mask_lons = np.round(ha_da['lon'].values,4) if 'lon' in ha_da.coords else np.round(ha_da['longitude'].values,4)
    ha_vals = ha_da.values
    mesh_lons, mesh_lats = np.meshgrid(mask_lons, mask_lats)
    ha_df = pd.DataFrame({'Lat':mesh_lats.ravel(), 'Lon':mesh_lons.ravel(), 'HA':ha_vals.ravel()})
    ha_df = ha_df[ha_df['HA']>2500]

    merged = pd.merge(grouped, ha_df, on=['Lat','Lon'], how='inner')
    if merged.empty:
        print(f"No pixels with HA>2500 for {basin} {crop} {varname}")
        return

    # Compute vmax as 90th percentile of all valid values for this basin × crop × var
    vmax = merged[varname].quantile(0.9)
    vmin = 0

    lats = np.sort(merged['Lat'].unique())
    lons = np.sort(merged['Lon'].unique())
    grid = {}
    for m in valid_months:
        sub = merged[merged['Month']==m]
        pivot = sub.pivot_table(index='Lat', columns='Lon', values=varname, aggfunc='mean')
        pivot = pivot.reindex(index=lats, columns=lons)
        grid[m] = pivot.values
        grid[m] = np.clip(grid[m], 0, vmax)

    shp_path = shp_root / basin / f"{basin}.shp"
    basin_poly = gpd.read_file(shp_path) if shp_path.exists() else None

    n_rows, n_cols = 4, 3
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12,12))
    axes = axes.flatten()
    month_labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

    for i, ax in enumerate(axes):
        ax.axis('off')
        if i<len(valid_months):
            m = valid_months[i]
            X, Y = np.meshgrid(lons, lats)
            pcm = ax.pcolormesh(X, Y, grid[m], vmin=vmin, vmax=vmax, shading='auto', cmap=cmap)
            if basin_poly is not None:
                basin_poly.boundary.plot(ax=ax, color='black', linewidth=1)
            ax.set_title(month_labels[m-1], fontsize=10)

    # Colorbar at top-left
    cax = fig.add_axes([0.02, 0.4, 0.03, 0.3])
    fig.colorbar(pcm, cax=cax, label=unit)

    fig.suptitle(f"Monthly deficit for {crop} in {basin} river basin - Yp", fontsize=14, y=0.95)

    if out_file:
        fig.savefig(out_file, dpi=300, bbox_inches='tight')
        print(f"Saved map to {out_file}")
    plt.close(fig)


def make_split_violin(
    basin, crop, yp_df, wn_df, ha_da, varname, valid_months, out_file=None,
    palette={'Yp':"#a2d0f0",'WN':"#e1bd9d"}, ylims=None):
    import calendar

    # Round coordinates for merging
    ha_lats = np.round(ha_da['lat'].values,4) if 'lat' in ha_da.coords else np.round(ha_da['latitude'].values,4)
    ha_lons = np.round(ha_da['lon'].values,4) if 'lon' in ha_da.coords else np.round(ha_da['longitude'].values,4)
    ha_vals = ha_da.values
    mesh_lons, mesh_lats = np.meshgrid(ha_lons, ha_lats)
    ha_df = pd.DataFrame({'Lat': mesh_lats.ravel(), 'Lon': mesh_lons.ravel(), 'HA': ha_vals.ravel()})
    
    # Only use pixels where HA < 2500
    ha_df = ha_df[ha_df['HA'] < 2500]

    # Compute average per pixel per month
    yp_avg = yp_df[(yp_df['Year']>=1996)&(yp_df['Year']<=2015)].groupby(['Lat','Lon','Month'])[varname].mean().reset_index()
    wn_avg = wn_df[(wn_df['Year']>=1996)&(wn_df['Year']<=2015)].groupby(['Lat','Lon','Month'])[varname].mean().reset_index()

    # Keep only pixels with HA < 2500
    yp_avg = pd.merge(yp_avg, ha_df[['Lat','Lon']], on=['Lat','Lon'])
    wn_avg = pd.merge(wn_avg, ha_df[['Lat','Lon']], on=['Lat','Lon'])

    # Only keep valid months
    yp_avg = yp_avg[yp_avg['Month'].isin(valid_months)]
    wn_avg = wn_avg[wn_avg['Month'].isin(valid_months)]

    # Prepare long-format for seaborn
    yp_avg = yp_avg[['Month', varname]].rename(columns={varname:'value'}); yp_avg['type']='Yp'
    wn_avg = wn_avg[['Month', varname]].rename(columns={varname:'value'}); wn_avg['type']='WN'
    combined = pd.concat([yp_avg, wn_avg], ignore_index=True).dropna(subset=['value'])
    combined = combined[combined['value']>0]

    if combined.empty:
        print(f"No uptake data for {basin} {crop} {varname} with HA<2500")
        return

    # Clip to 10–90 percentile
    q_low, q_high = combined['value'].quantile([0.1, 0.9])
    combined = combined[(combined['value'] >= q_low) & (combined['value'] <= q_high)]

    # Dynamic y-axis if ylims not provided
    if ylims is None:
        ymin, ymax = combined['value'].min(), combined['value'].max()
        margin = 0.05 * (ymax - ymin)
        ylims = (ymin - margin, ymax + margin)

    # Violin plot
    plt.figure(figsize=(12,6))
    sns.violinplot(
        data=combined,
        x='Month',
        y='value',
        hue='type',
        split=True,
        inner='quartile',
        palette=palette,
        cut=0
    )
    plt.ylim(ylims)
    plt.xlabel('Month'); plt.ylabel(varname)
    plt.legend(title='Type')
    plt.xticks(ticks=range(len(valid_months)), labels=[calendar.month_abbr[m] for m in valid_months])

    if out_file:
        plt.savefig(out_file, dpi=300, bbox_inches='tight')
        print(f"Saved violin to {out_file}")
    plt.close()

def make_monthly_lines_with_percentiles(
    basin, crop, yp_df, wn_df, ha_da, varname, valid_months, out_file=None,
    colors={'Yp':"#8dc2e8",'WN':"#dea676"}):
    import calendar

    # Round coordinates for merging
    ha_lats = np.round(ha_da['lat'].values,4) if 'lat' in ha_da.coords else np.round(ha_da['latitude'].values,4)
    ha_lons = np.round(ha_da['lon'].values,4) if 'lon' in ha_da.coords else np.round(ha_da['longitude'].values,4)
    ha_vals = ha_da.values
    mesh_lons, mesh_lats = np.meshgrid(ha_lons, ha_lats)
    ha_df = pd.DataFrame({'Lat': mesh_lats.ravel(), 'Lon': mesh_lons.ravel(), 'HA': ha_vals.ravel()})
    
    # Only use pixels where HA < 2500
    ha_df = ha_df[ha_df['HA'] < 2500]

    # Compute average per pixel per month
    yp_avg = yp_df[(yp_df['Year']>=1996)&(yp_df['Year']<=2015)].groupby(['Lat','Lon','Month'])[varname].mean().reset_index()
    wn_avg = wn_df[(wn_df['Year']>=1996)&(wn_df['Year']<=2015)].groupby(['Lat','Lon','Month'])[varname].mean().reset_index()

    # Keep only pixels with HA < 2500
    yp_avg = pd.merge(yp_avg, ha_df[['Lat','Lon']], on=['Lat','Lon'])
    wn_avg = pd.merge(wn_avg, ha_df[['Lat','Lon']], on=['Lat','Lon'])

    # Only keep valid months
    yp_avg = yp_avg[yp_avg['Month'].isin(valid_months)]
    wn_avg = wn_avg[wn_avg['Month'].isin(valid_months)]

    if yp_avg.empty and wn_avg.empty:
        print(f"No uptake data for {basin} {crop} {varname} with HA<2500")
        return

    # Compute median and 10-90 percentile per month
    def summary_stats(df):
        stats = df.groupby('Month')[varname].agg([('median','median'),
                                                  ('q10', lambda x: np.percentile(x,10)),
                                                  ('q90', lambda x: np.percentile(x,90))]).reset_index()
        return stats

    yp_stats = summary_stats(yp_avg)
    wn_stats = summary_stats(wn_avg)

    # Plot
    plt.figure(figsize=(12,6))
    for stats, label in zip([yp_stats, wn_stats], ['Yp','WN']):
        plt.plot(stats['Month'], stats['median'], color=colors[label], label=label)
        plt.fill_between(stats['Month'], stats['q10'], stats['q90'], color=colors[label], alpha=0.3)

    plt.xlabel('Month'); plt.ylabel(varname)
    plt.xticks(ticks=range(1,13), labels=[calendar.month_abbr[m] for m in range(1,13)])
    plt.legend(title='Type')
    plt.title(f"Monthly {varname} for {crop} in {basin} river basin")

    if out_file:
        plt.savefig(out_file, dpi=300, bbox_inches='tight')
        print(f"Saved line plot to {out_file}")
    plt.close()


# ====== Main loop ======
for basin in basins:
    for crop in crops:
        yp_path = root_yp / f"{basin}_{crop}_monthly.csv"
        wn_path = root_wn / f"{basin}_{crop}_monthly.csv"
        if not yp_path.exists() and not wn_path.exists():
            print(f"Skipping {basin} {crop} (no files)")
            continue

        try:
            ha_da = load_mask_ha(basin, crop)
        except Exception as e:
            print(f"Skipping {basin} {crop}: {e}")
            continue

        yp_df = read_monthly_csv(yp_path) if yp_path.exists() else pd.DataFrame()
        wn_df = read_monthly_csv(wn_path) if wn_path.exists() else pd.DataFrame()

        valid_N_months, valid_P_months = [], []
        if not yp_df.empty:
            for m in range(1,13):
                sub = yp_df[yp_df['Month']==m]
                if not sub.empty and sub['N_demand'].replace(np.nan,0).sum()>0:
                    valid_N_months.append(m)
                if not sub.empty and sub['P_demand'].replace(np.nan,0).sum()>0:
                    valid_P_months.append(m)
                    make_monthly_maps(
                        basin, crop, ha_da, yp_df, 'N_deficit',
                        unit='kg/ha',
                        out_file=out_root/f"{basin}_{crop}_N_deficit_map_Yp.png"
                    )
                    make_monthly_maps(
                        basin, crop, ha_da, yp_df, 'P_deficit',
                        unit='kg/ha',
                        out_file=out_root/f"{basin}_{crop}_P_deficit_map_Yp.png"
                        )
                    
                # =========  Violin Plot ===============
                # if not yp_df.empty or not wn_df.empty:
                #     make_split_violin(
                #         basin, crop, yp_df, wn_df, ha_da=ha_da, varname='N_uptake', valid_months=valid_N_months,
                #         out_file=out_root/f"{basin}_{crop}_mon_N_uptake_Yp_S2.png"
                #     )
                #     make_split_violin(
                #         basin, crop, yp_df, wn_df, ha_da=ha_da, varname='P_uptake', valid_months=valid_P_months,
                #         out_file=out_root/f"{basin}_{crop}_mon_P_uptake_Yp_S2.png"
                #     )
                # if not yp_df.empty or not wn_df.empty:
                #     make_monthly_lines_with_percentiles(
                #         basin, crop, yp_df, wn_df, ha_da, varname='N_uptake', valid_months=valid_N_months, out_file=out_root/f"{basin}_{crop}_mon_N_uptake_line_Yp_S2.png")

                #     make_monthly_lines_with_percentiles(
                #         basin, crop, yp_df, wn_df, ha_da, varname='P_uptake', valid_months=valid_N_months, out_file=out_root/f"{basin}_{crop}_mon_P_uptake_line_Yp_S2.png")
print('All done.')