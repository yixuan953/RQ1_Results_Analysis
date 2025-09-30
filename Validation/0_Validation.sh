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

# 1. Compare the yield with GYGA
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Validation/1_GYGA_yield.py

# 2. Compare the uptakes and inputs with GYGA
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Validation/2_Input_Uptake.py

# 3. Get the masks to analyze: where is nutrien limited, where is water limited
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Validation/3_Get_Focus_Mask.py

# 4. Plot focus maps for 4 basins
python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Validation/4_WN_management.py

conda deactivate