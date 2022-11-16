#!/bin/sh
chimerax --nogui prepare_map.cxc
chimerax --nogui prepare_model.cxc
rm -f 2lpz_assembly1.pdb
