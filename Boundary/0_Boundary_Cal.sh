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
    python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/1_Monthly_VIC_runoff.py
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


# ============== Wim's method
# 3.1 Get the cropland area
GetCroplandArea(){
    source /home/WUR/zhou111/miniconda3/etc/profile.d/conda.sh
    conda activate myenv
    python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/2_1_Get_total_Harvest_Area.py
    conda deactivate  
}
# GetCroplandArea

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

    # Critical N, P losses to main crops
    # python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method1_4.py
    
    conda deactivate
}
# Cal_Critical_Method1

Cut_Range(){
    module load cdo
    module load nco
    StudyAreas=("Rhine" "Yangtze" "LaPlata" "Indus") #("Rhine" "Yangtze" "LaPlata" "Indus")
    data_dir="/lustre/nobackup/WUR/ESG/zhou111/2_RQ1_Data/2_StudyArea"
    output_dir="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1"
    N_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1/Global_cropland_critical_N_runoff.nc"
    P_runoff="/lustre/nobackup/WUR/ESG/zhou111/3_RQ1_Model_Outputs/Test_CriticalNP/Method1/Global_cropland_critical_P_runoff.nc"

    for StudyArea in "${StudyAreas[@]}"; 
    do
        crop_mask="${data_dir}/${StudyArea}/range.txt"

        cdo remapnn,$crop_mask $N_runoff ${output_dir}/${StudyArea}_crit_N_runoff.nc
        cdo remapnn,$crop_mask $P_runoff ${output_dir}/${StudyArea}_crit_P_runoff.nc

    done   
}
Cut_Range


# ========= Method 2: Using agriculture runoff * critical concentration
Cal_Critical_Method2(){
    source /home/WUR/zhou111/miniconda3/etc/profile.d/conda.sh
    conda activate myenv
    python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/Test_Method2.py
    conda deactivate
}
# Cal_Critical_Method2