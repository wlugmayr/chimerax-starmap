*******************
Welcome to StarMap!
*******************

.. image:: _images/starmap_logo.png
  :width: 400
  :alt: Logo


StarMap is an easy-to-be-used mediator between the popular structural display program ChimeraX and the refinement program Rosetta.
StarMap provides a graphical interface within ChimeraX to control and execute Rosetta-based refinements. It includes options for symmetry,
local refinements, as well as independent map validation.
A series of analytical outputs, including precise magnification calibration (pixel size calibration) and Fourier shell correlations (FSC)
to assess the overall quality of the refinement and resolution (map versus model FSC) are being calculated.
Furthermore, per-residue Z-scores provide a fast guide to evaluate and improve local refinements as well as to identify flexible and
potentially functional sites in large macromolecular complexes.

- *ChimeraX*: `https://www.rbvi.ucsf.edu/chimerax/ <https://www.rbvi.ucsf.edu/chimerax/>`_
- *Rosetta*: `https://www.rosettacommons.org/ <https://www.rosettacommons.org/>`_
- *StarMap*: `https://github.com/wlugmayr/chimerax-starmap/ <https://github.com/wlugmayr/chimerax-starmap/>`_
- *StarMap Manual*: `EPUB <StarMap.epub>`_

Note:

- *StarMap* for *ChimeraX* 1.4+ can be installed from the *ChimeraX* toolshed.
- *StarMap* for *ChimeraX* 1.3 with Qt5 support can be downloaded from the GitHub repository and must be installed as described in this manual.


Contact:

- *Wolfgang Lugmayr <w.lugmayr@uke.de>*



.. _starmap_citations:


How to cite StarMap
-------------------

If you use *StarMap* please cite:

- Lugmayr, Kotov et al. StarMap: A user-friendly workflow for Rosetta-driven molecular structure refinement. 
  Nat. Protoc. (2022). `https://doi.org/10.1038/s41596-022-00757-9 <https://doi.org/10.1038/s41596-022-00757-9>`_


Contents
--------

.. toctree::
   :maxdepth: 2

   install_guide.rst
   getting_started.rst
   symmetry_tab.rst
   rosetta_tab.rst
   advanced_tab.rst
   user_tab.rst
   execute_tab.rst
   analysis_tab.rst
   apix_tab.rst
   log_tab.rst
   commands.rst
   troubleshooting.rst
   references.rst