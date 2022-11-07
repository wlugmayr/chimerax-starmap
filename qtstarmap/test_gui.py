#!/usr/bin/env python3
"""
Test the StarMap pyuic user interface.
"""
import sys
from PyQt5 import QtWidgets
from qtstarmapwidget import Ui_qtStarMapWidget  # @UnresolvedImport

# -----------------------------------------------------------------------------
class TestGui(Ui_qtStarMapWidget):
    def __init__(self, dialog):
        Ui_qtStarMapWidget.__init__(self)
        self.setupUi(dialog)

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    dialog = QtWidgets.QDialog()

    prog = TestGui(dialog)

    dialog.show()
    sys.exit(app.exec_())

