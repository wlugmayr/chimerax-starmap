
.. _commands:

.. index:: Commands

Commands
========

*StarMap* supports the *ChimeraX* commandline with the provided commands described below.

StarMap Commands
^^^^^^^^^^^^^^^^

stmconfig
---------

.. index:: stmconfig

Prints the actual *StarMap* configuration to the *ChimeraX* log window.
::

  stmconfig

This command helps if e.g. the *Rosetta* executables cannot be located or the symmetry script has problems.


stmhelp
-------

.. index:: stmhelp

Opens the help window with the locally installed help files.
::

  stmhelp show


stmset
------

.. index:: stmset

Sets values in the *StarMap* GUI. This feature is used for setting special *StarMap* values from a *.cxc* script
e.g. it is used to save the status of the *StarMap* user interface in a *.cxc* file for later usage.
::

  stmset key=value


Scripting the Analysis
^^^^^^^^^^^^^^^^^^^^^^

For testing purposes we implemented some scripting and *hidden* commands for the analysis part via *ChimeraX* command scripts.
E.g. you could let *ChimeraX* download a PDB and a map, fit them manually and then generate the Z-scores for testing the software.

A script would look like (below called *run_fsc.cxc*)::

	ui tool show StarMap
	stmset densitymap=density_c7.mrc
	stmset mapres=3.3
	stmset alspdb=starting_model_c7.pdb
	stmrunfsc
	stmrunlcc
	stmrunzsc
	exit

And the corresponding commandline call is like::

	chimerax --nogui run_fsc.cxc
	


 