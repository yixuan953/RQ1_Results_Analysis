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

# =============== Test 1 ===============
# Q: If 2010 - 2019 can represent the current climate?
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/SimPeriod_Test/1_Yield_Compare.py
# ======================================

# =============== Test 2 ==============
# Q: How many years do the model need to warm up?
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/SimPeriod_Test/2_Check_WarmUp.py

# =============== Test 3 ==============
# Q: Is 5 years enough for warm up? Check yield and losses
# Q: Is the fertilizer reduction okay? Plot yield losses maps
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/SimPeriod_Test/3_Check_Yield_Losses.py

# =============== Test 4 ======================
# Q: Is PC ratio calcualted correctly?
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/SimPeriod_Test/4_Check_PC_ratio.py

# =============== Test 5 ======================
# Q: How does the N, P balance change when we adjust irrigation and fertilzer input?
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/SimPeriod_Test/5_N_balance.py
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/SimPeriod_Test/5_P_balnce.py

# =============== Test 6 ======================
# Q: How did the crop production and P pool change in the fertilization reduction process?
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/SimPeriod_Test/6_Plines_pool_fert.py
python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/SimPeriod_Test/7_Total_production_annual.py

conda deactivate