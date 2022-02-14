#!/bin/sh

# setup the environment
source /etc/profile.d/modules.sh
module load rosetta/3.13

# run Rosetta script
echo "### start: " $(date)
echo "### node : " $(hostname)

@@ROSETTA_SCRIPT_EXE@@ \
    -parser:protocol @@ROSETTA_SCRIPT_FILE@@ \
    -edensity:mapfile @@DENSITY_FILE@@ \
    -s @@INPUT_PDB_FILE@@ \
    -in::file::centroid_input \
    -mapreso @@HIRES@@ \
    -nstruct @@NSTRUCT@@ \
    -default_max_cycles 200 \
    -crystal_refine \
    -edensity::cryoem_scatterers true \
    -ignore_unrecognized_res \
    -out:level 200

echo "### end: " $(date)

