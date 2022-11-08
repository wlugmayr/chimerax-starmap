#!/bin/sh
#
# Darwin: search and replace sed by gsed
#

cd bundle

# bundle_info.xml
#sed -i "s/StarMapQt5/StarMap/g" bundle_info.xml
sed -i "s/==1.3/>=1.4/g" bundle_info.xml

cd src

# tool.py
sed -i "s/from PyQt5 /from PyQt6 /g" tool.py
sed -i "s/from PyQt5.Qt/from PyQt6.QtGui/g" tool.py
sed -i "s/self.starMapGui.executionTextEdit.setTabStopWidth/#self.starMapGui.executionTextEdit.setTabStopWidth/g" tool.py
sed -i "s/#self.starMapGui.executionTextEdit.setTabStopDistance/self.starMapGui.executionTextEdit.setTabStopDistance/g" tool.py
sed -i "s/font.setStyleHint/#font.setStyleHint/g" tool.py

# qtstarmapwidget.py
sed -i "s/PyQt5/PyQt6/g" qtstarmapwidget.py
sed -i "s/setFrameShape(QtWidgets.QFrame.HLine)/setFrameStyle(QtWidgets.QFrame.Shape.HLine)/g" qtstarmapwidget.py
sed -i "s/setFrameShadow(QtWidgets.QFrame.Sunken)/setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)/g" qtstarmapwidget.py
sed -i "s/self.tabWidget = QtWidgets.QTabWidget(qtStarMapWidget)/self.tabWidget = QtWidgets.QTabWidget(qtStarMapWidget); self.tabWidget.setFont(QtGui.QFont(\"Sans Serif\", 10))/g" qtstarmapwidget.py

