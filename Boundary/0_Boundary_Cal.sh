#!/bin/bash
#-----------------------------Mail address-----------------------------

#-----------------------------Output files-----------------------------
#SBATCH --output=HPCReport/output_%j.txt
#SBATCH --error=HPCReport/error_output_%j.txt

#-----------------------------Required resources-----------------------
#SBATCH --time=60
#SBATCH --mem=250000

#--------------------Environment, Operations and Job steps-------------

# 1. Get the global monthly baseflow and runoff from VIC
GetGlobalFlow(){
    source /home/WUR/zhou111/miniconda3/etc/profile.d/conda.sh
    conda activate myenv
    python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/1_Annual_VIC_runoff.py
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/1_Monthly_VIC_runoff.py
    conda deactivate
}
# GetGlobalFlow

# 2. Cut the baseflow and runoff for 4 basins
CutFlow(){

    # baseflow
    cdo invertlat \
    /lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/VIC_baseflow/monthly_baseflow_ensembleMean_1986-2015.nc \
    /lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/VIC_baseflow/monthly_baseflow_ensembleMean_1986-2015_latfix.nc

    # runoff
    cdo invertlat \
    /lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/VIC_runoff/monthly_runoff_ensembleMean_1986-2015.nc \
    /lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/VIC_runoff/monthly_runoff_ensembleMean_1986-2015_latfix.nc

    basins=("LaPlata" "Indus" "Yangtze" "Rhine")

    for basin in "${basins[@]}"; do
        range_file="/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea/${basin}/range.txt"
        outdir="/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea/${basin}/Hydro"
        mkdir -p "$outdir"

        # baseflow
        cdo remapnn,$range_file \
            /lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/VIC_baseflow/monthly_baseflow_ensembleMean_1986-2015_latfix.nc \
            ${outdir}/${basin}_monthly_baseflow_1986-2015.nc

        # runoff
        cdo remapnn,$range_file \
            /lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/VIC_runoff/monthly_runoff_ensembleMean_1986-2015_latfix.nc \
            ${outdir}/${basin}_monthly_runoff_1986-2015.nc

        echo "Done $basin"
    done

}
# CutFlow


# 3.1 Get the cropland area
GetCroplandArea(){
    source /home/WUR/zhou111/miniconda3/etc/profile.d/conda.sh
    conda activate myenv
    python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/2_1_Get_total_Harvest_Area.py
    conda deactivate  
}
#GetCroplandArea

# 3.2 Get the monthly critical N, P losses
GetCriticalLoss(){
    source /home/WUR/zhou111/miniconda3/etc/profile.d/conda.sh
    conda activate myenv
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/2_2_Cal_global_critical_loss.py
    python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/2_Get_Critical_Loss.py
    conda deactivate  
}
# GetCriticalLoss

SumAnnual(){

    BASE_DIR="/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
    BASINS=("Yangtze" "LaPlata" "Indus" "Rhine")
    TYPES=("N_critical_leaching" "N_critical_runoff" "P_critical_leaching" "P_critical_runoff")

    for basin in "${BASINS[@]}"; do
        HYDRO_DIR="${BASE_DIR}/${basin}/Hydro"
        OUT_DIR="${HYDRO_DIR}"

        for type in "${TYPES[@]}"; do
            infile="${HYDRO_DIR}/${basin}_${type}_1986-2015.nc"
            outfile="${OUT_DIR}/${basin}_${type}_annual.nc"

            if [[ -f "$infile" ]]; then
                echo "Summing monthly to annual for $infile ..."
                cdo yearsum "$infile" "$outfile"
            else
                echo "⚠️  File not found: $infile"
            fi
        done
    done

    echo "✅ All basins processed. Annual files saved in each Hydro/Annual directory."

}
# SumAnnual

# ========= Method 1: Downscaling the critical N, P load to cropland
Cal_Critical_Method1(){
    source /home/WUR/zhou111/miniconda3/etc/profile.d/conda.sh
    conda activate myenv
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method1_1.py # Get the total critical N, P runoff (from all sectors) [kg]
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method1_2.py # Get the total agricultural N, P runoff [kg]
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method1_3.py # Get the total cropland N, P runoff [kg]

    # Critical N, P losses for main crops [kg/ha]
    python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method1_4.py
    
    # Total critical N, P losses for main crops [kg]
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method1_5.py

    conda deactivate
}
# Cal_Critical_Method1

Cut_Range(){
    module load cdo
    module load nco
    StudyAreas=("Rhine" "Yangtze" "LaPlata" "Indus") #("Rhine" "Yangtze" "LaPlata" "Indus")
    data_dir="/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
    # output_dir="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1"
    # N_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1/Global_cropland_critical_N_runoff.nc"
    # P_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1/Global_cropland_critical_P_runoff.nc"
    # N_total_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1/Global_maincrop_critical_total_N_runoff.nc"
    # P_total_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1/Global_maincrop_critical_total_P_runoff.nc"
    output_dir="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3"
    N_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/Global_cropland_critical_N_runoff_kgPerha.nc"
    P_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/Global_cropland_critical_P_runoff_kgPerha.nc"
    N_total_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/Global_maincrop_critical_total_N_runoff.nc"
    P_total_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/Global_maincrop_critical_total_P_runoff.nc"

    for StudyArea in "${StudyAreas[@]}"; 
    do
        crop_mask="${data_dir}/${StudyArea}/range.txt"

            GRID_DEF="/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/grids.txt"
            # 1. Critical N Runoff (kg/ha)
            echo "Processing Critical N Runoff (kg/ha)..."
            cdo setgrid,$GRID_DEF $N_runoff tmp_N_ha.nc
            cdo remapnn,$crop_mask tmp_N_ha.nc ${output_dir}/${StudyArea}_crit_N_runoff_kgperha.nc
            rm tmp_N_ha.nc
            # 2. Critical P Runoff (kg/ha)
            echo "Processing Critical P Runoff (kg/ha)..."
            cdo setgrid,$GRID_DEF $P_runoff tmp_P_ha.nc
            cdo remapnn,$crop_mask tmp_P_ha.nc ${output_dir}/${StudyArea}_crit_P_runoff_kgperha.nc
            rm tmp_P_ha.nc
            # 3. Critical N Total Runoff (kg)
            echo "Processing Critical N Total Runoff (kg)..."
            cdo setgrid,$GRID_DEF $N_total_runoff tmp_N_kg.nc
            cdo remapnn,$crop_mask tmp_N_kg.nc ${output_dir}/${StudyArea}_crit_N_runoff_kg.nc
            rm tmp_N_kg.nc
            # 4. Critical P Total Runoff (kg)
            echo "Processing Critical P Total Runoff (kg)..."
            cdo setgrid,$GRID_DEF $P_total_runoff tmp_P_kg.nc
            cdo remapnn,$crop_mask tmp_P_kg.nc ${output_dir}/${StudyArea}_crit_P_runoff_kg.nc
            rm tmp_P_kg.nc

            echo "All four files have been processed and regridded successfully."

    done   
}
Cut_Range

Cut_Range_Irr_Rain(){
    module load cdo
    module load nco
    StudyAreas=("Rhine" "Yangtze" "LaPlata" "Indus") #("Rhine" "Yangtze" "LaPlata" "Indus")
    data_dir="/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
    output_dir="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1"
    N_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1/Global_cropland_critical_N_runoff.nc"
    P_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1/Global_cropland_critical_P_runoff.nc"
    N_total_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1/Global_maincrop_critical_total_N_runoff.nc"
    P_total_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1/Global_maincrop_critical_total_P_runoff.nc"

    for StudyArea in "${StudyAreas[@]}"; 
    do
        crop_mask="${data_dir}/${StudyArea}/range.txt"

        cdo remapnn,$crop_mask $N_runoff ${output_dir}/${StudyArea}_crit_N_runoff_kgperha.nc
        cdo remapnn,$crop_mask $P_runoff ${output_dir}/${StudyArea}_crit_P_runoff_kgperha.nc
        cdo remapnn,$crop_mask $N_total_runoff ${output_dir}/${StudyArea}_crit_N_runoff_kg.nc
        cdo remapnn,$crop_mask $P_total_runoff ${output_dir}/${StudyArea}_crit_P_runoff_kg.nc

    done   
}
# Cut_Range_Irr_Rain


# ========= Method 2: Using agriculture runoff * critical concentration
Cal_Critical_Method2(){
    source /home/WUR/zhou111/miniconda3/etc/profile.d/conda.sh
    conda activate myenv
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method2.py # [kg/ha]
    python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method2_Total.py
    conda deactivate
}
# Cal_Critical_Method2


# ======== Method 3: Assuming all sectors do their job ==============
Cal_Critical_Method3(){
    source /home/WUR/zhou111/miniconda3/etc/profile.d/conda.sh
    conda activate myenv
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method3_0.py
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method3_1.py
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method3_2.py
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method3_3_1.py
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method3_3_2.py
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method3_3_3.py
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method3_4.py # Redistribute to each crop by fertilizer use
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method3_5.py

    
    conda deactivate
}
# Cal_Critical_Method3

# After Test_Method_3_2: Sum up the nitrogen input for all crops
# cd /lustre/nobackup/WUR/ESG/zhou111/Data/Fertilization/N_Total_Input_2015
# cdo -O -f nc4 -z zip_4 -enssum *.nc All_crop_sum.nc


Cut_Range(){
    module load cdo
    module load nco
    StudyAreas=("Rhine" "Yangtze" "LaPlata" "Indus") #("Rhine" "Yangtze" "LaPlata" "Indus")
    croplist=("Rice" "Maize" "Soybean" "Wheat") #("Rhine" "Yangtze" "LaPlata" "Indus")
    data_dir="/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
    output_dir="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/2_Critical_NP_losses/Method3"

    for StudyArea in "${StudyAreas[@]}"; 
            do 
                data_dir="/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
                crop_mask="${data_dir}/${StudyArea}/range.txt"
                
                for crop in "${croplist[@]}";      
                    do
                        # --- NITROGEN (N) CALCULATIONS (Original) ---
                        
                        # 1. N Runoff (kg/ha)
                        N_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/${crop}_crit_N_runoff_kgperha.nc"
                        cdo setgrid,/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/grids.txt $N_runoff tmp_N_ha.nc
                        cdo remapnn,$crop_mask tmp_N_ha.nc ${output_dir}/${crop}/${StudyArea}_crit_N_runoff_kgperha.nc
                        rm tmp_N_ha.nc

                        # 2. Total N Runoff (kg)
                        N_total_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/${crop}_crit_N_runoff_kg.nc"
                        cdo setgrid,/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/grids.txt $N_total_runoff tmp_N_kg.nc
                        cdo remapnn,$crop_mask tmp_N_kg.nc ${output_dir}/${crop}/${StudyArea}_crit_N_runoff_kg.nc
                        rm tmp_N_kg.nc

                        # --- PHOSPHORUS (P) CALCULATIONS (Added) ---

                        # 3. P Runoff (kg/ha)
                        P_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/${crop}_crit_P_runoff_kgperha.nc"
                        cdo setgrid,/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/grids.txt $P_runoff tmp_P_ha.nc
                        cdo remapnn,$crop_mask tmp_P_ha.nc ${output_dir}/${crop}/${StudyArea}_crit_P_runoff_kgperha.nc
                        rm tmp_P_ha.nc

                        # 4. Total P Runoff (kg)
                        P_total_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method3/${crop}_crit_P_runoff_kg.nc"
                        cdo setgrid,/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/1_Global/grids.txt $P_total_runoff tmp_P_kg.nc
                        cdo remapnn,$crop_mask tmp_P_kg.nc ${output_dir}/${crop}/${StudyArea}_crit_P_runoff_kg.nc
                        rm tmp_P_kg.nc
                        
                    done  
            done
}
# Cut_Range

Comp_Method13(){
    source /home/WUR/zhou111/miniconda3/etc/profile.d/conda.sh
    conda activate myenv
    python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/3_Compare_Method13.py
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/4_Agri_NP_runoff_share.py
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/5_Cal_Global_P_conc.py
    conda deactivate
}
# Comp_Method13
