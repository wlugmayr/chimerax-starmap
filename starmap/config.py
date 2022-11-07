#
# Copyright (c) 2013-2022 by the Universitätsklinikum Hamburg-Eppendorf (UKE)
# Written by Wolfgang Lugmayr <w.lugmayr@uke.de>
#
"""
Configuration tools
"""
import os
import platform

# -----------------------------------------------------------------------------
SEP = os.sep
if platform.system() == "Windows":
    SEP = os.sep + os.sep

# -----------------------------------------------------------------------------
ROSETTA_SCRIPTS_CMD = "rosetta_scripts"
ROSETTA_SCRIPTS_MPI_CMD = "rosetta_scripts.mpi"
ROSETTA_DENSITY_CMD = "density_tools"
ROSETTA_SYMMDEF_CMD = "${ROSETTA3}/source/src/apps/public/symmetry/make_symmdef_file.pl"
ROSETTA_FOUND = False

STARMAP_ROSETTA_SCRIPT = "rosetta_tmpl_1.2.xml"
STARMAP_ROSETTA_APIX_SCRIPT = "rosetta_apix.xml"
STARMAP_SYMMETRY_CMD = "check_symmetry.sh"
STARMAP_HELP = None
STARMAP_USER_ENV = {}
STARMAP_TEMPLATES_DIR = ""

CYGWIN_BASH = r'C:\\Cygwin64\\bin\\bash.exe'
WSL_BASH = r'C:\\Windows\system32\\bash.exe'
BASH = WSL_BASH

# -----------------------------------------------------------------------------
def cmd_exists(name):
    """Check whether `name` is on PATH and marked as executable"""
    from shutil import which
    return which(name) is not None

# -----------------------------------------------------------------------------
def cmd_location(name):
    """Check whether `name` is on PATH and marked as executable"""
    from shutil import which
    return which(name)

# -----------------------------------------------------------------------------
def install_path(pkg):
    """Return the local install path"""
    import importlib
    try:
        m = importlib.import_module(pkg)
        s = str(m.__path__).split("'")
        return s[1]
    except ImportError:
        return None

# -----------------------------------------------------------------------------
def rosetta_cmd_location(cmd):
    """Returns the full path to the executable"""
    buildtype = []
    buildtype.append("default")
    buildtype.append("static")
    compiler = []
    compiler.append("gcc")
    compiler.append("icc")
    compiler.append("clang")
    dist = []
    dist.append("linux")
    dist.append("macos")
    for c in compiler:
        for o in dist:
            for t in buildtype:
                if "mpi" in cmd:
                    n = cmd + '.' + o + c + 'release'
                else:
                    n = cmd + '.' + t + '.' + o + c + 'release'
                if cmd_exists(n):
                    return cmd_location(n)
    return None

# -----------------------------------------------------------------------------
def get_data_location():
    """Returns the full datadir to the installed data directory"""
    # global is $CHIMERAX/libexec/UCSF-ChimeraX/lib/python3.8/site-packages/starmap
    # local is $HOME/.local/share/ChimeraX/1.2/site-packages/starmap
    # windows local is $HOME\\AppData\\Local\\UCSF\\ChimeraX\\share\\starmap
    # darwin local is $HOME/Library/Application Support/ChimeraX/share/starmap
    # ubuntu global is /usr/lib/ucsf-chimerax/share/starmap
    if '.local' in install_path("starmap"):
        tok = 'ChimeraX'
    else:
        tok = 'libexec' + SEP + 'UCSF-ChimeraX'

    if platform.system() == "Windows":
        tok ='UCSF' + SEP + 'ChimeraX'

    if platform.system() == "Darwin":
        tok ='ChimeraX'

    topdir = install_path("starmap").split(tok)[0]
    #print("starmap> topdir=" + topdir)
    if os.path.exists(topdir):
        datadir = topdir + tok + SEP + "share"  + SEP + "starmap" + SEP
        #print("starmap> datadir=" + datadir)
        if os.path.exists(datadir):
            return datadir
    # dirty fix for global Ubuntu installations from bash
    datadir = "/usr/lib/ucsf-chimerax/share/starmap/"
    #print("starmap> datadir=" + datadir)
    if os.path.exists(datadir):
        return datadir
    return topdir

# -----------------------------------------------------------------------------
def data_location(dataname):
    """Returns the full path to the file in the installed data directory"""
    try:
        file = get_data_location() + str(dataname)
        if os.path.exists(file):
            return file
    except TypeError:
        return "/starmap_data_directory_not_found"

# -----------------------------------------------------------------------------
def tmp_location():
    """Returns the full path to a usable tmp directory"""
    try:
        tok = 'Local'
        localdir = get_data_location().split(tok)[0]
        tmpdir = localdir + tok + SEP + "Temp"  + SEP
        #print("starmap> tmpdir=" + tmpdir)
        if os.path.exists(tmpdir):
            return tmpdir
    except TypeError:
        return "/tmp"

# -----------------------------------------------------------------------------
def help_url(htmlfile=None):
    """Check if the files exist"""
    global STARMAP_HELP
    STARMAP_HELP = "docs" + SEP + "index.html"
    loc = data_location(STARMAP_HELP) or STARMAP_HELP
    if platform.system() == "Windows":
        loc = loc.replace(' ', "%20")
        loc = loc.replace('\\\\', "/")
        loc = "file:///" + loc
    else:
        loc = "file://" + loc
    STARMAP_HELP = loc

    if htmlfile:
        return loc.replace('index.html', htmlfile)

    return STARMAP_HELP

# -----------------------------------------------------------------------------
def win_path_wrapper(p=None):
    """Wraps for Windows and Unix"""
    if not platform.system() == "Windows":
        return p

    p = p.replace('\\\\', '/')
    p = p.replace('Program F', 'Program\\ F')
    if BASH == WSL_BASH:
        drive = p.rsplit(':')[0]
        p = p.replace(drive + ':', '/mnt/' + drive.lower())

    return p

# -----------------------------------------------------------------------------
def win_cmd_wrapper(cmd=None):
    """Wraps for Windows and Unix"""
    if not platform.system() == "Windows":
        return cmd

    cmd = win_path_wrapper(cmd)
    cmd = BASH + " -c " + '"' + cmd + '"'
    return cmd

# -----------------------------------------------------------------------------
def check_rosetta_cmd():
    """Initializes the Rosetta cmd locations"""
    #print("starmap> searching Rosetta executables")
    global ROSETTA_SCRIPTS_CMD, ROSETTA_SCRIPTS_MPI_CMD, ROSETTA_DENSITY_CMD, ROSETTA_FOUND, ROSETTA_SYMMDEF_CMD
    ROSETTA_SCRIPTS_CMD = rosetta_cmd_location(ROSETTA_SCRIPTS_CMD) or ROSETTA_SCRIPTS_CMD
    ROSETTA_SCRIPTS_MPI_CMD = rosetta_cmd_location(ROSETTA_SCRIPTS_MPI_CMD) or ROSETTA_SCRIPTS_MPI_CMD
    ROSETTA_DENSITY_CMD = rosetta_cmd_location(ROSETTA_DENSITY_CMD) or ROSETTA_DENSITY_CMD
    if cmd_exists('make_symmdef_file.pl'):
        ROSETTA_SYMMDEF_CMD = cmd_location('make_symmdef_file.pl')
    # add default suffix
    if not ROSETTA_SCRIPTS_MPI_CMD.endswith('release'):
        ROSETTA_SCRIPTS_MPI_CMD = ROSETTA_SCRIPTS_MPI_CMD + '.linuxgccrelease'
    if not ROSETTA_SCRIPTS_CMD.endswith('release'):
        ROSETTA_SCRIPTS_CMD = ROSETTA_SCRIPTS_CMD + '.linuxgccrelease'
        ROSETTA_DENSITY_CMD = ROSETTA_DENSITY_CMD + '.linuxgccrelease'
    else:
        ROSETTA_FOUND = True

    if not ROSETTA_FOUND:
        if platform.system() == "Darwin":
            ROSETTA_SCRIPTS_CMD = 'rosetta_scripts.static.macosclangrelease'
            ROSETTA_SCRIPTS_MPI_CMD = 'rosetta_scripts.static.macosclangrelease'
            ROSETTA_DENSITY_CMD = 'density_tools.static.macosclangrelease'
        if platform.system() == "Windows":
            ROSETTA_SCRIPTS_CMD = 'rosetta_scripts.static.linuxgccrelease'
            ROSETTA_SCRIPTS_MPI_CMD = 'rosetta_scripts.static.linuxgccrelease'
            ROSETTA_DENSITY_CMD = 'density_tools.static.linuxgccrelease'
    return

# -----------------------------------------------------------------------------
def check_windows_cmd():
    """Checks basic executables"""
    global BASH, STARMAP_SYMMETRY_CMD
    BASH = cmd_location(WSL_BASH) or None
    if not BASH:
        BASH = "bash.exe_not_found"
        return

    STARMAP_SYMMETRY_CMD = "make_NCS.pl"
    STARMAP_SYMMETRY_CMD = data_location(STARMAP_SYMMETRY_CMD) or STARMAP_SYMMETRY_CMD

    return

# -----------------------------------------------------------------------------
def check_starmap_files():
    """Check if the files exist"""
    global STARMAP_ROSETTA_SCRIPT, STARMAP_ROSETTA_APIX_SCRIPT, STARMAP_SYMMETRY_CMD, STARMAP_HELP
    STARMAP_ROSETTA_SCRIPT = data_location(STARMAP_ROSETTA_SCRIPT) or STARMAP_ROSETTA_SCRIPT
    STARMAP_ROSETTA_APIX_SCRIPT = data_location(STARMAP_ROSETTA_APIX_SCRIPT) or STARMAP_ROSETTA_APIX_SCRIPT
    STARMAP_SYMMETRY_CMD = data_location(STARMAP_SYMMETRY_CMD) or STARMAP_SYMMETRY_CMD
    help_url()
    return

# -----------------------------------------------------------------------------
def config_as_string():
    """Return the configuration for printing"""
    from . import __version__ as version
    s = "\nSTARMAP_VERSION             = " + str(version)
    global ROSETTA_FOUND
    if not ROSETTA_FOUND:
        check_rosetta_cmd()
    s += "\nROSETTA_SCRIPTS_CMD         = " + ROSETTA_SCRIPTS_CMD
    s += "\nROSETTA_SCRIPTS_MPI_CMD     = " + ROSETTA_SCRIPTS_MPI_CMD
    s += "\nROSETTA_DENSITY_CMD         = " + ROSETTA_DENSITY_CMD
    s += "\nROSETTA_SYMMDEF_CMD         = " + ROSETTA_SYMMDEF_CMD
    check_starmap_files()
    s += "\nSTARMAP_ROSETTA_SCRIPT      = " + STARMAP_ROSETTA_SCRIPT
    s += "\nSTARMAP_ROSETTA_APIX_SCRIPT = " + STARMAP_ROSETTA_APIX_SCRIPT
    s += "\nSTARMAP_SYMMETRY_CMD        = " + STARMAP_SYMMETRY_CMD
    s += "\nSTARMAP_HELP                = " + STARMAP_HELP
    get_user_env()
    s += "\nSTARMAP_TEMPLATES_DIR       = " + STARMAP_TEMPLATES_DIR
    for k, v in STARMAP_USER_ENV.items():
        s += '\nSTARMAP_USER' + str(k) + '               = ' + str(v)
    if platform.system() == 'Windows':
        s += "\nBASH                        = " + BASH
        s += "\nTEMP                        = " + tmp_location()
    s += "\nPYTHON_SITE_PACKAGE         = " + install_path("starmap")
    s += "\nLOCAL_CORES                 = " + str(os.cpu_count())
    s += "\n"

    return s

# -----------------------------------------------------------------------------
def get_user_env():
    "get the plugin-specific environment variables"
    for i in range(1, 9):
        envstr = 'STARMAP_USER' + str(i)
        try:
            envval = str(os.environ[envstr])
        except KeyError:
            envval = ""
        override = False
        if i == 1 and envval == "":
            STARMAP_USER_ENV[1] = "extra_res_cen"
            override = True
        if i == 2 and envval == "":
            STARMAP_USER_ENV[2] = "extra_res_fa"
            override = True
        if not override:
            STARMAP_USER_ENV[i] = str(envval)

    try:
        global STARMAP_TEMPLATES_DIR
        STARMAP_TEMPLATES_DIR = str(os.environ["STARMAP_TEMPLATES_DIR"])
    except KeyError:
        STARMAP_TEMPLATES_DIR = get_data_location()

    return


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print(config_as_string())
