#
# Copyright (c) 2013-2022 by the Universitätsklinikum Hamburg-Eppendorf (UKE)
# Written by Wolfgang Lugmayr <w.lugmayr@uke.de>
#
"""
Configuration tools
"""
import os
import platform
import subprocess
import importlib
from shutil import which
from . import __version__ as version
from .medic import MEDIC_SCRIPT_TEMPLATE

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
STARMAP_CONFIG_CHECK = False

WSL = 'C:/Windows/system32/wsl.exe'
WSL_ROSETTA_DIR = ''
WSL_AVAIL = False

# -----------------------------------------------------------------------------
def cmd_exists(name):
    """Check whether `name` is on PATH and marked as executable"""
    return which(name) is not None

# -----------------------------------------------------------------------------
def cmd_location(name):
    """Check whether `name` is on PATH and marked as executable"""
    return which(name)

# -----------------------------------------------------------------------------
def install_path(pkg):
    """Return the local install path"""
    try:
        m = importlib.import_module(pkg)
        s = str(m.__path__).split("'")
        return s[1]
    except ImportError:
        return None

# -----------------------------------------------------------------------------
def wsl_find_location(findstr):
    """Returns the full path to the executable in WSL"""    
    global WSL_AVAIL
    if not WSL_AVAIL:
        return ""
    
    #print(findstr)
    findstr = WSL + ' ' + findstr
    # hide WSL empty popup window when executing
    win_kwargs = {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    win_kwargs['startupinfo'] = startupinfo
    output = subprocess.run(findstr.split(), capture_output=True, text=True, **win_kwargs).stdout
    if not output:
        return ""
    return str(output.strip())

# -----------------------------------------------------------------------------
def wsl_check_distribution():
    """Checks if a WSL compatible distribution is installed"""
    if not platform.system() == "Windows":
        return ""

    cmdstr = 'wsl.exe --status'    
    win_kwargs = {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    win_kwargs['startupinfo'] = startupinfo
    diststr = subprocess.run(cmdstr.split(), capture_output=True, text=True, **win_kwargs).stdout
    
    global WSL_AVAIL
    print("starmap> checking WSL2 installation by calling:")
    print("starmap> wsl.exe --status")
    if diststr:
        for line in diststr.splitlines():
            if len(line.strip()) > 1:
                print("wsl> " + str(line))
                WSL_AVAIL = True
        return diststr
    else:
        print("wsl> ")
        print("starmap> ERROR using the default Windows Subsystem for Linux (WSL2)!!!\nstarmap> Is WSL properly installed?")
    return ""

# -----------------------------------------------------------------------------
def wsl_rosetta_cmd_location(rosettacmd, grepdir):
    """Returns the full path to the executable in WSL. Search specific dirs for faster startup."""
    
    global WSL_AVAIL
    if platform.system() == "Windows" and WSL_AVAIL:
        global WSL_ROSETTA_DIR
        finddir = '/usr/local/rosetta'
        if WSL_ROSETTA_DIR:
            finddir = WSL_ROSETTA_DIR
        if not WSL_ROSETTA_DIR:
            findstr =  "/usr/bin/find " + finddir + r" -type d | /usr/bin/grep 'source\/bin'"
            WSL_ROSETTA_DIR = wsl_find_location(findstr)
        elif grepdir == 'apps':
            finddir = WSL_ROSETTA_DIR.removesuffix('bin') + 'src/apps/public/symmetry'

        findstr = '/usr/bin/find ' + finddir + ' -name ' + rosettacmd
        output = wsl_find_location(findstr)
        if output is not None and rosettacmd in str(output) and len(output.split('\n')) == 1:
            return str(output.strip())
        if len(output.split('\n')) > 1:
            lines = output.splitlines()
            for line in lines:
                if not 'build' in line and rosettacmd in line:
                    return str(line.strip())
    return None

# -----------------------------------------------------------------------------
def rosetta_cmd_location(cmd):
    """Returns the full path to the executable"""
    global WSL_AVAIL
    if platform.system() == "Windows" and not WSL_AVAIL:
        return None

    buildtype = []
    buildtype.append("static")
    buildtype.append("default")
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
                    rosettacmd = cmd + '.' + o + c + 'release'
                else:
                    rosettacmd = cmd + '.' + t + '.' + o + c + 'release'
                if platform.system() == "Windows":
                    loc = wsl_rosetta_cmd_location(rosettacmd, 'bin')
                    if rosettacmd in str(loc):
                        return loc
                if cmd_exists(rosettacmd):
                    return cmd_location(rosettacmd)
    return None

# -----------------------------------------------------------------------------
def get_data_location():
    """Returns the full datadir to the installed data directory"""
    # data/share locations
    # global is $CHIMERAX/libexec/UCSF-ChimeraX/lib/python3.8/site-packages/starmap
    # local is $HOME/.local/share/ChimeraX/1.2/site-packages/starmap
    # windows local is $HOME\\AppData\\Local\\UCSF\\ChimeraX\\share\\starmap
    # darwin local is $HOME/Library/Application Support/ChimeraX/share/starmap
    # ubuntu global is /usr/lib/ucsf-chimerax/share/starmap
    return str(install_path("chimerax.starmap")) + SEP

# -----------------------------------------------------------------------------
def data_location(subdir, dataname):
    """Returns the full path to the file in the installed data directory"""
    try:
        file = get_data_location() + str(subdir) + SEP + str(os.path.basename(dataname))
        file = win_path_wrapper(file)
        if os.path.exists(file):
            return file
    except TypeError:
        return "/starmap_data_directory_not_found"
    return ""

# -----------------------------------------------------------------------------
def tmp_location():
    """Returns the full path to a usable tmp directory"""
    try:
        tok = 'Local'
        localdir = get_data_location().split(tok, maxsplit=1)[0]
        tmpdir = localdir + tok + SEP + "Temp"  + SEP
        if os.path.exists(tmpdir):
            return tmpdir
    except TypeError:
        return "/tmp"
    return ""

# -----------------------------------------------------------------------------
def help_url(htmlfile=None):
    """Check if the files exist"""
    global STARMAP_HELP
    STARMAP_HELP = "starmap.html"
    loc = data_location('docs', STARMAP_HELP) or STARMAP_HELP
    if platform.system() == "Windows":
        loc = loc.replace(' ', "%20")
        loc = win_path_wrapper(loc)
        loc = "file:///" + loc
    else:
        loc = "file://" + loc
    STARMAP_HELP = loc
    if htmlfile:
        return loc.replace('starmap.html', htmlfile)
    return STARMAP_HELP

# -----------------------------------------------------------------------------
def win_path_wrapper(p=None):
    """Wraps slashes"""
    if not platform.system() == "Windows":
        return p
    p = p.replace('\\\\', "/")
    return p.replace('\\', "/")

# -----------------------------------------------------------------------------
def wsl_path_wrapper(p=None, windrive=False):
    """Wraps for Windows and Unix"""
    if not platform.system() == "Windows":
        return p
    p = p.replace('\\', '/')
    if windrive:
        drive = p.rsplit(':')[0]
        p = p.replace(drive + ':', '/mnt/' + drive.lower())
    return p

# -----------------------------------------------------------------------------
def wsl_cmd_wrapper(cmd=None, windrive=False):
    """Wraps for WSL"""
    if not platform.system() == "Windows":
        return cmd
    cmd = WSL + ' ' + wsl_path_wrapper(cmd, windrive)
    return cmd

# -----------------------------------------------------------------------------
def check_rosetta_cmd():
    """Initializes the Rosetta cmd locations"""
    #print("starmap> searching Rosetta executables")
    global ROSETTA_SCRIPTS_CMD, ROSETTA_SCRIPTS_MPI_CMD, ROSETTA_DENSITY_CMD, ROSETTA_FOUND, ROSETTA_SYMMDEF_CMD
    ROSETTA_SCRIPTS_CMD = rosetta_cmd_location(ROSETTA_SCRIPTS_CMD) or ROSETTA_SCRIPTS_CMD
    ROSETTA_SCRIPTS_MPI_CMD = rosetta_cmd_location(ROSETTA_SCRIPTS_MPI_CMD) or ROSETTA_SCRIPTS_MPI_CMD
    ROSETTA_DENSITY_CMD = rosetta_cmd_location(ROSETTA_DENSITY_CMD) or ROSETTA_DENSITY_CMD
    symmcmd = 'make_symmdef_file.pl'
    if platform.system() == "Windows":
        loc = wsl_rosetta_cmd_location(symmcmd, 'apps')
        if loc:
            ROSETTA_SYMMDEF_CMD = loc
        else:
            ROSETTA_SYMMDEF_CMD = symmcmd
    elif cmd_exists(symmcmd):
        ROSETTA_SYMMDEF_CMD = cmd_location(symmcmd)
    # add default suffix
    if not ROSETTA_SCRIPTS_MPI_CMD.endswith('release'):
        ROSETTA_SCRIPTS_MPI_CMD = ROSETTA_SCRIPTS_MPI_CMD + '.linuxgccrelease'
    if not ROSETTA_SCRIPTS_CMD.endswith('release'):
        ROSETTA_SCRIPTS_CMD = ROSETTA_SCRIPTS_CMD + '.linuxgccrelease'
        ROSETTA_DENSITY_CMD = ROSETTA_DENSITY_CMD + '.linuxgccrelease'
    else:
        ROSETTA_FOUND = True
    if ROSETTA_SCRIPTS_CMD != os.path.basename(ROSETTA_SCRIPTS_CMD):
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
    global WSL, STARMAP_SYMMETRY_CMD
    WSL = cmd_location(WSL) or None
    if not WSL:
        WSL = "wsl.exe_not_found"
        return
    STARMAP_SYMMETRY_CMD = "make_NCS.pl"
    STARMAP_SYMMETRY_CMD = data_location('contrib', STARMAP_SYMMETRY_CMD) or STARMAP_SYMMETRY_CMD

# -----------------------------------------------------------------------------
def check_starmap_files():
    """Check if the files exist"""
    global STARMAP_ROSETTA_SCRIPT, STARMAP_ROSETTA_APIX_SCRIPT, STARMAP_SYMMETRY_CMD, MEDIC_SCRIPT_TEMPLATE
    STARMAP_ROSETTA_SCRIPT = data_location('templates', STARMAP_ROSETTA_SCRIPT) or STARMAP_ROSETTA_SCRIPT
    STARMAP_ROSETTA_APIX_SCRIPT = data_location('templates', STARMAP_ROSETTA_APIX_SCRIPT) or STARMAP_ROSETTA_APIX_SCRIPT
    STARMAP_SYMMETRY_CMD = data_location('contrib', STARMAP_SYMMETRY_CMD) or STARMAP_SYMMETRY_CMD
    MEDIC_SCRIPT_TEMPLATE = data_location('templates', MEDIC_SCRIPT_TEMPLATE) or MEDIC_SCRIPT_TEMPLATE
    help_url()

# -----------------------------------------------------------------------------
def check_config():
    """Return the configuration for printing"""
    global ROSETTA_FOUND, STARMAP_CONFIG_CHECK
    if not STARMAP_CONFIG_CHECK:
        wsl_check_distribution()
        if not ROSETTA_FOUND:
            check_rosetta_cmd()
        get_user_env()
        check_starmap_files()
        STARMAP_CONFIG_CHECK = True

# -----------------------------------------------------------------------------
def config_as_string():
    """Return the configuration for printing"""
    check_config()
    s = "\nSTARMAP_VERSION             = " + str(version)
    s += "\nROSETTA_SCRIPTS_CMD         = " + ROSETTA_SCRIPTS_CMD
    s += "\nROSETTA_SCRIPTS_MPI_CMD     = " + ROSETTA_SCRIPTS_MPI_CMD
    s += "\nROSETTA_DENSITY_CMD         = " + ROSETTA_DENSITY_CMD
    s += "\nROSETTA_SYMMDEF_CMD         = " + ROSETTA_SYMMDEF_CMD
    s += "\nMEDIC_SCRIPT_TEMPLATE       = " + MEDIC_SCRIPT_TEMPLATE
    s += "\nSTARMAP_ROSETTA_SCRIPT      = " + STARMAP_ROSETTA_SCRIPT
    s += "\nSTARMAP_ROSETTA_APIX_SCRIPT = " + STARMAP_ROSETTA_APIX_SCRIPT
    s += "\nSTARMAP_SYMMETRY_CMD        = " + STARMAP_SYMMETRY_CMD
    s += "\nSTARMAP_HELP                = " + STARMAP_HELP
    s += "\nSTARMAP_TEMPLATES_DIR       = " + STARMAP_TEMPLATES_DIR
    for k, v in STARMAP_USER_ENV.items():
        s += '\nSTARMAP_USER' + str(k) + '               = ' + str(v)
    if platform.system() == 'Windows':
        s += "\nWSL                         = " + win_path_wrapper(WSL)
        s += "\nTEMP                        = " + win_path_wrapper(tmp_location())
    s += "\nPYTHON_SITE_PACKAGE         = " + win_path_wrapper(install_path("chimerax.starmap"))
    s += "\nLOCAL_CORES                 = " + str(os.cpu_count())
    s += "\nFIX_FONT_SIZE               = " + win_path_wrapper(os.path.join(install_path("chimerax.starmap"), "qtstarmapwidget.py"))
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
        STARMAP_TEMPLATES_DIR = data_location('templates', '')

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print(config_as_string())
