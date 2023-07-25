#
# Copyright (c) 2017-2022 by the Universitätsklinikum Hamburg-Eppendorf (UKE)
# Written by Wolfgang Lugmayr <w.lugmayr@uke.de>
#
"""
Handle all command registered at ChimeraX.
"""
from chimerax.core.commands import CmdDesc, NoArg, StringArg, BoolArg # @UnresolvedImport
from chimerax.help_viewer.tool import HelpUI  # @UnresolvedImport
from .tool import StarMap
from . import config
#from .config import help_url

# -----------------------------------------------------------------------------
starmap_config_desc = CmdDesc(required=[('stmconfig', NoArg)],
                              synopsis='Print StarMap configuration')

starmap_runfsc_desc = CmdDesc(required=[('stmrunfsc', NoArg)],
                              synopsis='Run StarMap FSC analysis')

starmap_runlcc_desc = CmdDesc(required=[('stmrunlcc', NoArg)],
                              synopsis='Run StarMap LCC analysis')

starmap_runzsc_desc = CmdDesc(required=[('stmrunzsc', NoArg)],
                              synopsis='Run StarMap LCC zscore analysis')

starmap_openmedsum_desc = CmdDesc(required=[('stmopenmedsum', NoArg)],
                              synopsis='Open MEDIC summary window')

starmap_help_desc = CmdDesc(required=[('stmhelp', StringArg)],
                            keyword=[("show", NoArg),
                                     ("section", NoArg),
                                    ],
                            synopsis='Show StarMap help')

starmap_set_desc = CmdDesc(required=[('stmset', StringArg)],
                           keyword=[('symm', BoolArg),
                                ],
                           synopsis='Set StarMap values')


# -----------------------------------------------------------------------------
def print_init_warning(session):
    """Print a warning when StarMap is not initialized"""
    session.logger.error("Trying to access StarMap without full initialization!\nSee ChimeraX 'Log' window for details.")
    session.logger.warning("starmap> open StarMap in Tools->More Tools... first or add")
    session.logger.warning("starmap> ui tool show StarMap")
    session.logger.warning("starmap> as first line in your CXC script!")

# -----------------------------------------------------------------------------
def starmap_cmd_handler(session, stmconfig=None, stmhelp=None, stmset=None, stmrunfsc=None, stmrunlcc=None, stmrunzsc=None, stmopenmedsum=None):
    """StarMap command handler"""
    if stmset:
        #session.logger.info("stmset> " + stmset)
        stm = StarMap.get_singleton(session, create=True)
        stm.set_value(stmset)
        return

    if stmconfig:
        session.logger.info(config.config_as_string())
        return

    if stmrunfsc:
        stm = StarMap.get_singleton(session, create=False)
        if not stm:
            print_init_warning(session)
            return
        stm.cxc_exec_fsc_calc()
        return

    if stmrunlcc:
        stm = StarMap.get_singleton(session, create=False)
        if not stm:
            print_init_warning(session)
            return
        stm.cxc_exec_lcc_calc()
        return

    if stmrunzsc:
        stm = StarMap.get_singleton(session, create=False)
        if not stm:
            print_init_warning(session)
            return
        stm.cxc_exec_zsc_calc()
        return

    if stmopenmedsum:
        stm = StarMap.get_singleton(session, create=True)
        stm._show_medic_summary_window()
        return

    if stmhelp:
        #session.logger.info("stmhelp> " + stmhelp)
        hv = HelpUI.get_viewer(session)
        url = config.help_url()

        try:
            section = stmhelp.split('=')[1]
        except IndexError:
            section = ''

        if '#' in section:
            where = section.split('#')
            url = config.help_url(where[0]  + ".html")
            url += '#' + where[1]

        #session.logger.info("stmhelp> url=" + str(url))
        hv.show(url)
        return

    session.logger.info('> no corresponding StarMap command found')
    return
