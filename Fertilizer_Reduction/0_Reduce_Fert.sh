#!/bin/bash
#-----------------------------Mail address-----------------------------

#-----------------------------Output files-----------------------------
#SBATCH --output=HPCReport/output_%j.txt
#SBATCH --error=HPCReport/error_output_%j.txt

#-----------------------------Required resources-----------------------
#SBATCH --time=60
#SBATCH --mem=250000

#--------------------Environment, Operations and Job steps-------------
source /home/WUR/zhou111/miniconda3/etc/profile.d/conda.sh
conda activate myenv

# Step 1: Transform the output from .csv to .nc format
python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/1_Export2nc.py

# Step 2: Get mask for where fertilizer need to be reduced
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/2_Get_Mask_exessive.py

# Step 3: Calculate fertilizer input after reduction
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/1_Fert_Red.py

# Step 4: Sensitivity analysis
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/3_Sensivity_Analysis_N_losses.py
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/4_Sensivity_Analysis_impact_on_Yield.py

# Step 5: Plot the map of land use reduction
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/5_Loss_landuse_production_map.py

# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/4_Sensitivity_Analysis_N_red_rate.py

conda deactivate
