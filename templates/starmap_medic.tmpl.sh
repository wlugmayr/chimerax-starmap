#!/usr/bin/bash

echo "loading specific environment"
source ~/miniconda/etc/profile.d/conda.sh
conda activate medic

echo "running MEDIC"
echo "using $(which detect_errors.py)"
$(which detect_errors.py) @@MEDIC_CLEAN_PDB@@ @@MEDIC_SKIP_RELAX@@ \
	--pdb "@@MEDIC_INPUT_PDB@@" \
	--map "@@DENSITY_FILE@@" \
	--reso @@ANALYSIS_HIRES@@ \
	--verbose \
	@@MEDIC_RUN_PARAMS@@
	
if [ ! -f @@MEDIC_RESULT_PDB@@ ]; then
    echo --- StarMap: MEDIC run failed! ---
    echo --- StarMap: no output file: @@MEDIC_RESULT_PDB@@ ---
    echo --- StarMap: end of log ---
    exit 4
fi

SUMMARY_CXC=MEDIC_summary_@@MEDIC_INPUT@@.cxc
echo "generating file ${SUMMARY_CXC}"
echo "ui tool show StarMap" >${SUMMARY_CXC}
echo "hide models" >>${SUMMARY_CXC}
echo "open @@MEDIC_RESULT_PDB@@" >>${SUMMARY_CXC}
echo "open @@DENSITY_FILE@@" >>${SUMMARY_CXC}
echo "preset 'initial styles' cartoon" >>${SUMMARY_CXC}
echo "transparency 50" >>${SUMMARY_CXC}
echo "color byattribute bfactor palette 0.78,red:0.6,orange:0,blue" >>${SUMMARY_CXC}
echo "stmset medsum=MEDIC_summary_@@MEDIC_INPUT@@.txt" >>${SUMMARY_CXC}
echo "stmopenmedsum" >>${SUMMARY_CXC}
echo

echo "cleaning up"
rm -f slurm-*.out
rm -rf dask-worker-space

echo --- StarMap: end of log ---
