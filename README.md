<!-- ![StarMap Logo](file://sphinx/_images/starmap_logo.png){width=400px} -->
![StarMap Logo](sphinx/_images/starmap_logo.png)


*StarMap* is an easy-to-be-used mediator between the popular structural display program *ChimeraX* and the refinement program *Rosetta*.
*StarMap* provides a graphical interface within *ChimeraX* to control and execute *Rosetta*-based refinements. It includes options for symmetry,
local refinements, as well as independent map validation.

A series of analytical outputs, including precise magnification calibration (pixel size calibration) and Fourier shell correlations (FSC)
to assess the overall quality of the refinement and resolution (map versus model FSC) are being calculated.
Furthermore, per-residue Z-scores provide a fast guide to evaluate and improve local refinements as well as to identify flexible and
potentially functional sites in large macromolecular complexes.


# Manuscript

If you use *StarMap* please **read** and **cite**:

- Lugmayr, Kotov et al. StarMap: A user-friendly workflow for Rosetta-driven molecular structure refinement. 
  Nat. Protoc. (2022). https://doi.org/10.1038/s41596-022-00757-9

# Software releases

The *ChimeraX 1.4+ (Qt6)* version of the plugin will be available via the **ChimeraX Toolshed** in the near future.

Installations using *ChimeraX 1.3 (Qt5)* are available in the **dist** folder of this site.

# Development notes

Here are some starting notes on how this tool is developed.

Since *StarMap* was mainly ported from *Chimera 1.x* to *ChimeraX 0.3* in 2017, some things might work not as now described in the *ChimeraX* development guidelines.

First have a look at the file *dev_functions.source* for example development environment settings. 
These functions are compatible with *BASH* and *ZSH*.

The user interface is done with the QtCreator of Qt5 and the script **qt5_to_qt6.sh** will replace some code statements.

Since we currently build the Qt5 and the Qt6 version of *StarMap*, **make sure you commited your changes before making the distribution wheels as decribted below**!

## Create a development environment

Edit the shell function *starmap_create_env* to fit to your needs and call the following statements in your terminal:
```
  source dev_functions.source
  starmap_create_env
```
Install and setup *Rosetta*.

## Set your development environment

Here we use the shell statments in the *starmap_dev_chimerax_centos9* function by calling the following statements in your terminal:
```
  source dev_functions.source
  starmap_dev_chimerax_centos9
```

## Use Makefile targets to develop and test StarMap

We work with *Makefile* targets to do tasks.

### Make an installable Python wheel file
```
  make dist
```
will generate the documentation and make a installable Python wheel file.
	
### Install and test your changes

```
  make deploy
```
will create the installable wheel file and install it into your developent *ChimeraX* application for testing.

### Change the user interface

```
  make qtcreator
  make test_gui
```
will open *QtCreator* if you want to change the user interface. The second target will show the user interface as pop-up window.





