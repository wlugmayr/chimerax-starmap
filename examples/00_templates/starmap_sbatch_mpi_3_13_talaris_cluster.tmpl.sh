#!/bin/zsh

#SBATCH --partition uke,cssb,all
#SBATCH --job-name starmap
#SBATCH --time 7-00:00
#SBATCH --output starmap_cluster.out
#SBATCH --ntasks @@CORES@@
#SBATCH --cpus-per-task 1

source /etc/profile.d/modules.sh
module load rosetta/3.13
export LD_PRELOAD=""

# run Rosetta script
echo "### start: " $(date)
echo "### node : " $(hostname)

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
  -ignore_unrecognized_res \
  -restore_talaris_behavior \
  -out:level 200

echo "### end: " $(date)

