#!/bin/sh
# This StarMap template uses GNU parallel to compute multiple models on available CPUs
# Used on MacOS via HomeBrew installation

echo "### start: " $(date)
echo "### node : " $(hostname)

parallel -j @@CORES@@ \
'@@ROSETTA_SCRIPT_EXE@@ \
-parser:protocol "@@ROSETTA_SCRIPT_FILE@@" \
-edensity:mapfile "@@DENSITY_FILE@@" \
-s "@@INPUT_PDB_FILE@@" \
-in::file::centroid_input \
-mapreso @@HIRES@@ \
-nstruct 1 \
-default_max_cycles 200 \
-crystal_refine \
-edensity::cryoem_scatterers true \
-ignore_unrecognized_res \
-exclude_dna_dna false \
-out:level 200 \
-out:no_nstruct_label \
-out:pdb \
-out:suffix _`printf %04d {}`
' ::: {1..@@NSTRUCT@@}

echo "### end: " $(date)

