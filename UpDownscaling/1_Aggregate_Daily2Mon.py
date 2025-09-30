import pandas as pd
import numpy as np
from pathlib import Path

basins = ["LaPlata", "Indus", "Yangtze", "Rhine"]
crops = ["wheat", "maize", "rice", "soybean"]

daily_dir_tpl = Path("/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Yp/{basin}_{crop}_daily.csv")

for basin in basins:
    for crop in crops:
        daily_fp = daily_dir_tpl.with_name(f"{basin}_{crop}_daily.csv")
        if not daily_fp.exists():
            print(f"{daily_fp} does not exist, skipping.")
            continue

        df = pd.read_csv(daily_fp)
        df['Date'] = pd.to_datetime(df['Year'].astype(str), format='%Y') + pd.to_timedelta(df['Day'] - 1, unit='D')
        df['Month'] = df['Date'].dt.month

        # Deficits
        df['N_deficit'] = np.where(df['N_uptake'] > 0,np.maximum(df['N_uptake'] - df['N_avail'], 0),0)
        df['P_deficit'] = np.where(df['P_uptake'] > 0,np.maximum(df['P_uptake'] - df['P_avail'], 0),0)
        df['Days_Fertilization'] = ((df['Fertilization'] == 11) | (df['Fertilization'] == 12)).astype(int)

        # Crop-specific dev stage mask
        if crop == 'soybean':
            dev_mask = (df['Dev_Stage'] > 0) & (df['Dev_Stage'] < 1.5)
        else:
            dev_mask = (df['Dev_Stage'] > 0) & (df['Dev_Stage'] < 1.3)

        # Split df for N/P demand aggregation
        df_demand = df[dev_mask].copy()

        # Aggregate sums
        sum_cols_all = ['SurfaceRunoff','SubsurfaceRunoff','Percolation',
                        'Days_Fertilization','N_uptake','P_uptake',
                        'N_deficit','P_deficit','N_decomp','P_decomp',
                        'P_Surf','P_Sub','P_Leaching']

        # Aggregate general sums
        monthly_all = df.groupby(['Lat','Lon','Year','Month'])[sum_cols_all].sum().reset_index()

        # Aggregate N_demand and P_demand only for dev stage
        monthly_demand = df_demand.groupby(['Lat','Lon','Year','Month'])[['N_demand','P_demand']].sum().reset_index()

        # Merge the two
        monthly = pd.merge(monthly_all, monthly_demand, on=['Lat','Lon','Year','Month'], how='left')

        monthly_fp = daily_fp.parent / f"{basin}_{crop}_monthly.csv"
        monthly.to_csv(monthly_fp, index=False)
        print(f"Saved monthly data: {monthly_fp}")
