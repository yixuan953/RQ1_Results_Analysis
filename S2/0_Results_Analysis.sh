#!/bin/bash
#-----------------------------Mail address-----------------------------

#-----------------------------Output files-----------------------------
#SBATCH --output=HPCReport/output_%j.txt
#SBATCH --error=HPCReport/error_output_%j.txt

#-----------------------------Required resources-----------------------
#SBATCH --time=600
#SBATCH --mem=250000

#--------------------Environment, Operations and Job steps-------------
source /home/WUR/zhou111/miniconda3/etc/profile.d/conda.sh

conda activate myenv

# ================== Annual output =====================
# 1 - Plot the annual N and P fluxes maps 
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/S2/1_Nmaps_30y_Avg.py
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/S2/1_Pmaps_30y_Avg.py

# 2 - Plot the basin average N and P fluxes for the past 30 years 
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/S2/2_NbarCharts_30y_Avg.py
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/S2/2_PbarCharts_30y_Avg.py

# 3 - Plot the annual basin-average p pools and p inputs for the past 30 years
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/S2/3_Plines_pool_fert.py

# ================== Daily output =====================
# 4 - "Crop-water-nutrient interactions" for P fluxes
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/S2/4_Plines_fluxes_5y_daily.py

conda deactivate