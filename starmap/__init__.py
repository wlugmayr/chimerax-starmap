#
# Copyright (c) 2017-2022 by the Universitätsklinikum Hamburg-Eppendorf (UKE)
# Written by Wolfgang Lugmayr <w.lugmayr@uke.de>
#
"""
The StarMap ChimeraX tool enables Cryo-EM refinement and analysis
using the external Rosetta modeling software.
"""

# -----------------------------------------------------------------------------
__version__ = "1.1.74"
__versionTime__ = "29 November 2022 16:50"
__author__ = "Wolfgang Lugmayr <w.lugmayr@uke.de>"
__copyright__ = "Copyright (c) 2013-2022 by the Universitätsklinikum Hamburg-Eppendorf (UKE)"


# -----------------------------------------------------------------------------
from chimerax.core.toolshed import BundleAPI  # @UnresolvedImport

# -----------------------------------------------------------------------------
class _MyAPI(BundleAPI):
    """Plug-in entry point"""
    # -------------------------------------------------------------------------
    @staticmethod
    def get_class(class_name):
        """Returns gui class"""
        if class_name == 'StarMap':
            from . import tool
            return tool.StarMap
        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def start_tool(session, tool_name, **kw):
        """Returns gui instance"""
        session.logger.info('> starting StarMap ' + __version__)
        session.logger.info('> use command <stmhelp show> for the StarMap manual')
        from .config import check_config
        check_config()

        from .tool import StarMap
        return StarMap.get_singleton(session)

    # -------------------------------------------------------------------------
    @staticmethod
    def register_command(command_name, logger):
        """registers commandline commands"""
        from chimerax.core.commands import register  # @UnresolvedImport
        from . import cmd
        if command_name == "stmconfig":
            register(command_name, cmd.starmap_config_desc, cmd.starmap_cmd_handler, logger=logger)
        if command_name == "stmhelp":
            register(command_name, cmd.starmap_help_desc, cmd.starmap_cmd_handler, logger=logger)
        if command_name == "stmset":
            register(command_name, cmd.starmap_set_desc, cmd.starmap_cmd_handler, logger=logger)
        if command_name == "stmrunfsc":
            register(command_name, cmd.starmap_runfsc_desc, cmd.starmap_cmd_handler, logger=logger)
        if command_name == "stmrunlcc":
            register(command_name, cmd.starmap_runlcc_desc, cmd.starmap_cmd_handler, logger=logger)
        if command_name == "stmrunzsc":
            register(command_name, cmd.starmap_runzsc_desc, cmd.starmap_cmd_handler, logger=logger)
        return

# -----------------------------------------------------------------------------
bundle_api = _MyAPI()
