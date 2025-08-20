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

# 1 - Get the growing length, potential yield, N and P uptakes to the .nc file 
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/S1/1_Export2nc.py

# 2 - Plot the potential yield, growing days, N uptake, and P uptake
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/S1/2_Plot_Yp.py

# 3 - Get the new HA for the mainrice and secondrice in Yangtze River Basin
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/S1/3_GetMask4SR.py
# After this step, I rename the mask with the orginal HA as XXX_org.nc

conda deactivate