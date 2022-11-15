.. _getting_started:

***************
Getting started
***************

Make sure all steps in the :ref:`installation_guide` section above are done and the *rosetta_script* executable
can be called from the command line where you start *ChimeraX*.

The plug-in tries to detect the naming location and naming convention of the executables when initializing.
If no *Rosetta* executables are detected a warning dialog will appear and *StarMap* will later create scripts with default naming conventions.
These scripts maybe need modification with a normal text editor before execution from the commandline.

More information on how to test the *Rosetta* installation is in the :ref:`rosetta_howto` section.



.. _running:

Use StarMap
===========

1.
Run *ChimeraX*.

2.
The plug-in is in the menu order **Tools -> Volume Data -> StarMap**.
It can also be called by a script or the *ChimeraX* command::

   ui tool show StarMap

3.
You can drag & drop the StarMap window by clicking with the mouse on the text *StarMap*
and move the window with the pressed mouse button inside or outside *ChimeraX*.
The *StarMap* window has a fixed size for layout reasons.

4.
Sample scripts and data are located in the *examples* folder from our website (:ref:`references`).

5.
Each example has a *ChimeraX* **.cxc** command file, which can be loaded and will set the used values in the *StarMap* user interface.

6.
*StarMap* works best in a working directory where all files are located. To switch the working directory in *ChimeraX* use the *ChimeraX* commandline::

  cd ~/myworkdir


Data preparation tips
=====================

Some hints for the data preparation are also on the corresponding tab pages.


Prepare the Cryo-EM map
-----------------------

You can use maps as they are, but you will get much better results when you preprocess them. 
Since the *Relion* software is very popular in Cryo-EM it is used here:

- **Cryo-EM map (half-maps available)**

  - Inspect the output of the *Postprocessing* job in *Relion* and note the gold-standard resolution (in angstroms) and the
    automatically estimated B-factor (typically ranges between −100 and −70).
   
  - Copy the unfiltered half-maps from the gold-standard refinement procedure (*Relion* job *Refine3D*) to the working directory.
    These files are usually named::

	run_half1_class001_unfil.mrc
	run_half2_class001_unfil.mrc

  - Low-pass filter both maps 0.2–0.5 Å above the gold-standard resolution by using the utility *relion_image_handler* in the system shell::

	relion_image_handler --i run_half1_class001_unfil.mrc --o HALF1_FILT.mrc --lowpass RESOLUTION

  - Perform B-factor sharpening in the system shell::

	relion_image_handler --i HALF1_FILT.mrc --o HALF1_SHARP.mrc --bfactor BFACTOR

- **Cryo-EM map (half-maps unavailable)**

  - Low-pass filter the map 0.2–0.5 Å above the reported gold-standard resolution by using the utility 
    *relion_image_handler* in the system shell (see above).


Symmetry definition
-------------------

*StarMap* and *Rosetta* provide tools for generating the proper symmetry files.
See :ref:`symmetry_howto` for useful parameters. 
If you use the tool from the symmetry tab section **Alternative 2 (advanced)** it will also prepare a proper input file (suffix *_INPUT.pdb*)
and preset this as input to *Rosetta* in the *StarMap* user interface.


Ligands
-------

This is not a full guide. Please read the *StarMap* publication for more detailed information.

- **Obtain a PDB file with the 3D structure of the ligand**

  - The ligand is available in the PDB.
    If the ligand of interest was previously solved in the context of a biological macromolecule, then it has already been assigned
    with a three-letter PDB residue code. Such ligands are natively supported by *Rosetta*. Download a 3D model of the ligand in
    *ChimeraX* by using the three-letter residue code; for instance, for *ATP*::

      open ccd:ATP

- **The ligand is not available in the PDB**

  - Open a *SMILES* string by using the *ChimeraX SMILES* translator command; for instance, for *ATP*::

      open smiles:C1=NC(=C2C(=N1)N(C=N2)C3C(C(C(O3)COP(=O)(O)OP(=O)(O)OP(=O)(O)O)O)O)N

  - Select the generated molecule in the *ChimeraX* user interface.
    Set the residue code. To avoid inconsistencies in atom parametrization during *Rosetta* refinement,
    this residue code must be unique; for instance::

      setattr sel r name LIG

- Place the ligand in the expected binding pocket

- Combine the ligand model and the remaining structure into a single model.
  Assuming that the placed ligand has ChimeraX model ID #3::

	combine #2 #3

- Save the combined model (ID #4) in PDB format. 
  Close all other models and open the combined model. If the ligand is from CCD you do not need the steps below.
  
- Select the placed ligand in ChimeraX and save in MOL2 format in the working directory::

	save ligand.mol2 selectedOnly true format mol2 relModel #1

- Generate *Rosetta* parameter files by running the following command in the system shell. 
  The ligand is assigned with an arbitrary three-letter residue code ‘LIG’. This code must be unique (i.e., not present in the CCD)::

	molfile_to_params.py --keep-names --centroid ligand.mol2 -p LIG -n LIG

  If the *Rosetta* script *molfile_to_params.py* is not available in your shell try the location::
  
	${ROSETTA3}/source/scripts/python/public/molfile_to_params.py

- Check if the following output files were created in the working directory::

	LIG.cen.params
	LIG.fa.params

  These files can be set in the *User* tab of *StarMap* and used by using the **ligand** template for script generation at the *Run* tab.

