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

# 3. Get the cropland area
GetCroplandArea(){
    source /home/WUR/zhou111/miniconda3/etc/profile.d/conda.sh
    conda activate myenv
    python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/2_1_Get_total_cropland_Area.py
    conda deactivate  
}
# GetCroplandArea

# 3. Get the critical N, P losses
GetCriticalLoss(){
    source /home/WUR/zhou111/miniconda3/etc/profile.d/conda.sh
    conda activate myenv
    python /lustre/nobackup/WUR/ESG/zhou111/1_RQ1_Code/3_Results_Analysis/Boundary/2_Get_Critical_Loss.py
    conda deactivate  
}
# GetCriticalLoss