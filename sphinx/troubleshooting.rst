.. _troubleshooting:

**************************
Troubleshooting and HOWTOs
**************************

This section tries to help you with problems installing or using *StarMap* or running *Rosetta*.


.. _rosetta_howto:

Rosetta HowTo
=============

The names of *Rosetta* executables split into the following sections:

  * **toolname**:
    e.g. *rosetta_scripts*, *density_tools*
  * **multi cores support**:
    e.g. *mpi*, *static*, *default* or left empty
  * **operating system**:
    e.g. *linux*, *macos*
  * **used compiler**:
    e.g. *gcc* (GNU compiler), *icc* (Intel compiler), *clang* (Clang compiler mainly MacOS)
  * **release**:
    e.g. *release* (production release), *debug* (development release). Only production releases are currently supported by *StarMap*.

Examples:

  * *rosetta_scripts.mpi.linuxgccrelease*
  * *rosetta_scripts.default.linuxiccrelease*
  * *rosetta_scripts.static.macosclangrelease*

Used executables:

  * **Refinement**:
    *rosetta_scripts* is used for refinement. Either the single-threaded version or the parallel version (*mpi*).

  * **Analysis**:
    *density_tools* are used for most analysis steps. *StarMap* uses the single-threaded version.


.. _rosetta_install_help:

Quick start for installing the Rosetta binary distribution
----------------------------------------------------------

Download the binary package from the *Rosetta* website.

Extract the package on your PC and (*optional*) set a symbolic link for shorter paths::

	cd /usr/local
	tar zxvf /somewhere/Downloads/rosetta_bin_linux_3.13_bundle.tgz
	ln -s rosetta_bin_linux_2021.16.61629_bundle 3.13

Edit your shell environment with your favorite editor or a simple one like *pico* or *nano*::

	nano ~/.bashrc

Add the Rosetta environment::

	export ROSETTA3=/usr/local/rosetta/3.13/main
	export ROSETTA3_DB=$ROSETTA3/database
	export PATH=$ROSETTA3/source/bin:$PATH

For using the *molfile_to_params.py* script from the Unix command line you would need also::

	export PATH=$ROSETTA3/source/scripts/python/public:$PATH

Now open a new terminal and depending on your operating system call one of the following::

	rosetta_scripts.static.linuxgccrelease
	rosetta_scripts.static.macosclangrelease

You should see the program printing messages on the screen. To use this new settings in *ChimeraX* you have to re-login again.

When the *StarMap* plugin is installed you can call *stmconfig* in the commandline of *ChimeraX* or from the *Bash* commandline::

	chimerax -m starmap.config


.. _rosetta_mpi_support:

Adding MPI support to the Rosetta binary distribution
-----------------------------------------------------

*Rosetta* has a binary release for *Linux* and *MacOS*.
When you download this version you can use it direktly.

When you have a powerful workstation with multiple cores running *Linux*, you could consider to add the MPI support for faster parallel calculation with MPI.

First, install the *openmpi* development package with the usual package installer

Now edit the file *$ROSETTA_HOME/main/source/tools/build/site.settings* and change the section as below::

        "overrides" : {
            "cxx" : "mpicxx",
            "cc"  : "mpicc",
        },

Then make the MPI executables as below (in this case 4 local cores are used for parallel compilation)::

	    ./scons.py -j 4 bin mode=release extras=mpi



.. _rosetta_best_practice:

Rosetta best practice
---------------------

By default *StarMap* generates the execution script with the correct settings for you.
You can provide a different template or modify the script with a text editor before running it or submitting it to a computing cluster.

Rosetta *mpi* uses one core/thread per model calculation.

* So if the :ref:`results_number` entry field has e.g. *20* it runs fastest if you call *mpirun* with *21*.
  This can be done on a computing cluster or on a machine with at least *20* cores.
  MPI has 20 working threads plus 1 coordinating thread which in this case does not need much computing power.
* On a local machine with e.g. *8* cores you can still generate *20* models,
  but StarMap uses the Unix **nproc** command to use only as many cores as are available on this machine.
  Otherwise the machine would be overloaded and too busy for work.
  You can set a specific number of cores to use e.g. *6* by editing the execution script with a text editor and then run it by hand.



.. _bash_win_howto:

Windows Subsystem for Linux HowTo
=================================

The *Windows Subsystem for Linux* can run a full Linux distribution like *Ubuntu* on *Windows 10+*.
So you can compile *Rosetta* by yourself (or use the binary download version) and use it in *StarMap* on a computing workstation running *Windows 10+*.
You can access your data files on the filesystem from both systems, if they are located somewhere visible from Windows e.g. *C:\\*.

Path problems:

  The path handling of *Windows* and the *Windows Subsystem for Linux* differs as described below.
  If you have your data in e.g.:

  * *C:\\Users\\username\\Documents\\starmap_examples*

  the corresponding path for *Bash* would be:

  * */mnt/c/Users/username/Documents/starmap_examples*

  StarMap generates the scripts on *Windows* with the Bash Linux-style paths.


Running Linux ChimeraX in WSL HowTo
===================================

This setup requires deeper Linux knowledge and is not recommended for users not familiar with Linux/BASH/GCC.

You can run the user interface of *StarMap* in the Unix version of ChimeraX and have the full *StarMap/Rosetta* functionality.
But due the lack of GPU support you will see only the GUI of *ChimeraX* but you cannot display structures and result files
like *.mrc* or *.pdb*.

To run the limited GUI version of ChimeraX you need to do the following steps:

* Download the XServer *GWSL* from the Mircosoft Store and let it configure your WSL to add graphical support
  (Entry *Auto-Export Display/Audio*).
* Download and compile a newer *Mesa 3D graphics library* (tested with version *21.3.1*). This will overcome the
  *ERROR: ChimeraX requires OpenGL graphics version 3.3*. 
  Put the location of the *mesa* libraries into the *LD_LIBRARY_PATH* environment variable as first entry.


WSL2 with CUDA support HowTo
============================

At the current time this is no easy setup and is only recommended for users familiar with Linux system administration.

Follow the steps in *Enable NVIDIA CUDA on WSL* (:ref:`references`).

* **Hint**: install a suitable NVIDIA driver and check if the following file exists:
  *C:\\Windows\\System32\\lxss\\lib\\nvidia-smi*. This will be later available under Linux as
  */usr/lib/wsl/lib/nvidia-smi* and will be used to check if everything is is configured and useable.
  Linux *ChimeraX* will also use the CUDA libraries from this Windows
  directory, so check if the files are accessible via */usr/lib/wsl/lib*.

* **Optional**: install also the CUDA on WSL packages for additional tools like *Relion* helping you in pre- or
  postprocessing the input files or the results.
  This was tested with the *CUDA on WSL User Guide* (:ref:`references`) section 4.2.6 *Option 1: Using the WSL-Ubuntu Package*.

  
  






