#!/bin/sh
chimerax --nogui prepare_input.cxc
${ROSETTA3}/source/scripts/python/public/molfile_to_params.py --keep-names --clobber --centroid LGQ.mol2 -p LGQ -n LGQ
