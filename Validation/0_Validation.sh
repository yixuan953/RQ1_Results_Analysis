#!/bin/bash
#-----------------------------Mail address-----------------------------

#-----------------------------Output files-----------------------------
#SBATCH --output=HPCReport/output_%j.txt
#SBATCH --error=HPCReport/error_output_%j.txt

#-----------------------------Required resources-----------------------
#SBATCH --time=60
#SBATCH --mem=25000

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
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Validation/4_WN_management.py

# 5. Compare the N, P losses 
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Validation/5_Compare_NP_loss.py

# 6. Check the irrigation
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Validation/6_Irrigation_Check.py

# 7. Check the total N, P runoff, and N, P balance in ktons
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Validation/7_IMAGE_WOFOST.py
python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Validation/7_N_balance_ktons.py
python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Validation/7_P_balnce_ktons.py

# 7. Compare GLOBIOM and WOFOST runoff
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Validation/7_1_GLOBIOM_WOFOST.py
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Validation/7_2_GLOBIOM_WOFOST.py
conda deactivate