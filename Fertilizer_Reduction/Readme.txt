# =========== The scripts of this section are used to calculate the fertilizer input for the fertilizer reduction scenarios =================
# Fertilizer reduction scenario 1: Reduce the fertilizer input for each pixel until the regional boundary is met 
# Fertilizer reduction scenario 2: 
    - For pixels where the regional boundary was exceeded in the baseline scenario --> Keep the fertilizer input as scenario 1
    - For pixels where the regional boudnary was not exceeded in the baseline scenario --> Increase the fertilzier input until the regional boundary was exceeded

# ===== Main scripts and calculation procedures for fertilizer reduction scenarios ==========
1-1: Calculate where the boundary has been exceeded
    Code directory:  ../Fertilizer_Reduction/1_1_Get_exessive_NP.py
    Input:           Model output (.nc)
    Output:          N, P runoff excessive amount [kg/ha]: {basin}_{crop}_excessive_NP_losses.nc

1-2: Calculate the fertilizer input after reduction
    Code directory: ../Fertilizer_Reduction/1_2_Get_Fert_Red.py
    Input:           N, P runoff excessive amount [kg/ha]: {basin}_{crop}_excessive_NP_losses.nc
                     N, P runoff [kg/ha] from model output (.nc)
                     Original N, P fertilizer input [kg/ha] (.nc)
    Output:          N, P fertilizer input after reduction: {basin}_{cropname}_Fert_2005-2020_FixRate.nc

2-1: Summarize the sensitivity anslysis results from step 1-2
    Code directory: ../Fertilizer_Reduction/2_1_Sum_sens_results.py
    Input:           N, P runoff [kg/ha] and yield [kg/ha] from model output (.nc) with the reduced fertilizer input (from step 1-2) 
    Output:          Summarized 10 yr-average N, P runoff and yield (sens, lon, lat): 
                        {basin}_{crop}_Yields.nc 
                        {basin}_{crop}_N_Exceedance.nc
                        {basin}_{crop}_P_Exceedance.nc

2-2 & 2-3: Get the final fertilizer input after reudction 
    Code directory: ../Fertilizer_Reduction/2_2_Get_Fert_red.py
                    ../Fertilizer_Reduction/2_3_Cal_Final_Fert_input.py
    Input:           Summarized 10 yr-average N, P runoff and yield (sens, lon, lat) (from step 2-1)
                     Origian N, P fertilizer input [kg/ha] (.nc)
    Output:          N, P fertilizer input after reduction (with consideration of sensitivity analysis): 
                        {basin}_{cropname}_Fert_2005-2020_FixRate.nc

3_1: Calculate the fertilizer input after regional increase
    Code directory: ../Fertilizer_Reduction/3_1_Get_Fert_inc.py
    Input:           N, P runoff excessive amount [kg/ha]: {basin}_{crop}_excessive_NP_losses.nc
                     N, P runoff [kg/ha] from model output (.nc)
                     N, P fertilizer input [kg/ha] after step 2-3: {basin}_{cropname}_Fert_2005-2020_FixRate.nc
    Output:          N, P fertilizer input after regional increases: {basin}_{cropname}_Fert_2005-2020_FixRate.nc

3_2 & 3_3: Get the final fertilzier input after redistribution
    Code directory: ../Fertilizer_Reduction/3_2_Get_Fert_inc.py
                    ../Fertilizer_Reduction/3_3_Cal_Final_Fert_input.py
    Input:           Summarized 10 yr-average N, P runoff and yield (sens, lon, lat) (from step 2-1)
                     N, P fertilizer input [kg/ha] after step 2-3: {basin}_{cropname}_Fert_2005-2020_FixRate.nc
    Output:          N, P fertilizer input after increase (with consideration of sensitivity analysis): 
                        {basin}_{cropname}_Fert_2005-2020_FixRate.nc