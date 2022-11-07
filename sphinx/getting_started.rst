.. _getting_started:

***************
Getting started
***************

Make sure all steps in the :ref:`installation_guide` section above are done and the *rosetta_script* executable
can be called from the command line where you start *Chimera*.

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

   ui tool show starmap

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


