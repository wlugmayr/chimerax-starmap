#
# Rosetta settings for BASH or ZSH
#
# Usage:
#   Adapt and add this content to ~/.bashrc or ~/.zshrc
# 

export ROSETTA3=/beegfs/cssb/software/bio/rosetta/3.13/main
export ROSETTA3_DB=$ROSETTA3/database

export PATH=$ROSETTA3/source/bin:$PATH

# if you want to run make_symmdef_file.pl in a terminal
#export PATH=$ROSETTA3/source/src/apps/public/symmetry:$PATH

# if you want to run molfile_to_params.py in a terminal
#export PATH=$ROSETTA3/source/scripts/python/public:$PATH


