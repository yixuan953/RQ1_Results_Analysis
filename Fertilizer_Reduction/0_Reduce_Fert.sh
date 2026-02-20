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

# Step 0: Transform the output from .csv to .nc format
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/1_Export2nc.py

# Step 1: Calculate excessive N, P losses [kg/ha] for rainfed and sustainable irrigated cropland
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/1_1_Get_exessive_NP.py

# Step 2: Get fertilizer input after reduction [kg/ha] for rainfed and sustainable irrigated cropland
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/1_2_Get_Fert_Red.py

# Step 3: Summarize the fertilizer reduction output
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/2_1_Sum_sens_results.py

# Step 4: Select the fertilizer reduction scenario
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/2_2_Get_Fert_red.py

# Step 5: Get the fertilizer reduction .nc after selection
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/2_3_Cal_Final_Fert_input.py

# Step 6: Increase fertilizer input at locations where the boundary is not exceeded
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/3_1_Get_Fert_inc.py
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/3_2_Sum_sens_results.py
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/3_3_Get_Fert_inc.py
python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/3_4_Cal_Final_Fert_input.py
conda deactivate