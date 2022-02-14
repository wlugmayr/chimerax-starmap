#!/bin/sh
#PBS -j oe

set -u
set -x

if [ ! -z ${PBS_O_WORKDIR} ]; then
	cd ${PBS_O_WORKDIR}
fi

# run Rosetta script
echo "### start: " `date`
echo "### node : " `hostname`

mpirun -np @@CORES@@ @@ROSETTA_SCRIPT_EXE@@ \
  -parser:protocol @@ROSETTA_SCRIPT_FILE@@ \
  -edensity:mapfile @@DENSITY_FILE@@ \
  -s @@INPUT_PDB_FILE@@ \
  -in::file::centroid_input \
  -mapreso @@HIRES@@ \
  -nstruct @@NSTRUCT@@ \
  -default_max_cycles 200 \
  -crystal_refine \
  -edensity::cryoem_scatterers true \
  -ignore_unrecognized_res

echo "### end: " `date`
