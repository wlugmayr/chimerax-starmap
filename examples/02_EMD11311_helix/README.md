# HOWTO

Make sure ChimeraX and the Rosetta executables are callable from the commandline.

Call the following script to use ChimeraX to prepare the input data:
```
    ./prepare_input.sh
```

Start ChimeraX and load the CXC script to preset the values in the StarMap user interface:
```
    chimerax example02_setup_starmap.cxc
```

Go to the Symmetry tab section 'Alternative 2 (Advanced)' and press the Execute button.

Go to the Save/Run tab and save the CXC settings and Rosetta XML script.

Save the Bash script and execute the run locally or submit it to the computing cluster.

