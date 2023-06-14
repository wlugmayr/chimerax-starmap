#
# Copyright (c) 2022 by the Universitätsklinikum Hamburg-Eppendorf (UKE)
# Written by Wolfgang Lugmayr <w.lugmayr@uke.de>
#
"""
MEDIC add-ons and summary popup window
"""
import os
import re
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QScrollArea, QApplication, QFrame, QComboBox,
                             QVBoxLayout, QHBoxLayout, QMainWindow, QGridLayout, QMessageBox, QCheckBox,
                             QGroupBox)
from PyQt5.QtCore import Qt, QRect
from PyQt5 import QtGui

MEDIC_SCRIPT_TEMPLATE = "starmap_medic.tmpl.sh"
MEDIC_SUMMARY = "MEDIC_summary.txt"

# -------------------------------------------------------------------------
class MedicSummaryPopupWindow(QMainWindow):
    """GUI handling"""
    tool = None

    # -------------------------------------------------------------------------
    def __init__(self, parent):
        """Initializes this class"""
        super(MedicSummaryPopupWindow, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.win = parent
        self.win.setCentralWidget(self)
        #self._init_gui()

    # -------------------------------------------------------------------------
    def init_gui(self, summaryFile):
        """Initializes the user interface"""
        self.buttonDict = {}
        
        self.scrollArea = QScrollArea()
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaContent = QWidget()
        self.verticalLayoutWidget = QWidget(self.scrollAreaContent)
        self.medicWindowContent = QVBoxLayout(self.verticalLayoutWidget)       
        self.scrollAreaContent.setLayout(self.medicWindowContent)
        
        # chimerax zone row
        self.chimeraxBox = QGroupBox(self.verticalLayoutWidget)
        self.chimeraxBox.setTitle("ChimeraX")
        self.zoneRow = QHBoxLayout()
        self.chimeraxBox.setLayout(self.zoneRow)
        self.zoneCheckBox = QCheckBox(self.chimeraxBox)
        self.zoneCheckBox.setChecked(True)
        self.zoneCheckBox.setText("Zone")
        self.zoneRow.addWidget(self.zoneCheckBox)        
        models = self.tool.get_models_string()
        self.mapValueBox = QComboBox(self.chimeraxBox)
        for m in models:
            self.mapValueBox.addItem(m)
            self.mapValueBox.setCurrentIndex(1)
        self.zoneRow.addWidget(self.mapValueBox)
        self.nearLabel = QLabel(self.chimeraxBox)
        self.nearLabel.setText("near")
        self.zoneRow.addWidget(self.nearLabel)
        self.modelValueBox = QComboBox(self.chimeraxBox)
        for m in models:
            self.modelValueBox.addItem(m)
            self.modelValueBox.setCurrentIndex(0)
        self.zoneRow.addWidget(self.modelValueBox)
        self.zoneHelpButton = QPushButton(self.chimeraxBox)
        self.zoneHelpButton.setFixedWidth(30)
        self.zoneHelpButton.setText("?")
        self.zoneHelpButton.clicked.connect(self.tool._help_analysis_medic_summary)
        self.zoneRow.addWidget(self.zoneHelpButton)
        self.medicWindowContent.addWidget(self.chimeraxBox)

        # dynamic medic_summary.txt content
        global MEDIC_SUMMARY
        if not summaryFile:
            summaryFile = MEDIC_SUMMARY
        if not os.path.isfile(summaryFile):
            msg = summaryFile + " file not found!\n\n"
            msg += "Maybe your MEDIC job failed or is not finished yet!"
            QMessageBox.warning(self, "StarMap Warning", msg, QMessageBox.Ok)
            return False
            
        with open(summaryFile, 'r') as read:
            medicRowGrid = QGridLayout(self.verticalLayoutWidget)
            medicRowGrid.setHorizontalSpacing(50)
            medicRow = QWidget()
            medicRow.setLayout(medicRowGrid)
            resLabel = QLabel()
            errLabel = QLabel()
            causeLabel = QLabel()
            row = 0
            for line in read:
                if line and len(line.strip()) > 1:
                    tok = line.split(',')
                    if len(tok) == 1 and 'causes' in str(tok[0].strip()):
                        causeLabel.setText(tok[0].strip())
                        causeLabel.setFont(QtGui.QFont('Sans Serif', 12))
                    if len(tok) == 2:
                        res = tok[0].strip().replace(' ','')
                        resLabel.setText(res)
                        resLabel.setFont(QtGui.QFont('Sans Serif', 12))
                        errLabel = QLabel(str(tok[1].strip()))
                        if tok[1] and tok[1].strip() == 'definite error':
                            resLabel.setStyleSheet("color: red")
                            errLabel.setText('definite error')
                        if tok[1] and tok[1].strip() == 'possible error':
                            resLabel.setStyleSheet("color: orange")
                            errLabel.setText('possible error')
                else:
                    #print(resLabel.text() + ' - ' + errLabel.text() + ' - ' + causeLabel.text())
                    medicRowGrid.addWidget(resLabel, row, 0)
                    medicRowGrid.addWidget(causeLabel, row, 1)
                    selButton = QPushButton()
                    selButton.setText('   Show ' + resLabel.text() + '   ')
                    self.buttonDict[resLabel.text()] = selButton
                    medicRowGrid.addWidget(selButton, row, 3)
                    self.medicWindowContent.addWidget(medicRow)
                    row += 1
                    resLabel = QLabel()
                    errLabel = QLabel()
                    causeLabel = QLabel()
            # fix for new newline at file end, so add last manually
            #print(resLabel.text() + ' - ' + errLabel.text() + ' - ' + causeLabel.text())
            medicRowGrid.addWidget(resLabel, row, 0)
            medicRowGrid.addWidget(causeLabel, row, 1)
            selButton = QPushButton()
            selButton.setText('   Show ' + resLabel.text() + '   ')
            self.buttonDict[resLabel.text()] = selButton
            medicRowGrid.addWidget(selButton, row, 3)
            self.medicWindowContent.addWidget(medicRow)

            # connect buttons with residue text
            for res, button in self.buttonDict.items():
                button.clicked.connect(lambda checked, res=res: self._show_res(res))

        self.scrollArea.setWidget(self.scrollAreaContent)
        self.win.setCentralWidget(self.scrollArea)
        #self.win.setFixedWidth(700)
        self.win.setMinimumWidth(750)
        screen = QApplication.primaryScreen()
        self.win.move(screen.size().width() - 800, 400)
        self.win.setWindowTitle('MEDIC Summary')
        return True

    # -------------------------------------------------------------------------
    def set_callback(self, tool):
        """Set callback to StarMap plug-in"""
        self.tool = tool

    # -------------------------------------------------------------------------
    def _convert_res(self, s):
        """Parse residues and return in ChimeraX notation"""
        if len(re.findall('(\d+|\D+)', s)) == 2:
            tok = re.findall('(\d+|\D+)', s)
            return tok[1] + ':' + tok[0]
        if len(re.findall('(\d+|\D+)', s)) == 4:
            tok = re.findall('(\d+|\D+)', s)
            return tok[3] + ':' + tok[0] + '-' + tok[2]

    # -------------------------------------------------------------------------
    def _show_res(self, res):
        """Run a ChimeraX command"""
        model_id = self.modelValueBox.currentText().rsplit(" ", 1)[0]
        map_id = self.mapValueBox.currentText().rsplit(" ", 1)[0]
        if not self.zoneCheckBox.isChecked():
            self.tool._run_cmd("~sel")
            self.tool._run_cmd("volume unzone " + map_id)
            self.tool._run_cmd("sel " + model_id + "/" + self._convert_res(res))
            self.tool._run_cmd("view sel")
        else:
            self.tool._run_cmd("~sel")
            self.tool._run_cmd("sel " + model_id + "/" + self._convert_res(res))
            self.tool._run_cmd("view sel")
            self.tool._run_cmd("volume zone " + map_id + " near sel range 3")
        self.tool._run_cmd("clip off")
        self.tool._run_cmd("zoom 0.4")

