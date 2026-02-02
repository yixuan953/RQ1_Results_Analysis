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
python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/2_3_Cal_Final_Fert_input.py
conda deactivate


# Step 1: Transform the output from .csv to .nc format
# python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Fertilizer_Reduction/1_Export2nc.py

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


