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

# 1 - Get the TSUM1, TSUM2, Average yield, Growing length, sowing dates to the .nc file 
python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/S0/1_Export2nc.py

# 2 - Plot the TSUM1, TSUM2, Sowing date, and harvested area
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/S0/2_Plot_TSM_SD_HA.py

conda deactivate