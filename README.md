<!-- ![StarMap Logo](file://sphinx/_images/starmap_logo.png){width=400px} -->
![StarMap Logo](sphinx/_images/starmap_logo.png)


*StarMap* is an easy-to-be-used mediator between the popular structural display program *ChimeraX* and the refinement program *Rosetta*.
*StarMap* provides a graphical interface within *ChimeraX* to control and execute *Rosetta*-based refinements. It includes options for symmetry,
local refinements, as well as independent map validation.

A series of analytical outputs, including precise magnification calibration (pixel size calibration) and Fourier shell correlations (FSC)
to assess the overall quality of the refinement and resolution (map versus model FSC) are being calculated.
Furthermore, per-residue Z-scores provide a fast guide to evaluate and improve local refinements as well as to identify flexible and
potentially functional sites in large macromolecular complexes.

In *StarMap v1.2* we have integrated support for *MEDIC (Model Error Detection in Cryo-EM)*,
a robust statistical model that identifies local backbone errors in protein structures built into cryo-EM maps
by combining local fit-to-density with deep-learning-derived structural information.

The *MEDIC* integration is based on *PyRosetta*, can be used in addition or independent of the *StarMap v1.1* workflow
and integrates a *ChimeraX MEDIC* result viewer to easily inspect problematic areas.

# Manuscript

If you use *StarMap* please **read** and **cite**:

- Lugmayr W., Kotov V. et al. StarMap: A user-friendly workflow for Rosetta-driven molecular structure refinement.
  Nat. Protoc. (2022). https://doi.org/10.1038/s41596-022-00757-9

- DiMaio F. et al. Atomic-accuracy models from 4.5-A cryo-electron microscopy data with density-guided iterative local refinement.
  Nat. Methods 12, 361-365 (2015). https://www.nature.com/articles/nmeth.3286
  
- Reggiano G. et al. Robust residue-level error detection in cryo-electron microscopy models.
  Structure (2023). https://doi.org/10.1016/j.str.2023.05.002

If you are interested in the history and background of *StarMap* please read:

- Kotov V., Lugmayr W. How to solve a molecular tangram? Behind the paper:
  https://protocolsmethods.springernature.com/posts/how-to-solve-a-molecular-tangram


# Software releases

The actual GitHub code release is: **StarMap 1.2.23** (see CHANGELOG.txt for changes).

The official *ChimeraX 1.4+ (Qt6)* version of the plugin is available via the **ChimeraX Toolshed** (*Tools->More Tools...*).

Installations using *ChimeraX 1.3 (Qt5)* are available in the **dist** folder of this site.
```
  chimerax -m pip install --user ChimeraX_StarMap-1.2.23-py3-none-any.whl
```

# Development notes

Here are some starting notes on how this tool is developed.

First have a look at the file *dev_functions.source* for example development environment settings. 
These functions are compatible with *BASH* and *ZSH*.

The user interface is done with the *Qt Designer* of Qt5 and the script **qt5_to_qt6.sh** will replace some code statements.

## Create a development environment

Edit the shell function *starmap_create_env* to fit to your needs and call the following statements in your terminal:
```
  source dev_functions.source
  starmap_create_env
```
Install and setup *Rosetta*.

## Set your development environment

Here we use the shell statements in the *starmap_dev_chimerax_centos9* function by calling the following statements in your terminal:
```
  source dev_functions.source
  starmap_dev_chimerax_centos9
```

Just edit or add your own functions.

## Use Makefile targets to develop and test StarMap

We work with *Makefile* targets to do tasks.
	
### Install and test your changes

```
  make bundle-install
```
will generate the documentation and install it directly into your user space of your development *ChimeraX* application for testing.

### Make an installable Python wheel file
```
  make wheeldist-qt5
```
will generate the documentation and make a installable Python wheel file for *ChimeraX 1.3*.

### Change the user interface

```
  make designer
  make test_gui
```
will open *Qt Designer* if you want to change the user interface.
The second test target will show the user interface as pop-up window as it would appear in *ChimeraX*.





