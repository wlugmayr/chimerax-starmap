#
# Copyright (c) 2017-2022 by the Universitätsklinikum Hamburg-Eppendorf (UKE)
# Written by Wolfgang Lugmayr <w.lugmayr@uke.de>
#
"""
Handle the StarMap user interface.
"""

# -----------------------------------------------------------------------------
import os
import platform
import stat
import threading
import subprocess
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.Qt import QIntValidator, QDoubleValidator
#from PyQt6 import QtCore, QtWidgets, QtGui
#from PyQt6.QtGui import QIntValidator, QDoubleValidator
from chimerax.core.tools import ToolInstance  # @UnresolvedImport
from chimerax.ui.gui import MainToolWindow  # @UnresolvedImport
from chimerax.core.commands import run  # @UnresolvedImport
from .qtstarmapwidget import Ui_qtStarMapWidget
from .rosettascripts import script, asXmlList
from .config import ROSETTA_FOUND
from .config import STARMAP_TEMPLATES_DIR


_translate = QtCore.QCoreApplication.translate

TASK_FULL_REBUILD = 'Full rebuild'
TASK_MINIMUM_REBUILD = 'Minimum rebuild'
TASK_REFINEMENT_ONLY = 'Refinement only'
TASK_TORSIAN_REFINEMENT = 'Torsion refine'


# -----------------------------------------------------------------------------
class ExternalBashThread(threading.Thread):
    """Background execution"""

    # -------------------------------------------------------------------------
    def __init__(self):
        """Init this instance"""
        self.stdout = None
        self.stderr = None
        threading.Thread.__init__(self)
        return

    # -------------------------------------------------------------------------
    def set_script(self, cmd="bash", submit=""):
        """Set the commandline to execute"""
        self.cmd = cmd
        self.submit = submit
        return

    # -------------------------------------------------------------------------
    def set_submission(self):
        """Set the commandline to execute"""
        if self.submit.startswith('ts '):
            self.submit += ' -L starmap -n -E '

        self.cmd = self.submit + ' ' + self.cmd
        return

    # -------------------------------------------------------------------------
    def run(self):
        """Calls the command"""
        self.stdout = self.cmd.rsplit(".", 1)[0]  + ".out"
        self.stderr = self.cmd.rsplit(".", 1)[0]  + ".err"
        self.set_submission()

        with open(self.stdout, 'w') as o:
            with open(self.stderr, 'w') as e:
                subprocess.Popen(self.cmd, shell=True, stdout=o, stderr=e, universal_newlines=True)
        return


# -----------------------------------------------------------------------------
class StarMap(ToolInstance):
    """GUI handling"""
    symmPdbFile = ""
    rosettaCxSelPdbFile = ""
    rosettaDensityMapFile = ""
    rosettaSymmFile = ""
    rosettaModelEvalFile = ""
    rosettaConsFile = ""
    rosettaResultPdbFile = ""
    stmBashFile = ""
    stmBashApixFile = ""
    stmRosettaFile = ""
    stmChimeraxFile = ""
    rosettaScriptString = ""
    selectedResiduesCount = 0
    stdout = stderr = None
    fscModelMapCsvFile = ""
    fscCsvFiles = {}
    stmUserSelBashFile = ""
    stmUserSelRosettaFile = ""
    logTabIndex = 7
    localShellTemplates = {}
    remoteShellTemplates = {}


    # -------------------------------------------------------------------------
    def __init__(self, session, tool_name):
        """Initializes this class"""
        ToolInstance.__init__(self, session, tool_name)
        self.display_name = 'StarMap'
        tw = MainToolWindow(self)
        self.tool_window = tw
        self.logger = session.logger
        self._init_gui(tw.ui_area)
        self.tool_window.manage(placement="side")
        self._load_rosetta_script()
        global ROSETTA_FOUND
        if not ROSETTA_FOUND:
            msg = "Rosetta executables not found!\n\n"
            msg += "Scripts can only be generated with default Rosetta executable names."
            msg += " Executing them directly from ChimeraX will therefore fail!"
            QtWidgets.QMessageBox.warning(self.starMapGui.tabWidget, "StarMap Warning", msg, QtWidgets.QMessageBox.Ok)

        return

    # -------------------------------------------------------------------------
    def _init_gui(self, parent):
        """Initializes the user interface"""

        self.starMapGui = Ui_qtStarMapWidget()

        self.starMapGui.setupUi(parent)

        # symmetry tab
        self.starMapGui.symmSelectButton.clicked.connect(self._select_symmetry_pdb)
        self.starMapGui.symmCheckButton.clicked.connect(self._exec_symm_check)
        self.starMapGui.symmRosettaCheckButton.clicked.connect(self._exec_rosetta_symm_check)

        self.starMapGui.symmSelectHelp.clicked.connect(self._help_symm_select)
        self.starMapGui.symmCheckHelp.clicked.connect(self._help_symm_check)
        self.starMapGui.symmRosettaCheckHelp.clicked.connect(self._help_rosetta_symm_check)

        # rosetta tab
        global TASK_FULL_REBUILD, TASK_MINIMUM_REBUILD, TASK_REFINEMENT_ONLY, TASK_TORSIAN_REFINEMENT
        self.starMapGui.rosettaStrategyTaskBox.clear()
        self.starMapGui.rosettaStrategyTaskBox.addItem(_translate("qtStarMapWidget", TASK_FULL_REBUILD))
        self.starMapGui.rosettaStrategyTaskBox.addItem(_translate("qtStarMapWidget", TASK_MINIMUM_REBUILD))
        self.starMapGui.rosettaStrategyTaskBox.addItem(_translate("qtStarMapWidget", TASK_REFINEMENT_ONLY))
        self.starMapGui.rosettaStrategyTaskBox.addItem(_translate("qtStarMapWidget", TASK_TORSIAN_REFINEMENT))
        indexTaskStrategy = lambda: self._index_changed_task_strategy_event()
        self.starMapGui.rosettaStrategyTaskBox.currentIndexChanged.connect(indexTaskStrategy)

        self.starMapGui.rosettaStrategyValueBox.clear()
        self.starMapGui.rosettaStrategyValueBox.addItem(_translate("qtStarMapWidget", "auto"))
        self.starMapGui.rosettaStrategyValueBox.addItem(_translate("qtStarMapWidget", "user"))
        indexValueStrategy = lambda: self._index_changed_value_strategy_event()
        self.starMapGui.rosettaStrategyValueBox.currentIndexChanged.connect(indexValueStrategy)
        self.starMapGui.rosettaStrategyResiduesEdit.setDisabled(True)

        self.starMapGui.advancedDensityWeightsValueBox.clear()
        self.starMapGui.advancedDensityWeightsValueBox.addItem("ref2015")
        self.starMapGui.advancedDensityWeightsValueBox.addItem("talaris2013")
        self.starMapGui.advancedDensityWeightsValueBox.setCurrentIndex(0)

        # only rosetta tab changes all mapres
        intValidator = QIntValidator(1,99)
        doubleValidator = QDoubleValidator(0.1, 19.9, 2)
        #self.starMapGui.rosettaResolutionEdit.setInputMask("00.00");
        self.starMapGui.rosettaResolutionEdit.setValidator(doubleValidator)
        self.starMapGui.analysisResolutionEdit.setValidator(doubleValidator)
        self.starMapGui.apixResolutionEdit.setValidator(doubleValidator)
        self.starMapGui.rosettaResultsEdit.setValidator(intValidator)
        self.starMapGui.rosettaResolutionEdit.textChanged.connect(self._changed_mapres1_event)
        #self.starMapGui.analysisResolutionEdit.textChanged.connect(self._changed_mapres2_event)
        #self.starMapGui.apixResolutionEdit.textChanged.connect(self._changed_mapres3_event)
        self.starMapGui.rosettaResultsEdit.textChanged.connect(self._changed_models_event)

        self.starMapGui.rosettaCxSaveButton.clicked.connect(self._save_chimerax_pdb)
        self.starMapGui.rosettaCxSelectButton.clicked.connect(self._select_chimerax_pdb)
        self.starMapGui.rosettaDensityMapSelectButton.clicked.connect(self._select_rosetta_densitymap)
        self.starMapGui.rosettaModelCheckBox.clicked.connect(self._changed_model_evaluation_event)
        self.starMapGui.advancedSymmSelectButton.clicked.connect(self._select_symmetry_symm)
        self.starMapGui.rosettaModelSelectButton.clicked.connect(self._select_rosetta_modeleval)
        self.starMapGui.advancedConstraintsSetsSelectButton.clicked.connect(self._select_rosetta_constraints)
        self.starMapGui.userShellScriptsSelectButton.clicked.connect(self._select_user_shell_template)
        self.starMapGui.userRosettaScriptsSelectButton.clicked.connect(self._select_user_rosetta_template)
        self.starMapGui.userRosettaTemplatesCheckBox.clicked.connect(self._changed_user_rosettascript_event)
        self.starMapGui.analysisFscShowButton.clicked.connect(self._show_fsc_calculation)

        # execution tab
        self.starMapGui.executionLocalCoresEdit.setValidator(intValidator)
        self.starMapGui.executionRemoteCoresEdit.setValidator(intValidator)
        self.starMapGui.executionSaveButton.clicked.connect(self._save_starmap_settings)
        self.starMapGui.executionViewCxcScript.clicked.connect(self._view_chimerax_script)
        self.starMapGui.executionViewXmlScript.clicked.connect(self._view_rosetta_script)
        self.starMapGui.executionViewShScript.clicked.connect(self._view_bash_script)
        self.starMapGui.executionLocalEditButton.clicked.connect(self._edit_bash_script)
        self.starMapGui.executionRemoteEditButton.clicked.connect(self._edit_bash_script)
        self.starMapGui.executionRemoteExecuteButton.clicked.connect(self._submit_bash_script)
        self.starMapGui.executionLocalSaveButton.clicked.connect(self._save_bash_script)
        self.starMapGui.executionRemoteSaveButton.clicked.connect(self._save_bash_script)
        self.starMapGui.executionLocalRunScript.clicked.connect(self._exec_local_bash_script)

        # analysis tab
        self.starMapGui.analysisRosettaResultsExecuteButton.clicked.connect(self._exec_local_sort_rosetta_results)
        self.starMapGui.analysisFscModelMapCheckBox.setChecked(True)
        self.starMapGui.analysisFscLccCheckBox.setChecked(True)
        self.starMapGui.analysisFscLccCheckBox.clicked.connect(self._toggle_zscore_ui)
        self.starMapGui.analysisFscLccZscoreCheckBox.setChecked(True)
        self.starMapGui.analysisFscLccZscoreCheckBox.setEnabled(False)
        self.starMapGui.rosettaDensityMapSelectButton_2.clicked.connect(self._select_rosetta_densitymap)
        self.starMapGui.analysisResultPdbSelectButton.clicked.connect(self._select_result_pdb)
        self.starMapGui.analysisFscExecuteButton.clicked.connect(self._exec_stmrun_analysis)
        self.starMapGui.analysisCleanupButton.clicked.connect(self._exec_cleanup)

        # apix tab
        self.starMapGui.apixResultPdbSelectButton.clicked.connect(self._select_apix_pdb)
        self.starMapGui.apixDensityMapSelectButton.clicked.connect(self._select_apix_densitymap)
        self.starMapGui.apixAnisoCheckBox.setChecked(True)
        self.starMapGui.apixAnisoHelpButton.clicked.connect(self._help_aniso_check)
        self.starMapGui.apixSaveButton.clicked.connect(self._save_bash_apix_script)
        self.starMapGui.apixExecuteButton.clicked.connect(self._exec_local_bash_apix_script)

        # search templates
        from .config import data_location
        global STARMAP_TEMPLATES_DIR
        self.starMapGui.executionLocalTemplateComboBox.clear()
        self.starMapGui.executionLocalTemplateComboBox.setDuplicatesEnabled(False)
        files = os.listdir(data_location('templates', ''))
        #self._debug("using templates in: " + STARMAP_TEMPLATES_DIR)
        if STARMAP_TEMPLATES_DIR:
            try:
                files = os.listdir(str(STARMAP_TEMPLATES_DIR))
            except FileNotFoundError:
                QtWidgets.QMessageBox.warning(self.starMapGui.tabWidget, "StarMap warning",
                    "Directory from the environment variable STARMAP_TEMPLATES_DIR does not exist!\nUsing default templates!",
                    QtWidgets.QMessageBox.Ok)
        for file in sorted(files):
            if file.endswith("local.tmpl.sh"):
                self.localShellTemplates[str(file)] = os.path.join(STARMAP_TEMPLATES_DIR, file)
                self.starMapGui.executionLocalTemplateComboBox.addItem(file)
        #self._debug("local templates gui init = " + str(self.localShellTemplates))
        self.starMapGui.executionLocalTemplateComboBox.setCurrentIndex(0)
        self.starMapGui.executionRemoteTemplateComboBox.clear()
        self.starMapGui.executionRemoteTemplateComboBox.setDuplicatesEnabled(False)
        for file in sorted(files):
            if file.endswith("cluster.tmpl.sh"):
                self.remoteShellTemplates[str(file)] = os.path.join(STARMAP_TEMPLATES_DIR, file)
                self.starMapGui.executionRemoteTemplateComboBox.addItem(file)
        #self._debug("remote templates gui init = " + str(self.remoteShellTemplates))

        # submission commands
        self.starMapGui.executionRemoteSubmitComboBox.clear()
        self.starMapGui.executionRemoteSubmitComboBox.addItem("sbatch")
        self.starMapGui.executionRemoteSubmitComboBox.addItem("qsub")
        self.starMapGui.executionRemoteSubmitComboBox.addItem("bsub")
        self.starMapGui.executionRemoteSubmitComboBox.addItem("ts")
        self.starMapGui.executionRemoteTemplateComboBox.setCurrentIndex(0)

        # disable execution widgets
        self.starMapGui.executionTabWidget.setTabEnabled(1, False)
        self.starMapGui.executionTabWidget.setTabEnabled(2, False)

        # disable buttons
        self.starMapGui.executionLocalEditButton.setEnabled(False)
        self.starMapGui.executionLocalSaveButton.setEnabled(False)
        self.starMapGui.executionLocalRunScript.setEnabled(False)
        self.starMapGui.executionRemoteEditButton.setEnabled(False)
        self.starMapGui.executionRemoteSaveButton.setEnabled(False)
        self.starMapGui.executionRemoteExecuteButton.setEnabled(False)
        self.starMapGui.apixExecuteButton.setEnabled(False)

        # log buttons
        self.starMapGui.logViewEdit.setReadOnly(True)
        self.starMapGui.logStdoutButton.clicked.connect(self._show_stdout_log)
        self.starMapGui.logStderrButton.clicked.connect(self._show_stderr_log)

        # help buttons
        self.starMapGui.rosettaCxHelpButton.clicked.connect(self._help_rosetta_chimerax)
        self.starMapGui.rosettaDensityMapHelpButton.clicked.connect(self._help_rosetta_densitymap)
        self.starMapGui.rosettaResolutionHelpButton.clicked.connect(self._help_rosetta_resolution)
        self.starMapGui.rosettaResultsHelpButton.clicked.connect(self._help_rosetta_results)
        self.starMapGui.rosettaStrategyHelpButton.clicked.connect(self._help_rosetta_strategy)
        self.starMapGui.advancedSymmHelpButton.clicked.connect(self._help_rosetta_symmetry)
        self.starMapGui.rosettaModelHelpButton.clicked.connect(self._help_rosetta_model)
        #self.starMapGui.advancedConstraintsApHelpButton.clicked.connect(self._help_advanced_parameters)
        self.starMapGui.advancedConstraintsSetsHelpButton.clicked.connect(self._help_advanced_sets)
        self.starMapGui.advancedDensityWeightsHelpButton.clicked.connect(self._help_advanced_weights)
        self.starMapGui.userRosettaScriptsHelpButton.clicked.connect(self._help_user_rosetta)
        self.starMapGui.userShellScriptsHelpButton.clicked.connect(self._help_user_shell)
        self.starMapGui.userReplacementValuesScriptsHelpButton.clicked.connect(self._help_user_replacement_values)
        self.starMapGui.executionSaveHelpButton.clicked.connect(self._help_execution_save)
        self.starMapGui.executionViewCxcHelpButton.clicked.connect(self._help_execution_verify)
        self.starMapGui.executionViewXmlHelpButton.clicked.connect(self._help_execution_verify)
        self.starMapGui.executionViewShHelpButton.clicked.connect(self._help_execution_verify)
        self.starMapGui.executionLocalCoresHelpButton.clicked.connect(self._help_local_cores)
        self.starMapGui.executionLocalTemplateHelpButton.clicked.connect(self._help_local_templates)
        self.starMapGui.executionLocalSaveHelpButton.clicked.connect(self._help_local_save)
        self.starMapGui.executionLocalHelpButton.clicked.connect(self._help_local_execute)
        self.starMapGui.executionRemoteCoresHelpButton.clicked.connect(self._help_remote_cores)
        self.starMapGui.executionRemoteTemplateHelpButton.clicked.connect(self._help_remote_templates)
        self.starMapGui.executionRemoteSaveHelpButton.clicked.connect(self._help_remote_save)
        self.starMapGui.executionRemoteSubmitHelpButton.clicked.connect(self._help_remote_submit)
        self.starMapGui.executionRemoteExecuteHelpButton.clicked.connect(self._help_remote_execute)
        self.starMapGui.analysisRosettaResultsHelpButton.clicked.connect(self._help_analysis_rosetta)
        self.starMapGui.rosettaDensityMapHelpButton_2.clicked.connect(self._help_analysis_densmap)
        self.starMapGui.rosettaPdbResultHelpButton.clicked.connect(self._help_analysis_pdb)
        self.starMapGui.rosettaResolutionHelpButton_2.clicked.connect(self._help_analysis_resmap)
        self.starMapGui.analysisFscExecuteHelpButton.clicked.connect(self._help_analysis_fsc)
        self.starMapGui.analysisFscShowHelpButton.clicked.connect(self._help_analysis_fsc)
        self.starMapGui.analysisCleanupHelpButton.clicked.connect(self._help_cleanup)
        self.starMapGui.apixDensityMapHelpButton.clicked.connect(self._help_apix_densitymap)
        self.starMapGui.apixPdbResultHelpButton.clicked.connect(self._help_apix_pdb)
        self.starMapGui.apixResolutionHelpButton.clicked.connect(self._help_apix_resolution)
        self.starMapGui.apixSaveHelpButton.clicked.connect(self._help_apix_save)
        self.starMapGui.apixHelpButton.clicked.connect(self._help_apix_execute)
        self.starMapGui.logHelpButton.clicked.connect(self._help_log)
        self.starMapGui.howtoCiteButton.clicked.connect(self._help_cite)

        # hide development tab
        #self.starMapGui.tabWidget.removeTab(3)
        from .config import STARMAP_USER_ENV
        for k, v in STARMAP_USER_ENV.items():
            if str(v):
                self._run_cmd("stmset usrlbl" + str(k) + "=" + str(v))

        # copy values from Ui_qtStarMapWidget
        parent.setFixedHeight(640)
        parent.setFixedWidth(560)
        parent.updateGeometry()
        return

    # -------------------------------------------------------------------------
    def _index_changed_task_strategy_event(self):
        """Handle task strategy index events"""
        #self._debug(self.starMapGui.rosettaStrategyTaskBox.currentText())

        global TASK_FULL_REBUILD, TASK_MINIMUM_REBUILD, TASK_REFINEMENT_ONLY, TASK_TORSIAN_REFINEMENT
        task = self.starMapGui.rosettaStrategyTaskBox.currentText()

        if (task == _translate("qtStarMapWidget", TASK_REFINEMENT_ONLY)) or (task == _translate("qtStarMapWidget", TASK_TORSIAN_REFINEMENT)):
            self.starMapGui.rosettaStrategyValueBox.setDisabled(True)
            self.starMapGui.rosettaStrategyResiduesEdit.setDisabled(True)
        else:
            self.starMapGui.rosettaStrategyValueBox.setDisabled(False)
            if self.starMapGui.rosettaStrategyValueBox.currentText() == "user":
                self.starMapGui.rosettaStrategyResiduesEdit.setDisabled(False)
            self.set_value("models=20")

        if task == _translate("qtStarMapWidget", TASK_FULL_REBUILD):
            self.set_value("models=20")
        if task == _translate("qtStarMapWidget", TASK_MINIMUM_REBUILD):
            self.set_value("models=10")
        if task == _translate("qtStarMapWidget", TASK_REFINEMENT_ONLY):
            self.set_value("models=1")
        if task == _translate("qtStarMapWidget", TASK_TORSIAN_REFINEMENT):
            self.set_value("models=1")

        return

    # -------------------------------------------------------------------------
    def _index_changed_value_strategy_event(self):
        """Handle value strategy index events"""
        #self._debug(self.starMapGui.rosettaStrategyValueBox.currentText())
        if self.starMapGui.rosettaStrategyValueBox.currentText() == "user":
            self.starMapGui.rosettaStrategyResiduesEdit.setDisabled(False)
        else:
            self.starMapGui.rosettaStrategyResiduesEdit.setDisabled(True)
        return

    # -------------------------------------------------------------------------
    def _changed_mapres1_event(self):
        """Handle map resolution events"""
        self.set_value("mapres=" + self.starMapGui.rosettaResolutionEdit.text())
        return

    # -------------------------------------------------------------------------
    def _changed_mapres2_event(self):
        """Handle map resolution events"""
        self.set_value("mapres=" + self.starMapGui.analysisResolutionEdit.text())
        return

    # -------------------------------------------------------------------------
    def _changed_mapres3_event(self):
        """Handle map resolution events"""
        self.set_value("mapres=" + self.starMapGui.apixResolutionEdit.text())
        return

    # -------------------------------------------------------------------------
    def _changed_models_event(self):
        """Handle model events"""
        self.set_value("models=" + self.starMapGui.rosettaResultsEdit.text())
        return

    # -------------------------------------------------------------------------
    def _changed_model_evaluation_event(self):
        """Handle model eval events"""
        if self.starMapGui.rosettaModelCheckBox.isChecked():
            self.starMapGui.analysisDensityMapFileLabel.setText(self._short_path(self.rosettaModelEvalFile))
        else:
            self.starMapGui.analysisDensityMapFileLabel.setText(self._short_path(self.rosettaDensityMapFile))
        return

    # -------------------------------------------------------------------------
    def _changed_user_rosettascript_event(self):
        """Handle model events"""
        if self.starMapGui.userRosettaTemplatesCheckBox.isChecked():
            #self._debug("initializing user-defined rosetta script template")
            self._load_rosetta_script(self.stmUserSelRosettaFile)
            self.rosettaScriptString = self._replace_xml_tags(self.stmUserSelRosettaFile)
        else:
            #self._debug("initializing original rosetta script template")
            from .config import STARMAP_ROSETTA_SCRIPT
            self._load_rosetta_script(STARMAP_ROSETTA_SCRIPT)
            self.rosettaScriptString = self._replace_xml_tags(STARMAP_ROSETTA_SCRIPT)
        return

    # -------------------------------------------------------------------------
    def _save_file(self, suffixPattern='*', namePattern='.'):
        """Opens the file dialog"""
        filename = QtWidgets.QFileDialog.getSaveFileName(self.starMapGui.tabWidget, _translate("qtStarMapWidget", "Save file ..."),
                                                         directory=namePattern, initialFilter=suffixPattern)[0]
        if filename:
            #self._debug(filename)
            return filename
        self.logger.warning("No filename given!")
        return

    # -------------------------------------------------------------------------
    def _select_file(self, pattern='*'):
        """Opens the file dialog"""
        filename = QtWidgets.QFileDialog.getOpenFileName(self.starMapGui.tabWidget, 'Select file', '.', pattern)[0]
        if filename:
                #self._debug(filename)
            return filename
        self.logger.warning("No file selected!")
        return

    # -------------------------------------------------------------------------
    def _save_chimerax_pdb(self):
        """Saves the selected atoms in Chimerax as pdb file"""
        import string, random
        randomName = './' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8)) + '.pdb'
        self.rosettaCxSelPdbFile = self._save_file('*.pdb', randomName)
        if self.rosettaCxSelPdbFile:
            #self._debug(self.rosettaCxSelPdbFile)
            self._run_cmd("save " + self.rosettaCxSelPdbFile + " selectedOnly true")
            self.starMapGui.rosettaCxPdbFileLabel.setText(self._short_path(self.rosettaCxSelPdbFile))
        return

    # -------------------------------------------------------------------------
    def _save_starmap_settings(self):
        """Saves settings as .cxc file"""
        self.stmChimeraxFile = self._save_file('*.*', './run_starmap.cxc')
        if self.stmChimeraxFile:
            self.stmChimeraxFile = self.stmChimeraxFile.rsplit(".", 1)[0]  + ".cxc"
            self.stmRosettaFile = self.stmChimeraxFile.rsplit(".", 1)[0]  + ".xml"
            self.stmBashFile = self.stmChimeraxFile.rsplit(".", 1)[0]  + ".sh"
            target = open(self.stmChimeraxFile, 'w', newline='\n')
            target.write(self.get_values_script())
            target.close()
            self.set_value("runcxc=" + os.path.basename(self.stmChimeraxFile))
            self._save_fsc_script(self.stmChimeraxFile)
            self._save_rosetta_script()
            self._view_chimerax_script()
            self.starMapGui.executionSaveFileShLabel.setText("")
        return

    # -------------------------------------------------------------------------
    def _save_fsc_script(self, cxcFile):
        """Saves a default fsc starmap script"""
        if cxcFile:
            fscFile = cxcFile.rsplit(".", 1)[0]  + "_fsc.cxc"
            target = open(fscFile, 'w', newline='\n')
            target.write(self.get_values_script(True))
            target.close()
        return

    # -------------------------------------------------------------------------
    def _save_rosetta_script(self):
        """Saves rosetta as .xml file"""
        self.rosettaScriptString = self._replace_script_tags(self.rosettaScriptString)
        #self._debug(self.rosettaScriptString)

        if self.stmRosettaFile:
            target = open(self.stmRosettaFile, 'w', newline='\n')
            target.write(self.rosettaScriptString)
            target.close()
            # re-edit to add residues to the correct replaced file
            self.rosettaScriptString = self._replace_xml_tags(self.stmRosettaFile)
            target = open(self.stmRosettaFile, 'w', newline='\n')
            target.write(self.rosettaScriptString)
            target.close()
            self.set_value("runxml=" + os.path.basename(self.stmRosettaFile))
        #self._debug("re-initializing original Rosetta script template")
        #self._load_rosetta_script()
        self._changed_user_rosettascript_event()
        return

    # -------------------------------------------------------------------------
    def _save_bash_script(self):
        """Saves settings as .sh file"""
        # save modified edit field
        if not self.starMapGui.executionTextEdit.isReadOnly():
            #self.starMapGui.userRosettaTemplatesCheckBox
            self.starMapGui.executionTextEdit.setReadOnly(True)
            self.starMapGui.executionLocalEditButton.setText(_translate("qtStarMapWidget", "Edit"))
            self.starMapGui.executionRemoteEditButton.setText(_translate("qtStarMapWidget", "Edit"))
            self.starMapGui.executionLocalEditButton.setStyleSheet("background-color: rgb(255, 255, 255); color: rgb(0, 0, 0)")
            self.starMapGui.executionRemoteEditButton.setStyleSheet("background-color: rgb(255, 255, 255); color: rgb(0, 0, 0)")
            if self.stmBashFile:
                target = open(self.stmBashFile, 'w', newline='\n')
                target.write(self.starMapGui.executionTextEdit.toPlainText())
                target.close()
                return

        # generate file from template
        template = self.localShellTemplates[self.starMapGui.executionLocalTemplateComboBox.currentText()]
        if self.starMapGui.executionTabWidget.currentIndex() == 2:
            template = self.remoteShellTemplates[self.starMapGui.executionRemoteTemplateComboBox.currentText()]

        #self._debug("template = " + template)
        if os.path.isfile(template):
            file = open(template, 'r')
            templateScriptString = file.read()
            templateScriptString = self._replace_script_tags(templateScriptString)
            if self.stmBashFile:
                target = open(self.stmBashFile, 'w', newline='\n')
                target.write(templateScriptString)
                target.close()
                os.chmod(self.stmBashFile, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH)
                self.set_value("runsh=" + os.path.basename(self.stmBashFile))
                self._view_bash_script()
        else:
            QtWidgets.QMessageBox.warning(self.starMapGui.tabWidget, "StarMap warning",
                "Template file " + template + " does not exist!",
                QtWidgets.QMessageBox.Ok)

        return

    # -------------------------------------------------------------------------
    def _save_bash_apix_script(self):
        """Saves the bash script for local Rosetta calls"""
        from .config import ROSETTA_SCRIPTS_CMD, STARMAP_ROSETTA_APIX_SCRIPT

        self.stmBashApixFile = self._save_file('*.sh', './starmap_apix.sh')
        if not self.stmBashApixFile:
            return

        # generate apix xml with bash name
        apixFile = self.stmBashApixFile.rsplit(".", 1)[0]  + ".xml"
        self._save_apix_rosetta_script(apixFile)

        s = "#!/bin/sh\n"
        s += "$(which " + os.path.basename(ROSETTA_SCRIPTS_CMD) + ") \\\n"
        s += "  -parser:protocol \"" + os.path.basename(apixFile) + "\" \\\n"
        s += "  -edensity:mapfile \"" + os.path.basename(self.starMapGui.apixDensityMapFileLabel.text()) + "\" \\\n"
        s += "  -s \"" + os.path.basename(self.starMapGui.apixResultPdbFileLabel.text()) + "\" \\\n"
        s += "  -mapreso " + self.starMapGui.apixResolutionEdit.text() + " \\\n"
        s += "  -crystal_refine \\\n"
        s += "  -out:suffix \"_apix_bfactor\" \\\n"
        s += "  -out:no_nstruct_label \n"
        s += "echo --- StarMap: end of log ---\n"

        with open (self.stmBashApixFile, "w") as sFile:
            sFile.write(s)
        os.chmod(self.stmBashApixFile, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH)
        self.starMapGui.apixBashFileLabel.setText(os.path.basename(self.stmBashApixFile))
        self.starMapGui.apixExecuteButton.setEnabled(True)
        return

    # -------------------------------------------------------------------------
    def _save_apix_rosetta_script(self, apixFile):
        """Saves the Rosetta apix xml script"""
        from .config import STARMAP_ROSETTA_APIX_SCRIPT

        densMap = os.path.basename(self.starMapGui.apixDensityMapFileLabel.text())
        apixMap = densMap.rsplit(".", 1)[0]  + "_apix." + densMap.rsplit(".", 1)[1]
        s = ''
        with open(STARMAP_ROSETTA_APIX_SCRIPT) as f:
            s = f.read()
        s = s.replace("@@APIX_MAP@@", str(apixMap))

        if self.starMapGui.apixAnisoCheckBox.isChecked():
            s = s.replace("@@ANISO@@", "1")
        else:
            s = s.replace("@@ANISO@@", "0")

        with open (os.path.basename(apixFile), "w") as aFile:
            aFile.write(s)
        return

    # -------------------------------------------------------------------------
    def _edit_bash_script(self):
        """Sets the edit mode"""
        if self.starMapGui.executionLocalEditButton.text() == "Edit":
            self.starMapGui.executionTextEdit.setReadOnly(True)
            self.starMapGui.executionLocalEditButton.setText(_translate("qtStarMapWidget", "Cancel"))
            #self.starMapGui.executionLocalEditButton.setStyleSheet("background-color: rgb(255, 255, 255); color: rgb(0, 0, 0)")
            self.starMapGui.executionRemoteEditButton.setText(_translate("qtStarMapWidget", "Cancel"))
            #self.starMapGui.executionRemoteEditButton.setStyleSheet("background-color: rgb(255, 255, 255); color: rgb(0, 0, 0)")

        # enable edit mode
        if self.starMapGui.executionTextEdit.isReadOnly():
            self._view_text_file(self.stmBashFile)
            self.starMapGui.executionTextEdit.setReadOnly(False)
            self.starMapGui.executionLocalEditButton.setText(_translate("qtStarMapWidget", "Cancel"))
            self.starMapGui.executionLocalEditButton.setStyleSheet("background-color: rgb(255, 191, 0); color: rgb(0, 0, 0)")
            self.starMapGui.executionRemoteEditButton.setText(_translate("qtStarMapWidget", "Cancel"))
            self.starMapGui.executionRemoteEditButton.setStyleSheet("background-color: rgb(255, 191, 0); color: rgb(0, 0, 0)")
            return

        # disable edit mode
        if not self.starMapGui.executionTextEdit.isReadOnly():
            self.starMapGui.executionTextEdit.setReadOnly(True)
            self.starMapGui.executionLocalEditButton.setText(_translate("qtStarMapWidget", "Edit"))
            self.starMapGui.executionLocalEditButton.setStyleSheet("background-color: rgb(255, 255, 255); color: rgb(0, 0, 0)")
            self.starMapGui.executionRemoteEditButton.setText(_translate("qtStarMapWidget", "Edit"))
            self.starMapGui.executionRemoteEditButton.setStyleSheet("background-color: rgb(255, 255, 255); color: rgb(0, 0, 0)")
            self._view_text_file(self.stmBashFile)
        return

    # -------------------------------------------------------------------------
    def _toggle_zscore_ui(self):
        """Enabled/disabled zscore checkbox and handling"""
        if not self.starMapGui.analysisFscLccCheckBox.isChecked():
            self.starMapGui.analysisFscLccZscoreCheckBox.setEnabled(True)
            self.starMapGui.analysisFscLccZscoreCheckBox.setChecked(False)
        else:
            self.starMapGui.analysisFscLccZscoreCheckBox.setEnabled(False)
            self.starMapGui.analysisFscLccZscoreCheckBox.setChecked(True)
        return

    # -------------------------------------------------------------------------
    def _select_rosetta_constraints(self):
        """Selects the model evaluation input"""
        self.rosettaConsFile = self._select_file('*.cst')
        if self.rosettaConsFile:
            self.starMapGui.advancedConstraintsSetsFileLabel.setText(self._short_path(self.rosettaConsFile))
        return

    # -------------------------------------------------------------------------
    def _select_rosetta_modeleval(self):
        """Selects the model evaluation input"""
        self.rosettaModelEvalFile = self._select_file('*.mrc *.map')
        if self.rosettaModelEvalFile:
            self.starMapGui.rosettaModelFileLabel.setText(self._short_path(self.rosettaModelEvalFile))
            self.starMapGui.analysisDensityMapFileLabel.setText(self._short_path(self.rosettaModelEvalFile))
            self.starMapGui.rosettaModelCheckBox.setChecked(True)
        return

    # -------------------------------------------------------------------------
    def _select_rosetta_densitymap(self):
        """Selects the density map input"""
        self.rosettaDensityMapFile = self._select_file('*.mrc *.map')
        if self.rosettaDensityMapFile:
            self.set_value("densitymap=" + self.rosettaDensityMapFile)
        return

    # -------------------------------------------------------------------------
    def _select_apix_densitymap(self):
        """Selects the density map input"""
        mapfile = self._select_file('*.mrc *.map')
        if mapfile:
            self.starMapGui.apixDensityMapFileLabel.setText(self._short_path(mapfile))
        return

    # -------------------------------------------------------------------------
    def _select_user_shell_template(self):
        """Selects the user-defined shell template"""
        self.stmUserSelBashFile = self._select_file('*.sh')
        if self.stmUserSelBashFile:
            self.starMapGui.userShellScriptFileLabel.setText(self._short_path(self.stmUserSelBashFile))
            self._run_cmd("stmset usrtplsh=" + self.stmUserSelBashFile)
        return

    # -------------------------------------------------------------------------
    def _select_user_rosetta_template(self):
        """Selects the user-defined shell template"""
        self.stmUserSelRosettaFile = self._select_file('*.xml')
        if self.stmUserSelRosettaFile:
            #self.starMapGui.userShellScriptFileLabel.setText(self._short_path(self.stmUserSelRosettaFile))
            self._run_cmd("stmset usrtplro=" + self.stmUserSelRosettaFile)
        return

    # -------------------------------------------------------------------------
    def _select_chimerax_pdb(self):
        """Selects the chimerax pdb input"""
        self.rosettaCxSelPdbFile = self._select_file('*.pdb')
        if self.rosettaCxSelPdbFile:
            self.starMapGui.rosettaCxPdbFileLabel.setText(self._short_path(self.rosettaCxSelPdbFile))
        return

    # -------------------------------------------------------------------------
    def _select_apix_pdb(self):
        """Selects the apix pdb input"""
        pdbfile = self._select_file('*.pdb')
        if pdbfile:
            self.starMapGui.apixResultPdbFileLabel.setText(self._short_path(pdbfile))
        return

    # -------------------------------------------------------------------------
    def _select_symmetry_pdb(self):
        """Selects the symmetry pdb input"""
        self.symmPdbFile = self._select_file('*.pdb')
        if self.symmPdbFile:
            self.starMapGui.symmPdbDisplayLabel.setText(self._short_path(self.symmPdbFile))
            self.starMapGui.symmResultLabel.setText(_translate("qtStarMapWidget", "No result"))
        return

    # -------------------------------------------------------------------------
    def _select_symmetry_symm(self):
        """Selects the symmetry symm input"""
        self.rosettaSymmFile = self._select_file('*.symm')
        if self.rosettaSymmFile:
            self.starMapGui.advancedSymmFileLabel.setText(self._short_path(self.rosettaSymmFile))
        return

    # -------------------------------------------------------------------------
    def _select_result_pdb(self):
        """Selects the Rosetta result PDB"""
        self.rosettaResultPdbFile = self._select_file('*.pdb')
        if self.rosettaResultPdbFile:
            self.starMapGui.analysisResultPdbFileLabel.setText(self._short_path(self.rosettaResultPdbFile))
        return

    # -------------------------------------------------------------------------
    def _view_text_file(self, filename, readonly=True):
        """View read only file in gui"""
        font = QtGui.QFont('Monospace')
        font.setStyleHint(QtGui.QFont.TypeWriter) # Qt5
        font.setFixedPitch(True)
        font.setPointSize(10)
        metrics = QtGui.QFontMetrics(font)

        self.starMapGui.executionTextEdit.setFont(font)
        self.starMapGui.executionTextEdit.setTabStopWidth(metrics.width("  ")) # Qt5
        #self.starMapGui.executionTextEdit.setTabStopDistance(metrics.horizontalAdvance("  ")) # Qt6
        self.starMapGui.executionTextEdit.setReadOnly(readonly)
        self.starMapGui.executionTextEdit.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

        if os.path.exists(filename):
            text = open(filename).read()
            self.starMapGui.executionTextEdit.setPlainText(text)
        return

    # -------------------------------------------------------------------------
    def _view_chimerax_script(self):
        """Show the script in a scrollable area"""
        self._view_text_file(self.stmChimeraxFile)
        return

    # -------------------------------------------------------------------------
    def _view_rosetta_script(self):
        """Show the script in a scrollable area"""
        self._view_text_file(self.stmRosettaFile)
        return

    # -------------------------------------------------------------------------
    def _view_bash_script(self):
        """Show the script in a scrollable area"""
        self._view_text_file(self.stmBashFile)
        return

    # -------------------------------------------------------------------------
    def _view_bash_apix_script(self):
        """Show the script in a scrollable area"""
        self._view_text_file(self.stmBashApixFile)
        return

    # -------------------------------------------------------------------------
    def _exec_symm_check(self):
        """Executes the symmetry check and shows the result"""
        if not self.symmPdbFile:
            self._select_symmetry_pdb()
            if not self.symmPdbFile:
                return

        self.rosettaSymmFile = self.symmPdbFile.rsplit(".", 1)[0]  + ".symm"

        from .config import STARMAP_SYMMETRY_CMD, win_path_wrapper
        cmd = STARMAP_SYMMETRY_CMD.replace(' ', '\ ') + ' ' + self.starMapGui.symmOptionsEdit.text() + ' -p \"' + win_path_wrapper(self.symmPdbFile) + '\"'

        from .config import win_cmd_wrapper
        cmd = win_cmd_wrapper(cmd)
        if platform.system() == "Windows":
            scriptfile = self.symmPdbFile.rsplit(".", 1)[0]  + ".cmd"
            target = open(scriptfile, 'w', newline='\n')
            target.write(cmd)
            target.close()
            cmd = scriptfile
            self.logger.warning("If the symmetry check fails, run the symmetry script on Windows by double-clicking on it: " + scriptfile)

        #self._debug(cmd)
        procExe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.stdout, self.stderr = procExe.communicate()
        self.starMapGui.logViewEdit.setText(self.stderr)
        self.starMapGui.logStdoutButton.setEnabled(False)
        self.starMapGui.logStderrButton.setEnabled(False)
        self.starMapGui.tabWidget.setCurrentIndex(self.logTabIndex)
        log = self.starMapGui.logViewEdit.toPlainText()
        try:
            msg = log.split('\n')[-2]
        except Exception:
            msg = "Error: cannot parse log file"
        if not "Found" in msg:
            if "No symmetry found" in msg:
                msg = "No symmetry found"
            else:
                if not platform.system() == "Windows":
                    msg = "Error: check log for details"
                else:
                    if os.path.exists(self.rosettaSymmFile):
                        msg = "SYMM file generated"
                    else:
                        msg = "Error: check log for details"
        self.starMapGui.symmResultLabel.setText(msg)
        self.starMapGui.symmRosettaResultLabel.setText("See StarMap symmetry check")
        if os.path.exists(self.rosettaSymmFile):
            self.starMapGui.advancedSymmFileLabel.setText(self._short_path(self.rosettaSymmFile))
            self.starMapGui.advancedSymmCheckBox.setChecked(True)
        else:
            self.starMapGui.advancedSymmFileLabel.setText(_translate("qtStarMapWidget", "No file"))
            self.starMapGui.advancedSymmCheckBox.setChecked(False)
        return

    # -------------------------------------------------------------------------
    def _exec_rosetta_symm_check(self):
        """Executes the Rosetta symmetry check and shows the result"""
        if not self.symmPdbFile:
            self._select_symmetry_pdb()
            if not self.symmPdbFile:
                return

        self.rosettaSymmFile = self.symmPdbFile.rsplit(".", 1)[0]  + ".symm"

        from .config import ROSETTA_SYMMDEF_CMD, win_path_wrapper
        #cmd = '\"' + ROSETTA_SYMMDEF_CMD.replace(' ', '\ ') + '\" ' + self.starMapGui.symmRosettaOptionsEdit.text() + ' -p \"' + win_path_wrapper(self.symmPdbFile) + '\"'
        cmd = '/usr/bin/env perl ' + ROSETTA_SYMMDEF_CMD.replace(' ', '\ ') + ' ' + self.starMapGui.symmRosettaOptionsEdit.text() + ' -p \"' + win_path_wrapper(self.symmPdbFile) + '\"'

        self._debug(cmd)
        with open(self.rosettaSymmFile, "w") as outfile:
            procExe = subprocess.Popen(cmd, shell=True, stdout=outfile, stderr=subprocess.PIPE, universal_newlines=True)
            self.stdout, self.stderr = procExe.communicate()
        self.starMapGui.logViewEdit.setText(self.stderr)
        self.starMapGui.logStdoutButton.setEnabled(False)
        self.starMapGui.logStderrButton.setEnabled(False)
        self.starMapGui.tabWidget.setCurrentIndex(self.logTabIndex)
        log = self.starMapGui.logViewEdit.toPlainText()
        msg = log.split('\n')[-2]
        if not "Found" in msg:
            if "No symmetry found" in msg:
                msg = "No symmetry found"
            else:
                if os.path.getsize(self.rosettaSymmFile) > 0:
                    msg = "SYMM files: " + self._short_path(self.symmPdbFile.rsplit(".", 1)[0]  + "[.symm|_INPUT.pdb]")
                else:
                    msg = "Error: check log for details"
        self.starMapGui.symmRosettaResultLabel.setText(msg)
        self.starMapGui.symmResultLabel.setText("See Rosetta symmetry check")
        if os.path.exists(self.rosettaSymmFile):
            self.starMapGui.advancedSymmFileLabel.setText(self._short_path(self.rosettaSymmFile))
            self.starMapGui.advancedSymmCheckBox.setChecked(True)
            # set _INPUT as selected PDB
            inputSymmPdb = self.symmPdbFile.rsplit(".", 1)[0]  + "_INPUT.pdb"
            if os.path.exists(inputSymmPdb):
                self._run_cmd("stmset selfile=" + self._short_path(inputSymmPdb))
        else:
            self.starMapGui.advancedSymmFileLabel.setText(_translate("qtStarMapWidget", "No file"))
            self.starMapGui.advancedSymmCheckBox.setChecked(False)
        return

    # -------------------------------------------------------------------------
    def _exec_local_bash_script(self):
        """Executes the bash script for local Rosetta calls"""
        self._exec_external_script(self.stmBashFile)
        return

    # -------------------------------------------------------------------------
    def _exec_local_bash_apix_script(self):
        """Executes the bash script for local Rosetta calls"""
        self._exec_external_script(self.stmBashApixFile)
        return

    # -------------------------------------------------------------------------
    def _submit_bash_script(self):
        """Submits the bash script to a computing environment"""
        submit = self.starMapGui.executionRemoteSubmitComboBox.currentText()
        if submit == 'ts':
            submit += ' -L starmap -N ' + self.starMapGui.executionRemoteCoresEdit.text()
        self._exec_external_script(self.stmBashFile, submit)
        return

    # -------------------------------------------------------------------------
    def _exec_cleanup(self):
        """Cleanup necessary files"""
        if not self._check_supported():
            return

        filename = "cleanup.sh"
        s = "rm -f *.err *.out\n"
        s += "rm -f *_sort.*\n"
        s += "rm -f *_mm.sh *_res.sh *_zscore.sh\n"
        s += "rm -f *.sc\n"
        s += "rm -f cleanup.sh\n"
        filename = os.path.abspath(filename)
        self._write_bash_script(filename, s)
        self._exec_external_script_batchmode(filename)
        return

    # -------------------------------------------------------------------------
    def _exec_local_sort_rosetta_results(self):
        """Sorts the Rosetta results PDBs by FSC value"""
        if not self._check_supported():
            return

        spattern = os.path.basename(self.rosettaCxSelPdbFile).rsplit(".", 1)[0] + "_????.pdb"
        s = "names=`grep mask " + spattern + " | grep -v starmap_result | sort -r -k5 | cut -f1 -d':'`\n"
        s += "i=1\n"
        s += "for name in $names; do\n"
        s += "  echo mv $name starmap_result_$(printf \"%0004d\" $i).pdb\n"
        s += "  mv $name starmap_result_$(printf \"%0004d\" $i).pdb\n"
        s += "  i=$((i+1))\n"
        s += "done\n"
        filename = self.rosettaCxSelPdbFile.rsplit(".", 1)[0]  + "_sort.sh"
        filename = os.path.abspath(filename)
        self._write_bash_script(filename, s)
        self._exec_external_script(filename)
        return


    # -------------------------------------------------------------------------
    def _exec_stmrun_analysis(self):
        """Runs the full fsc analysis"""
        self.starMapGui.analysisFscShowButton.setStyleSheet("background-color: rgb(255, 191, 0); color: rgb(0, 0, 0)")
        self.starMapGui.analysisFscExecuteButton.update()
        if self.starMapGui.analysisFscModelMapCheckBox.isChecked():
            self._run_cmd("stmrunfsc")
        if self.starMapGui.analysisFscLccCheckBox.isChecked():
            self._run_cmd("stmrunlcc")
        if self.starMapGui.analysisFscLccZscoreCheckBox.isChecked():
            self._run_cmd("stmrunzsc")
        return

    # -------------------------------------------------------------------------
    def _exec_local_fsc_calculation(self, batchmode=False, fsc=False, lcc=False, zsc=False):
        """Executes Rosetta FSC calculation"""
        if not self._check_supported():
            return

        resultPdbName = os.path.basename(os.path.realpath(self.starMapGui.analysisResultPdbFileLabel.text()))
        #self._debug("resultPdbName=" + resultPdbName)

        from .config import ROSETTA_DENSITY_CMD
        s = "$(which " + os.path.basename(ROSETTA_DENSITY_CMD) + ")"
        if self.starMapGui.executionFullPathBox.isChecked():
            s = ROSETTA_DENSITY_CMD
        s += " -s " + resultPdbName
        s += " -mapfile " + os.path.basename(self.starMapGui.analysisDensityMapFileLabel.text())
        s += " -mapreso " + self.starMapGui.analysisResolutionEdit.text()
        s += " -cryoem_scatterers"

        if fsc:
            scriptname = os.path.basename(resultPdbName.rsplit(".", 1)[0] + "_fsc_mm.sh")
            self.fscModelMapCsvFile = os.path.basename(resultPdbName.rsplit(".", 1)[0] + "_fsc_mm.csv")
            s += " -nresbins 200 -hires 0.01 -verbose -mask_resolution 10\n"
        perres_applied = False
        if lcc:
            scriptname = os.path.basename(resultPdbName.rsplit(".", 1)[0] + "_lcc_res.sh")
            s += " -perres -ignore_unrecognized_res -out:levels protocols.hybridization.FragmentBiasAssigner:999\n"
            perres_applied = True
        if zsc:
            scriptname = os.path.basename(resultPdbName.rsplit(".", 1)[0] + "_lcc_res_zscore.sh")
            if not perres_applied:
                s += " -perres -ignore_unrecognized_res -out:levels protocols.hybridization.FragmentBiasAssigner:999\n"
        if not fsc:
            s += "myself=`basename $0`\n"
            s += "mylog=${myself%.sh}.out\n"
            s += "grep FragmentBias ${mylog} | grep -v init | grep -v Probs_ | grep -v rsn | grep -v Size | cut -d':' -f2 >fragmentbias.tmp\n"
            s += "grep PERRESCC ${mylog} | cut -d' ' -f4- >prerescc.tmp\n"
            s += "paste prerescc.tmp fragmentbias.tmp | tr '\t' ' ' >zscores.tmp\n"
            s += "cat zscores.tmp | tr -s ' ' >zscores_combined.csv\n"
            s += "rm -f fragmentbias.tmp prerescc.tmp zscores.tmp\n"

        s += "echo --- StarMap: end of log ---\n"
        self._write_bash_script(scriptname, s)
        if not batchmode:
            self._exec_external_script(scriptname)
        else:
            self._exec_external_script_batchmode(scriptname)

        self.starMapGui.analysisFscShowButton.setEnabled(True)
        return

    # -------------------------------------------------------------------------
    def _make_fsc_csv(self):
        """Generate FSC CSV files"""
        realname = os.path.realpath(self.starMapGui.analysisResultPdbFileLabel.text())
        fscname = os.path.basename(realname.rsplit(".", 1)[0] + "_fsc_mm.out")
        if not os.path.isfile(fscname):
            QtWidgets.QMessageBox.warning(self.starMapGui.tabWidget, "StarMap warning",
            "File " + fscname + " does not exist!\nPlease run analysis!",
            QtWidgets.QMessageBox.Ok)
            return

        lines = [line.rstrip('\n') for line in open(fscname)]
        with open(self.fscModelMapCsvFile, 'w', newline='\n') as f:
            for line in lines:
                if line.find("density_tools:") != -1:
                    tok = line.split()
                    try:
                        float(tok[1])
                        f.write(tok[1] + ' ' + tok[8] + '\n')
                    except ValueError:
                        dummy = 1
        f.close()

        self.fscCsvFiles = {}
        self.fscCsvFiles['0'] = self.fscModelMapCsvFile
        self._save_fsc_veusz(fsc=True)
        return

    # -------------------------------------------------------------------------
    def _make_lcc_csv(self):
        """Generate LCC CVS files"""
        realname = os.path.realpath(self.starMapGui.analysisResultPdbFileLabel.text())
        lccname = os.path.basename(realname.rsplit(".", 1)[0] + "_lcc_res.out")
        lines = [line.rstrip('\n') for line in open(lccname)]
        fscLccCsvFiles = {}

        for line in lines:
            if line.find("PERRESCC") != -1:
                tok = line.split()
                fscLccCsvFiles[tok[4]] = lccname.rsplit(".", 1)[0] + '_' + tok[4] + ".csv"

        #self._debug("generating csv file(s):\n" + str(fscLccCsvFiles))
        for chain in fscLccCsvFiles:
            with open(fscLccCsvFiles[chain], 'w', newline='\n') as f:
                for line in lines:
                    if line.find("PERRESCC") != -1:
                        tok = line.split()
                        if chain == tok[4]:
                            f.write(tok[5] + ' ' + tok[6] + '\n')
            f.close()

        self.fscCsvFiles = {}
        self.fscCsvFiles = fscLccCsvFiles.copy()
        self._save_fsc_veusz(lcc=True)
        self._save_fsc_veusz(zsc=True)
        return

    # -------------------------------------------------------------------------
    def _make_zsc_csv(self):
        """Generate LCC zscore CVS files"""
        realname = os.path.realpath(self.starMapGui.analysisResultPdbFileLabel.text())
        lccname = os.path.basename(realname.rsplit(".", 1)[0] + "_lcc_res.out")
        zscname = os.path.basename(realname.rsplit(".", 1)[0] + "_lcc_res_zscore.out")
        if not os.path.isfile(zscname):
            try:
                if os.path.isfile(lccname):
                    from shutil import copyfile
                    copyfile(lccname, zscname)
            except OSError:
                self._debug("assuming zsc direct run")

        lines = [line.rstrip('\n') for line in open(zscname)]
        fscLccZscoreCsvFiles = {}

        for line in lines:
            if line.find("PERRESCC") != -1:
                tok = line.split()
                fscLccZscoreCsvFiles[tok[4]] = zscname.rsplit(".", 1)[0] + '_' + tok[4] + ".csv"

        #self._debug("generating csv file(s):\n" + str(fscLccZscoreCsvFiles))
        for chain in fscLccZscoreCsvFiles:
            with open(fscLccZscoreCsvFiles[chain], 'w', newline='\n') as f:
                for line in lines:
                    if line.find("PERRESCC") != -1:
                        tok = line.split()
                        if chain == tok[4]:
                            f.write(tok[5] + ' ' + tok[7] + '\n')
            f.close()

        self.fscCsvFiles = {}
        self.fscCsvFiles = fscLccZscoreCsvFiles.copy()
        self._make_zscore_color_cxc(lccname)
        self._save_fsc_veusz(zsc=True)
        return

    # -------------------------------------------------------------------------
    def _obsolete_make_lcc_color_com(self, fscname):
        """Generate a color file for Chimera 1.x"""
        chimeraColorFile = fscname.rsplit(".", 1)[0] + ".com"
        lines = [line.rstrip('\n') for line in open(fscname)]
        with open(chimeraColorFile, 'w', newline='\n') as f:
            for line in lines:
                if line.find("PERRESCC") != -1:
                    tok = line.split()
                    f.write("setattr r ec " + tok[6] + " :" + tok[5] + "." + tok[4]  + '@CA\n')
            f.write("range ec -1 red -0.5 cyan 0 blue\n")
            f.write("start Render by Attribute\n")
        f.close()
        return

    # -------------------------------------------------------------------------
    def _make_zscore_color_cxc(self, fscname):
        """Generate a color file for ChimeraX"""
        csvfile = "zscores_combined.csv"

        colfile = fscname.rsplit(".", 1)[0] + "_zscore.cxc"
        self._write_zscore_color_cxc(csvfile, colfile, 4, "zscore")

        colfile = fscname.rsplit(".", 1)[0] + "_zdensity.cxc"
        self._write_zscore_color_cxc(csvfile, colfile, 5, "zdensity")

        colfile = fscname.rsplit(".", 1)[0] + "_zneighborhood.cxc"
        self._write_zscore_color_cxc(csvfile, colfile, 6, "zneighborhood")

        colfile = fscname.rsplit(".", 1)[0] + "_zrama.cxc"
        self._write_zscore_color_cxc(csvfile, colfile, 7, "zrama")

        colfile = fscname.rsplit(".", 1)[0] + "_zbondstrain.cxc"
        self._write_zscore_color_cxc(csvfile, colfile, 8, "zbondstrain")
        return

    # -------------------------------------------------------------------------
    def _write_zscore_color_cxc(self, csvfile, colfile, zcol, attrname):
        """Generate a color file for ChimeraX"""
        lines = [line.rstrip('\n') for line in open(csvfile)]
        with open(colfile, 'w', newline='\n') as f:
            f.write("hide atoms\n")
            f.write("show cartoons\n")
            try:
                for line in lines:
                    tok = line.split()
                    f.write("setattr " + '/' + tok[1] + ':' + tok[2] + ' res ' + attrname + ' ' + tok[zcol] + ' create true\n')
                f.write("color byattribute " + attrname + " palette -1,red:-0.5,white:0,gold\n")
            except IndexError:
                self.logger.error("Error generating file: " + str(colfile) + "\nIs there an error message in the *.out files?")
        f.close()
        return

    # -------------------------------------------------------------------------
    def _show_fsc_calculation(self):
        """Visualizes the FSC calculation"""
        self.starMapGui.analysisFscShowButton.setStyleSheet("background-color: rgb(255, 255, 255); color: rgb(0, 0, 0)")
        import numpy
        import pyqtgraph.exporters
        titlelabel = "Default Title"
        xlabel = "1/res"
        ylabel = "FSC_maskedmodelmap"
        if self.starMapGui.analysisFscModelMapCheckBox.isChecked():
            self._make_fsc_csv()
            titlelabel = "FSC between selected model and map"
        else:
            QtWidgets.QMessageBox.information(self.starMapGui.tabWidget, "StarMap info",
            "Preview is only available for the FSC calculation!  \nPlease use Veusz to view the other graphs.",
            QtWidgets.QMessageBox.Ok)
            return

        for chain in self.fscCsvFiles:
            if os.path.getsize(self.fscCsvFiles[chain]) <= 0:
                self.logger.error("Data file is empty!\nPlease check log if the execution is finished!\nIt should contain the last line:\n--- StarMap: end of log ---")
                return
            x, y = numpy.loadtxt(self.fscCsvFiles[chain], usecols=(0, 1), unpack=True)
            plt = pyqtgraph.plot(x, y, title=titlelabel, pen='r', background='w', left=ylabel, bottom=xlabel)
            pyqtgraph.exporters.ImageExporter(plt.plotItem)
            #exporter = pyqtgraph.exporters.ImageExporter(plt.plotItem)
            #exporter.export(self.fscCsvFiles[chain].rsplit(".", 1)[0] + ".png")

        return

    # -------------------------------------------------------------------------
    def _save_fsc_veusz(self, fsc=False, lcc=False, zsc=False):
        """Generates a Veusz project file"""
        filename = os.path.basename(self.starMapGui.analysisResultPdbFileLabel.text())
        vszfilename = filename.rsplit(".", 1)[0] + "_fsc_mm.vsz"
        if fsc:
            vszfilename = filename.rsplit(".", 1)[0] + "_fsc_mm.vsz"
        if lcc:
            vszfilename = filename.rsplit(".", 1)[0] + "_lcc_res.vsz"
        if zsc:
            vszfilename = filename.rsplit(".", 1)[0] + "_lcc_res_zscore.vsz"
        with open(vszfilename, 'w', newline='\n') as f:
            f.write("# generated by StarMap\n")
            f.write("AddImportPath(u'" + str(os.getcwd()) + "')\n")
            for chain in self.fscCsvFiles:
                f.write("ImportFileCSV(u'" + self.fscCsvFiles[chain] + "', delimiter=' ', linked=True, dsprefix=u'1', dssuffix=u'" + self.fscCsvFiles[chain] + "')\n")
                f.write("Add('page', name='page" + str(chain) + "', autoadd=False)\n")
                f.write("To('page" + str(chain) + "')\n")
                f.write("Add('graph', name='graph" + str(chain) + "', autoadd=False)\n")
                f.write("To('graph" + str(chain) + "')\n")
                f.write("Add('axis', name='x', autoadd=False)\n")
                f.write("Add('axis', name='y', autoadd=False)\n")
                f.write("To('y')\n")
                f.write("Set('direction', 'vertical')\n")
                f.write("To('..')\n")
                f.write("Add('xy', name='xy1', autoadd=False)\n")
                f.write("To('xy1')\n")
                f.write("Set('xData', u'1col1" + self.fscCsvFiles[chain] + "')\n")
                f.write("Set('yData', u'1col2" + self.fscCsvFiles[chain] + "')\n")
                f.write("To('..')\n")
                f.write("To('..')\n")
                f.write("To('..')\n")
            f.close()
        #self._debug("generated Veusz script: " + f.name)
        return

    # -------------------------------------------------------------------------
    def cxc_exec_fsc_calc(self):
        """Executes the FSC calculation as ChimeraX script"""
        self._exec_local_fsc_calculation(True, fsc=True)
        self._make_fsc_csv()
        return

    # -------------------------------------------------------------------------
    def cxc_exec_lcc_calc(self):
        """Executes the LCC calculation as ChimeraX script"""
        self._exec_local_fsc_calculation(True, lcc=True)
        self._make_lcc_csv()
        self._make_zsc_csv()
        return

    # -------------------------------------------------------------------------
    def cxc_exec_zsc_calc(self):
        """Executes the LCC zscore calculation as ChimeraX script"""
        self._exec_local_fsc_calculation(True, lcc=True, zsc=True)
        self._make_zsc_csv()
        return

    # -------------------------------------------------------------------------
    def _load_rosetta_script(self, scriptfile=""):
        """Loads the Rosetta script template"""
        from pyparsing import ParseException
        from .config import STARMAP_ROSETTA_SCRIPT
        from .rosettascripts import reset
        if not scriptfile:
            scriptfile = STARMAP_ROSETTA_SCRIPT
        try:
            #self._debug("loading script: " + scriptfile)
            parsedScript = script.parseFile(scriptfile)
            tags = parsedScript.asList()
            reset()
            self.rosettaScriptString = asXmlList(tags)
        except ParseException:
            self.logger.error("Error parsing the rosetta script template!")
        return

    # -------------------------------------------------------------------------
    def _help_symm_select(self):
        """Run StarMap help with section"""
        self._help("symmetry_tab#input-file")
        return

    # -------------------------------------------------------------------------
    def _help_symm_check(self):
        """Run StarMap help with section"""
        self._help("symmetry_tab#starmap-symmetry-check")
        return

    # -------------------------------------------------------------------------
    def _help_rosetta_symm_check(self):
        """Run StarMap help with section"""
        self._help("symmetry_tab#rosetta-symmetry-check")
        return

    # -------------------------------------------------------------------------
    def _help_rosetta_symmetry(self):
        """Run StarMap help with section"""
        self._help("advanced_tab#symmetry")
        return

    # -------------------------------------------------------------------------
    def _help_rosetta_chimerax(self):
        """Run StarMap help with section"""
        self._help("rosetta_tab#chimerax")
        return

    # -------------------------------------------------------------------------
    def _help_rosetta_densitymap(self):
        """Run StarMap help with section"""
        self._help("rosetta_tab#density")
        return

    # -------------------------------------------------------------------------
    def _help_rosetta_strategy(self):
        """Run StarMap help with section"""
        self._help("rosetta_tab#strategy")
        return

    # -------------------------------------------------------------------------
    def _help_rosetta_resolution(self):
        """Run StarMap help with section"""
        self._help("rosetta_tab#resolution")
        return

    # -------------------------------------------------------------------------
    def _help_rosetta_results(self):
        """Run StarMap help with section"""
        self._help("rosetta_tab#results")
        return

    # -------------------------------------------------------------------------
    def _help_rosetta_model(self):
        """Run StarMap help with section"""
        self._help("advanced_tab#model-evaluation")
        return

    # -------------------------------------------------------------------------
    def _help_advanced_parameters(self):
        """Run StarMap help with section"""
        self._help("advanced_tab#parameters")
        return

    # -------------------------------------------------------------------------
    def _help_advanced_sets(self):
        """Run StarMap help with section"""
        self._help("advanced_tab#sets")
        return

    # -------------------------------------------------------------------------
    def _help_advanced_weights(self):
        """Run StarMap help with section"""
        self._help("advanced_tab#versions")
        return

    # -------------------------------------------------------------------------
    def _help_execution_save(self):
        """Run StarMap help with section"""
        self._help("execute_tab#save-scripts")
        return

    # -------------------------------------------------------------------------
    def _help_execution_verify(self):
        """Run StarMap help with section"""
        self._help("execute_tab#verify-scripts")
        return

    # -------------------------------------------------------------------------
    def _help_local_cores(self):
        """Run StarMap help with section"""
        self._help("execute_tab#use-local-cores")
        return

    # -------------------------------------------------------------------------
    def _help_local_templates(self):
        """Run StarMap help with section"""
        self._help("execute_tab#local-script-templates")
        return

    # -------------------------------------------------------------------------
    def _help_local_save(self):
        """Run StarMap help with section"""
        self._help("execute_tab#save-local-script")
        return

    # -------------------------------------------------------------------------
    def _help_local_execute(self):
        """Run StarMap help with section"""
        self._help("execute_tab#execute-local-script")
        return

    # -------------------------------------------------------------------------
    def _help_remote_cores(self):
        """Run StarMap help with section"""
        self._help("execute_tab#use-cores")
        return

    # -------------------------------------------------------------------------
    def _help_remote_templates(self):
        """Run StarMap help with section"""
        self._help("execute_tab#submission-script-templates")
        return

    # -------------------------------------------------------------------------
    def _help_remote_save(self):
        """Run StarMap help with section"""
        self._help("execute_tab#save-submission-script")
        return

    # -------------------------------------------------------------------------
    def _help_remote_submit(self):
        """Run StarMap help with section"""
        self._help("execute_tab#submission-command")
        return

    # -------------------------------------------------------------------------
    def _help_remote_execute(self):
        """Run StarMap help with section"""
        self._help("execute_tab#submit-script")
        return

    # -------------------------------------------------------------------------
    def _help_apix_resolution(self):
        """Run StarMap help with section"""
        self._help("apix_tab#resolution")
        return

    # -------------------------------------------------------------------------
    def _help_apix_densitymap(self):
        """Run StarMap help with section"""
        self._help("apix_tab#density")
        return

    # -------------------------------------------------------------------------
    def _help_apix_pdb(self):
        """Run StarMap help with section"""
        self._help("apix_tab#rosetta-result-pdb")
        return

    # -------------------------------------------------------------------------
    def _help_apix_save(self):
        """Run StarMap help with section"""
        self._help("apix_tab#save-bash-script")
        return

    # -------------------------------------------------------------------------
    def _help_apix_execute(self):
        """Run StarMap help with section"""
        self._help("apix_tab#execute-apix-script")
        return

    # -------------------------------------------------------------------------
    def _help_user_rosetta(self):
        """Run StarMap help with section"""
        self._help("user_tab#rosetta")
        return

    # -------------------------------------------------------------------------
    def _help_user_shell(self):
        """Run StarMap help with section"""
        self._help("user_tab#shell")
        return

    # -------------------------------------------------------------------------
    def _help_user_replacement_values(self):
        """Run StarMap help with section"""
        self._help("user_tab#replacement-values")
        return

    # -------------------------------------------------------------------------
    def _help_analysis_rosetta(self):
        """Run StarMap help with section"""
        self._help("analysis_tab#rosetta-results")
        return

    # -------------------------------------------------------------------------
    def _help_analysis_pdb(self):
        """Run StarMap help with section"""
        self._help("analysis_tab#rosetta-result-pdb")
        return

    # -------------------------------------------------------------------------
    def _help_analysis_resmap(self):
        """Run StarMap help with section"""
        self._help("analysis_tab#resolution")
        return

    # -------------------------------------------------------------------------
    def _help_analysis_densmap(self):
        """Run StarMap help with section"""
        self._help("analysis_tab#density")
        return

    # -------------------------------------------------------------------------
    def _help_analysis_fsc(self):
        """Run StarMap help with section"""
        self._help("analysis_tab#graphs")
        return

    # -------------------------------------------------------------------------
    def _help_aniso_check(self):
        """Run StarMap help with section"""
        self._help("apix_tab#map-correction")
        return

    # -------------------------------------------------------------------------
    def _help_cleanup(self):
        """Run StarMap help with section"""
        self._help("analysis_tab#cleanup")
        return

    # -------------------------------------------------------------------------
    def _help_log(self):
        """Run StarMap help with section"""
        self._help("log_tab#log-tab")
        return

    # -------------------------------------------------------------------------
    def _help_cite(self):
        """Run StarMap help with section"""
        self._help("starmap#starmap-citations")
        return

    # -------------------------------------------------------------------------
    def _debug(self, msg):
        """TODO Comment before production release"""
        self.logger.info("starmap> " + str(msg))
        return

    # -------------------------------------------------------------------------
    def _help(self, section):
        """Show help on topic"""
        self._run_cmd("stmhelp section=" + section)
        return

    # -------------------------------------------------------------------------
    def _check_supported(self):
        """Sorts the Rosetta results PDBs by FSC value"""
        if platform.system() == "Windows":
            QtWidgets.QMessageBox.warning(self.starMapGui.tabWidget, "StarMap warning",
                                          "This functionality is not supported on Windows!",
                                          QtWidgets.QMessageBox.Ok)
            return False
        return True

    # -------------------------------------------------------------------------
    def _show_stdout_log(self):
        """Show stdout contents in log tab"""
        if not self.stdout:
            return
        with open(self.stdout, "r") as f:
            f.seek (0, 2)
            fsize = f.tell()
            f.seek (max (fsize-20000, 0), 0)
            self.starMapGui.logViewEdit.setText(f.read())
            self.starMapGui.logViewEdit.moveCursor(QtGui.QTextCursor.End)
        return

    # -------------------------------------------------------------------------
    def _show_stderr_log(self):
        """Show stderr contents in log tab"""
        if not self.stderr:
            return
        file = open(self.stderr, 'r')
        self.starMapGui.logViewEdit.setText(file.read())
        self.starMapGui.logViewEdit.moveCursor(QtGui.QTextCursor.End)
        return

    # -------------------------------------------------------------------------
    def _run_cmd(self, cmd):
        """Run a ChimeraX command"""
        run(self.session, cmd)
        return

    # -------------------------------------------------------------------------
    def _short_path(self, fname=''):
        """Display dots when path is longer than 60 chars"""
        if len(fname) > 60:
            return fname[:15] + "..." + os.sep + os.path.basename(fname)
        return fname

    # -------------------------------------------------------------------------
    def _write_bash_script(self, filename, content):
        """Executes or submits the the given script as thread"""
        with open (filename, "w", newline='\n') as sFile:
            sFile.write("#!/bin/sh\n")
            sFile.write(content)
        os.chmod(filename, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH)
        return

    # -------------------------------------------------------------------------
    def _exec_external_script(self, scriptfile, submit=''):
        """Executes or submits the the given script as thread"""
        if not os.path.exists(scriptfile):
            QtWidgets.QMessageBox.warning(self.starMapGui.tabWidget, "StarMap warning",
                                          "File does not exist: " + scriptfile,
                                          QtWidgets.QMessageBox.Ok)
            return

        self.starMapGui.logStdoutButton.setEnabled(True)
        self.starMapGui.logStderrButton.setEnabled(True)
        execThread = ExternalBashThread()
        execThread.set_script(os.path.abspath(scriptfile), submit)
        execThread.start()
        execThread.join()
        self.stdout = execThread.stdout
        self.stderr = execThread.stderr
        self.starMapGui.logViewEdit.setText(self.stdout)
        self.starMapGui.tabWidget.setCurrentIndex(self.logTabIndex)
        return

    # -------------------------------------------------------------------------
    def _exec_external_script_batchmode(self, cmd):
        """Executes or submits the the given script as thread"""
        o = open(cmd.rsplit(".", 1)[0]  + ".out", 'w', newline='\n')
        e = open(cmd.rsplit(".", 1)[0]  + ".err", 'w', newline='\n')
        procExe = subprocess.Popen(os.path.abspath(cmd), shell=True, stdout=o, stderr=e, universal_newlines=True)
        procExe.wait()
        o.close()
        e.close()
        return

    # -------------------------------------------------------------------------
    def set_value(self, value):
        """Expects a value in form name=value as string"""
        #self._debug(value)
        if not value.find('='):
            return

        qname, qval = value.split("=")
        # bool values
        if qname == "symm":
            if qval == "True":
                self.starMapGui.advancedSymmCheckBox.setChecked(True)
            else:
                self.starMapGui.advancedSymmCheckBox.setChecked(False)
        if qname == "symmhelix":
            if qval == "True":
                self.starMapGui.advancedSymmHelixCheckBox.setChecked(True)
            else:
                self.starMapGui.advancedSymmHelixCheckBox.setChecked(False)
        if qname == "half2":
            if qval == "True":
                self.starMapGui.rosettaModelCheckBox.setChecked(True)
            else:
                self.starMapGui.rosettaModelCheckBox.setChecked(False)
        if qname == "consset":
            if qval == "True":
                self.starMapGui.advancedConstraintsSetsFileCheckBox.setChecked(True)
            else:
                self.starMapGui.advancedConstraintsSetsFileCheckBox.setChecked(False)
        if qname == "fullpath":
            if qval == "True":
                self.starMapGui.executionFullPathBox.setChecked(True)
            else:
                self.starMapGui.executionFullPathBox.setChecked(False)
        # files
        if qname == "symmfile" and qval:
            self.starMapGui.advancedSymmFileLabel.setText(self._short_path(qval))
            self.rosettaSymmFile = qval
        if qname == "symmpdb" and qval:
            self.starMapGui.symmPdbDisplayLabel.setText(self._short_path(qval))
            self.symmPdbFile = qval
        if qname == "selfile" and qval:
            self.starMapGui.rosettaCxPdbFileLabel.setText(self._short_path(qval))
            self.rosettaCxSelPdbFile = qval
        if qname == "densitymap" and qval:
            self.starMapGui.rosettaDensityMapFileLabel.setText(self._short_path(qval))
            self.starMapGui.analysisDensityMapFileLabel.setText(self._short_path(qval))
            self.starMapGui.apixDensityMapFileLabel.setText(self._short_path(qval))
            self.rosettaDensityMapFile = qval
        if qname == "half2file" and qval:
            self.starMapGui.rosettaModelFileLabel.setText(self._short_path(qval))
            self.starMapGui.analysisDensityMapFileLabel.setText(self._short_path(qval))
            self.rosettaModelEvalFile = qval
        if qname == "consfile" and qval:
            self.starMapGui.advancedConstraintsSetsFileLabel.setText(self._short_path(qval))
            self.rosettaConsFile = qval
        # dependent values
        if qname == "task":
            self.starMapGui.rosettaStrategyTaskBox.setCurrentIndex(int(qval))
        if qname == "strategy":
            self.starMapGui.rosettaStrategyValueBox.setCurrentIndex(int(qval))
        if qname == "selres" and qval:
            self.starMapGui.rosettaStrategyResiduesEdit.setText(qval)
        # independent values
        if qname == "mapres":
            self.starMapGui.rosettaResolutionEdit.setText(qval)
            self.starMapGui.analysisResolutionEdit.setText(qval)
            self.starMapGui.apixResolutionEdit.setText(qval)
        if qname == "models":
            self.starMapGui.rosettaResultsEdit.setText(qval)
            if os.cpu_count() < int(qval)+1:
                self.starMapGui.executionLocalCoresEdit.setText(str(os.cpu_count()))
            else:
                self.starMapGui.executionLocalCoresEdit.setText(str(int(qval)+1))
            # Darwin has only static Rosetta executables for local execution
            if platform.system() == "Darwin":
                self.starMapGui.executionLocalCoresEdit.setText(str(1))
            self.starMapGui.executionRemoteCoresEdit.setText(str(int(qval)+1))
        # saved scripts
        if qname == "runcxc":
            if os.path.exists(qval):
                self.starMapGui.executionSaveFileCxcLabel.setText(self._short_path(qval))
                self.stmChimeraxFile = qval
                self._view_chimerax_script()
        if qname == "runxml":
            if os.path.exists(qval):
                self.starMapGui.executionSaveFileXmlLabel.setText(self._short_path(qval))
                self.stmRosettaFile = qval
                self.starMapGui.executionLocalSaveButton.setEnabled(True)
                self.starMapGui.executionRemoteSaveButton.setEnabled(True)
                self.starMapGui.executionTabWidget.setTabEnabled(1, True)
                self.starMapGui.executionTabWidget.setTabEnabled(2, True)
                self._view_rosetta_script()
        if qname == "runsh":
            if os.path.exists(qval):
                self.starMapGui.executionSaveFileShLabel.setText(self._short_path(qval))
                self.stmBashFile = qval
                self.starMapGui.executionLocalEditButton.setEnabled(True)
                self.starMapGui.executionRemoteEditButton.setEnabled(True)
                self.starMapGui.executionLocalRunScript.setEnabled(True)
                self.starMapGui.executionRemoteExecuteButton.setEnabled(True)
                self._view_bash_script()
        if qname == "alspdb":
            if os.path.exists(qval):
                self.starMapGui.analysisResultPdbFileLabel.setText(self._short_path(qval))
        if qname == "usrtplr" or qname == "usrtpl": # backward compatibility
            if qval == "True":
                self.starMapGui.userRosettaTemplatesCheckBox.setChecked(True)
            else:
                self.starMapGui.userRosettaTemplatesCheckBox.setChecked(False)
        if qname == "usrtplsh":
            names = ["local", "cluster"]
            if qval:
                if not any(st in qval for st in names):
                    QtWidgets.QMessageBox.warning(self.starMapGui.tabWidget, "StarMap warning",
                        "Template filenames must contain the keyword <local> or <cluster> for adding it to the corresponding tab!",
                        QtWidgets.QMessageBox.Ok)
                    return
                self.stmUserSelBashFile = str(qval)
                self.starMapGui.userShellScriptFileLabel.setText(self._short_path(qval))
                if "local" in qval:
                    self.localShellTemplates[str(os.path.basename(qval))] = str(qval)
                    self.starMapGui.executionLocalTemplateComboBox.addItem(os.path.basename(qval))
                if "cluster" in qval:
                    self.remoteShellTemplates[str(os.path.basename(qval))] = str(qval)
                    self.starMapGui.executionRemoteTemplateComboBox.addItem(os.path.basename(qval))
            else:
                self.starMapGui.userShellScriptFileLabel.setText("No file")
        if qname == "usrtplro":
            if qval:
                self.stmUserSelRosettaFile = str(qval)
                self.starMapGui.userRosettaScriptFileLabel.setText(self._short_path(qval))
                if self.starMapGui.userRosettaTemplatesCheckBox.isChecked():
                    self._changed_user_rosettascript_event()
        if qname == "usrlbl1":
            self.starMapGui.userReplaceLabel_1.setText(qval)
        if qname == "usrlbl2":
            self.starMapGui.userReplaceLabel_2.setText(qval)
        if qname == "usrlbl3":
            self.starMapGui.userReplaceLabel_3.setText(qval)
        if qname == "usrlbl4":
            self.starMapGui.userReplaceLabel_4.setText(qval)
        if qname == "usrlbl5":
            self.starMapGui.userReplaceLabel_5.setText(qval)
        if qname == "usrlbl6":
            self.starMapGui.userReplaceLabel_6.setText(qval)
        if qname == "usrlbl7":
            self.starMapGui.userReplaceLabel_7.setText(qval)
        if qname == "usrlbl8":
            self.starMapGui.userReplaceLabel_8.setText(qval)
        if qname == "usrval1":
            self.starMapGui.userReplaceEdit_1.setText(qval)
        if qname == "usrval2":
            self.starMapGui.userReplaceEdit_2.setText(qval)
        if qname == "usrval3":
            self.starMapGui.userReplaceEdit_3.setText(qval)
        if qname == "usrval4":
            self.starMapGui.userReplaceEdit_4.setText(qval)
        if qname == "usrval5":
            self.starMapGui.userReplaceEdit_5.setText(qval)
        if qname == "usrval6":
            self.starMapGui.userReplaceEdit_6.setText(qval)
        if qname == "usrval7":
            self.starMapGui.userReplaceEdit_7.setText(qval)
        if qname == "usrval8":
            self.starMapGui.userReplaceEdit_8.setText(qval)
        if qname == "rsymmflags":
            self.starMapGui.symmRosettaOptionsEdit.setText(qval.replace('_', ' '))
        return

    # -------------------------------------------------------------------------
    def get_values_script(self, fsc=False):
        """Returns settings script"""
        if fsc:
            cxc = "ui tool show StarMap"
            cxc += "\nstmset alspdb=" + os.path.basename(self.rosettaCxSelPdbFile)
            cxc += "\nstmset densitymap=" + os.path.basename(self.rosettaDensityMapFile)
            cxc += "\nstmset mapres=" + self.starMapGui.rosettaResolutionEdit.text()
            cxc += "\nstmrunfsc"
            cxc += "\nstmrunlcc"
            cxc += "\nexit\n"
            return cxc

        cxc = "ui tool show StarMap"
        if not self.starMapGui.executionFullPathBox.isChecked():
            if self.rosettaCxSelPdbFile:
                cxc += "\nopen " + os.path.basename(self.rosettaCxSelPdbFile)
            if self.rosettaDensityMapFile:
                cxc += "\nopen " + os.path.basename(self.rosettaDensityMapFile)
        else:
            if self.rosettaCxSelPdbFile:
                cxc += "\nopen " + os.path.abspath(self.rosettaCxSelPdbFile)
            if self.rosettaDensityMapFile:
                cxc += "\nopen " + os.path.abspath(self.rosettaDensityMapFile)

        # symm values
        symm = self.starMapGui.advancedSymmCheckBox.isChecked()
        cxc += "\nstmset symm=" + str(symm)
        if self.starMapGui.advancedSymmHelixCheckBox.isChecked():
            cxc += "\nstmset symmhelix=True"
        else:
            cxc += "\nstmset symmhelix=False"
        cxc += "\nstmset rsymmflags=" + self.starMapGui.symmRosettaOptionsEdit.text().replace(' ', '_')
        half2 = self.starMapGui.rosettaModelCheckBox.isChecked()
        cxc += "\nstmset half2=" + str(half2)
        consset = self.starMapGui.advancedConstraintsSetsFileCheckBox.isChecked()
        cxc += "\nstmset consset=" + str(consset)
        fullpath = self.starMapGui.executionFullPathBox.isChecked()
        cxc += "\nstmset fullpath=" + str(fullpath)
        # files
        if not self.starMapGui.executionFullPathBox.isChecked():
            if symm:
                cxc += "\nstmset symmfile=" + os.path.basename(self.rosettaSymmFile)
                cxc += "\nstmset symmpdb=" + os.path.basename(self.symmPdbFile)
            cxc += "\nstmset selfile=" + os.path.basename(self.rosettaCxSelPdbFile)
            cxc += "\nstmset densitymap=" + os.path.basename(self.rosettaDensityMapFile)
            if half2:
                cxc += "\nstmset half2file=" + os.path.basename(self.rosettaModelEvalFile)
            if consset:
                cxc += "\nstmset consfile=" + os.path.basename(self.rosettaConsFile)
            cxc += "\nstmset runcxc=" + os.path.basename(self.stmChimeraxFile)
            cxc += "\nstmset runsh=" + os.path.basename(self.stmBashFile)
            cxc += "\nstmset runxml=" + os.path.basename(self.stmRosettaFile)
        else:
            if symm:
                cxc += "\nstmset symmfile=" + os.path.abspath(self.rosettaSymmFile)
                cxc += "\nstmset symmpdb=" + os.path.abspath(self.symmPdbFile)
            cxc += "\nstmset selfile=" + os.path.abspath(self.rosettaCxSelPdbFile)
            cxc += "\nstmset densitymap=" + os.path.abspath(self.rosettaDensityMapFile)
            if half2:
                cxc += "\nstmset half2file=" + os.path.abspath(self.rosettaModelEvalFile)
            if consset:
                cxc += "\nstmset consfile=" + os.path.abspath(self.rosettaConsFile)
            cxc += "\nstmset runcxc=" + os.path.abspath(self.stmChimeraxFile)
            cxc += "\nstmset runsh=" + os.path.abspath(self.stmBashFile)
            cxc += "\nstmset runxml=" + os.path.abspath(self.stmRosettaFile)
        # dependent values
        cxc += "\nstmset task=" + str(self.starMapGui.rosettaStrategyTaskBox.currentIndex())
        if self.starMapGui.rosettaStrategyValueBox.currentText() == "user":
            cxc += "\nstmset strategy=" + str(self.starMapGui.rosettaStrategyValueBox.currentIndex())
            cxc += "\nstmset selres=" + self.starMapGui.rosettaStrategyResiduesEdit.text()
        # independent values
        cxc += "\nstmset mapres=" + self.starMapGui.rosettaResolutionEdit.text()
        cxc += "\nstmset models=" + self.starMapGui.rosettaResultsEdit.text()
        # user defined labels and values
        usrtplr = self.starMapGui.userRosettaTemplatesCheckBox.isChecked()
        if usrtplr:
            cxc += "\nstmset usrtplr=" + str(usrtplr)
            if not self.starMapGui.executionFullPathBox.isChecked():
                cxc += "\nstmset usrtplro=" + os.path.basename(self.stmUserSelRosettaFile)
            else:
                cxc += "\nstmset usrtplro=" + os.path.abspath(self.stmUserSelRosettaFile)
        if len(self.stmUserSelBashFile) > 0:
            if not self.starMapGui.executionFullPathBox.isChecked():
                cxc += "\nstmset usrtplsh=" + os.path.basename(self.stmUserSelBashFile)
            else:
                cxc += "\nstmset usrtplsh=" + os.path.abspath(self.stmUserSelBashFile)

        if not "@@" in self.starMapGui.userReplaceEdit_1.text():
            cxc += "\nstmset usrlbl1=" + self.starMapGui.userReplaceLabel_1.text()
            cxc += "\nstmset usrval1=" + self.starMapGui.userReplaceEdit_1.text()
        if not "@@" in self.starMapGui.userReplaceEdit_2.text():
            cxc += "\nstmset usrlbl2=" + self.starMapGui.userReplaceLabel_2.text()
            cxc += "\nstmset usrval2=" + self.starMapGui.userReplaceEdit_2.text()
        if not "@@" in self.starMapGui.userReplaceEdit_3.text():
            cxc += "\nstmset usrlbl3=" + self.starMapGui.userReplaceLabel_3.text()
            cxc += "\nstmset usrval3=" + self.starMapGui.userReplaceEdit_3.text()
        if not "@@" in self.starMapGui.userReplaceEdit_4.text():
            cxc += "\nstmset usrlbl4=" + self.starMapGui.userReplaceLabel_4.text()
            cxc += "\nstmset usrval4=" + self.starMapGui.userReplaceEdit_4.text()
        if not "@@" in self.starMapGui.userReplaceEdit_5.text():
            cxc += "\nstmset usrlbl5=" + self.starMapGui.userReplaceLabel_5.text()
            cxc += "\nstmset usrval5=" + self.starMapGui.userReplaceEdit_5.text()
        if not "@@" in self.starMapGui.userReplaceEdit_6.text():
            cxc += "\nstmset usrlbl6=" + self.starMapGui.userReplaceLabel_6.text()
            cxc += "\nstmset usrval6=" + self.starMapGui.userReplaceEdit_6.text()
        if not "@@" in self.starMapGui.userReplaceEdit_7.text():
            cxc += "\nstmset usrlbl7=" + self.starMapGui.userReplaceLabel_7.text()
            cxc += "\nstmset usrval7=" + self.starMapGui.userReplaceEdit_7.text()
        if not "@@" in self.starMapGui.userReplaceEdit_8.text():
            cxc += "\nstmset usrlbl8=" + self.starMapGui.userReplaceLabel_8.text()
            cxc += "\nstmset usrval8=" + self.starMapGui.userReplaceEdit_8.text()

        cxc += "\n\n"
        return cxc

    # -------------------------------------------------------------------------
    def _replace_xml_tags(self, template):
        """Reads the given template from the disk and replaces the xml tags"""
        from pyparsing import ParseException
        from .rosettascripts import cleanupList, removeTagAndMoverByTagName, removeTagAndMoverByValueName, replaceUserDefinedRebuildingValues, reset

        try:
            parsedScript = script.parseFile(template)
            l = parsedScript.asList()

            # TODO handle residues > 800
            if self.selectedResiduesCount < 800:
                removeTagAndMoverByTagName(l, "LocalRelax")
                cleanupList(l)
            else:
                removeTagAndMoverByTagName(l, "FastRelax")
                cleanupList(l)

            # handle symmetry check and setup
            if not self.starMapGui.advancedSymmCheckBox.isChecked():
                removeTagAndMoverByTagName(l, "SetupForSymmetry")
                removeTagAndMoverByTagName(l, "SymMinMover")
                cleanupList(l)
                #self._debug("tags without <SetupForSymmetry>:\n" + str(l))
            else:
                removeTagAndMoverByTagName(l, "SetupForDensityScoring")
                removeTagAndMoverByTagName(l, "MinMover")
                cleanupList(l)
                #self._debug("tags without <SetupForDensityScoring>:\n" + str(l))

            # remove constraints
            if not self.starMapGui.advancedConstraintsSetsFileCheckBox.isChecked():
                removeTagAndMoverByTagName(l, "ConstraintSetMover")
                cleanupList(l)
                #self._debug("tags without <ConstraintSetMover>:\n" + str(l))

            # handle model evaluation
            if self.starMapGui.rosettaModelCheckBox.isChecked():
                removeTagAndMoverByValueName(l, "reportFSC")
                cleanupList(l)
                #self._debug("tags without <ReportFSC::reportFSC>:\n" + str(l))
            else:
                removeTagAndMoverByValueName(l, "reportFSC_withtest")
                #self._debug("tags without <ReportFSC::reportFSC_withtest>:\n" + str(l))

            # handle tasks strategy (user = 1)
            if self.starMapGui.rosettaStrategyValueBox.currentIndex() == 1:
                reset()
                replaceUserDefinedRebuildingValues(l, "CartesianSampler", self.starMapGui.rosettaStrategyResiduesEdit.text())
                cleanupList(l)

            # full rebuild taks
            # -- default

            # minimum rebuild task
            if self.starMapGui.rosettaStrategyTaskBox.currentIndex() == 1:
                removeTagAndMoverByValueName(l, "cen5_50")
                removeTagAndMoverByValueName(l, "cen5_60")
                removeTagAndMoverByValueName(l, "cen5_70")
                #self._debug("tags without <CartesianSampler::can5_50|cen5_60|cen5_70>:\n" + str(l))

            # refinement only task
            if self.starMapGui.rosettaStrategyTaskBox.currentIndex() == 2 or self.starMapGui.rosettaStrategyTaskBox.currentIndex() == 3:
                removeTagAndMoverByValueName(l, "cen5_50")
                removeTagAndMoverByValueName(l, "cen5_60")
                removeTagAndMoverByValueName(l, "cen5_70")
                removeTagAndMoverByValueName(l, "cen5_80")
                removeTagAndMoverByValueName(l, "cen5_rama")
                #self._debug("tags without <CartesianSampler::can5_50|cen5_60|cen5_70|cen5_80|cen5_rama>:\n" + str(l))

            # torsian refinement
            s = asXmlList(l)
            if self.starMapGui.rosettaStrategyTaskBox.currentIndex() == 3:
                s = s.replace("mover=\"relaxcart\"", "mover=\"relax\"", 9)

            return s

        except ParseException:
            self.logger.error("Error in Rosetta XML replacements")

        return

    # -------------------------------------------------------------------------
    def _replace_script_tags(self, script):
        """Replace @@ tags"""
        from .config import ROSETTA_SCRIPTS_CMD, ROSETTA_SCRIPTS_MPI_CMD
        # use mpi if cores < 1
        cores = int(self.starMapGui.executionLocalCoresEdit.text())
        if self.starMapGui.executionTabWidget.currentIndex() == 2:
            cores = int(self.starMapGui.executionRemoteCoresEdit.text())
        if cores == 1:
            if not self.starMapGui.executionFullPathBox.isChecked():
                cmdline = "$(which " + os.path.basename(ROSETTA_SCRIPTS_CMD) + ")"
            else:
                cmdline = ROSETTA_SCRIPTS_CMD + " "
        else:
            if not self.starMapGui.executionFullPathBox.isChecked():
                cmdline = "$(which " + os.path.basename(ROSETTA_SCRIPTS_MPI_CMD) + ")"
            else:
                cmdline = ROSETTA_SCRIPTS_MPI_CMD + " "

        # filename of the rosetta script
        if self.starMapGui.executionFullPathBox.isChecked():
            s = script.replace("@@ROSETTA_SCRIPT_FILE@@", os.path.realpath(self.stmRosettaFile))
        else:
            s = script.replace("@@ROSETTA_SCRIPT_FILE@@", os.path.basename(self.stmRosettaFile))
        # replace cores
        s = s.replace("@@CORES@@", str(cores))
        # filename of the saved chimera selection
        if self.starMapGui.executionFullPathBox.isChecked():
            s = s.replace("@@INPUT_PDB_FILE@@", os.path.realpath(self.rosettaCxSelPdbFile))
        else:
            s = s.replace("@@INPUT_PDB_FILE@@", os.path.basename(self.rosettaCxSelPdbFile))
        # number of output models
        s = s.replace("@@NSTRUCT@@", self.starMapGui.rosettaResultsEdit.text())
        # control density
        if self.starMapGui.executionFullPathBox.isChecked():
            s = s.replace("@@DENSITY_FILE@@", os.path.realpath(self.rosettaDensityMapFile))
        else:
            s = s.replace("@@DENSITY_FILE@@", os.path.basename(self.rosettaDensityMapFile))

        # legacy atom pair weight fix in template
        s = s.replace("@@CONSTRAINT_APW@@", '0')
        if self.starMapGui.executionFullPathBox.isChecked():
            s = s.replace("@@CONSTRAINT_SET_FILE@@", os.path.realpath(self.starMapGui.advancedConstraintsSetsFileLabel.text()))
        else:
            s = s.replace("@@CONSTRAINT_SET_FILE@@", os.path.basename(self.starMapGui.advancedConstraintsSetsFileLabel.text()))

        # symmetry replacements
        if self.starMapGui.advancedSymmCheckBox.isChecked():
            if self.starMapGui.executionFullPathBox.isChecked():
                s = s.replace("@@SYMMETRY_FILE@@", os.path.realpath(self.starMapGui.advancedSymmFileLabel.text()))
            else:
                s = s.replace("@@SYMMETRY_FILE@@", os.path.basename(self.starMapGui.advancedSymmFileLabel.text()))
            if not self.starMapGui.advancedSymmHelixCheckBox.isChecked():
                cmdline = cmdline + " -score_symm_complex true "
            s = s.replace("@@USE_SYMMETRY@@", '1')
        else:
            s = s.replace("@@RUN_SYMMETRY_COMMANDLINE@@", "")
            # xml trouble
            s = s.replace("@@SYMMETRY_FILE@@", "@@XML_TAG_WILL_BE_DELETED@@")
            s = s.replace("@@USE_SYMMETRY@@", '0')

        # strategy
        s = s.replace("@@STRATEGY@@", self.starMapGui.rosettaStrategyValueBox.currentText())

        # density weight
        s = s.replace("@@DENSITY_WEIGHT@@", self.starMapGui.advancedDensityWeightsValueBox.currentText())

        # validation
        s = s.replace("@@HIRES@@", self.starMapGui.rosettaResolutionEdit.text())
        if self.starMapGui.rosettaModelCheckBox.isChecked():
            if self.starMapGui.executionFullPathBox.isChecked():
                s = s.replace("@@VALIDATION_HALF2_FILE@@", os.path.realpath(self.starMapGui.rosettaModelFileLabel.text()))
            else:
                s = s.replace("@@VALIDATION_HALF2_FILE@@", os.path.basename(self.starMapGui.rosettaModelFileLabel.text()))
        else:
            s = s.replace("@@VALIDATION_HALF2_FILE@@", "@@XML_TAG_WILL_BE_DELETED@@")

        # user defined tags
        s = s.replace("@@USER1@@", self.starMapGui.userReplaceEdit_1.text())
        s = s.replace("@@USER2@@", self.starMapGui.userReplaceEdit_2.text())
        s = s.replace("@@USER3@@", self.starMapGui.userReplaceEdit_3.text())
        s = s.replace("@@USER4@@", self.starMapGui.userReplaceEdit_4.text())
        s = s.replace("@@USER5@@", self.starMapGui.userReplaceEdit_5.text())
        s = s.replace("@@USER6@@", self.starMapGui.userReplaceEdit_6.text())
        s = s.replace("@@USER7@@", self.starMapGui.userReplaceEdit_7.text())
        s = s.replace("@@USER8@@", self.starMapGui.userReplaceEdit_8.text())

        # how to call rosetta
        s = s.replace("@@ROSETTA_SCRIPT_EXE@@", cmdline)

        return s

    # -------------------------------------------------------------------------
    @classmethod
    def get_singleton(cls, session, **kw):
        """Return single instance"""
        from chimerax.core import tools  # @UnresolvedImport
        return tools.get_singleton(session, StarMap, 'StarMap', **kw)
