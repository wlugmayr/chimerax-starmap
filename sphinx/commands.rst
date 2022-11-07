
.. _commands:

.. index:: Commands

Commands
========

*StarMap* supports the *ChimeraX* commandline with the provided commands described below.

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

Sets values in the *StarMap* GUI. This feature is used for setting special *StarMap* values from a *.cxc* script.
::

  stmset key=value
