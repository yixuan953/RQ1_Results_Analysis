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

# ================== Figure 1 =====================
# Purpose: Compare potential yield, yield with current irrigation while assuming sufficient nutrients, and yield with current irrigation and fertilzation
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/RQ1_Ideas/1_Yield_Compare.py

# ================== Figure 2 =====================
# Purpose:
# 1 - Monthly maps of the monthly N_deficit (For each month and each pixel: take the average of the year 1986 - 2015)
# 2 - Monthly maps of the monthly P_deficit (For each month and each pixel: take the average of the year 1986 - 2015)
# 3 - Split violin plots of the N_uptake of the Yp output (left half) and the Water-Nutrient-Limited yield (right half) for each month (year 1986 - 2015, basin)
# 4 - Split violin plots of the P_uptake of the Yp output (left half) and the Water-Nutrient-Limited yield (right half) for each month (year 1986 - 2015, basin)
python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/RQ1_Ideas/2_NP_deficit.py

# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/RQ1_Ideas/Test.py

conda deactivate