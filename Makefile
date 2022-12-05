#
# Before calling make source and activate the development environment like:
#   source dev_functions.source
#   starmap_dev_chimerax_centos9
#   make bundle-install
#

.EXPORT_ALL_VARIABLES:
.PHONY: env tmpdirs qt5-to-qt6 doc bundle-setup
VER := $(shell grep __version__ ./starmap/__init__.py | cut -f2 -d'"' | head -1)

env:
	export VER=$(VER)

wheeldist-qt5: clean doc
	sed -i "s/self.tabWidget = QtWidgets.QTabWidget(qtStarMapWidget)/self.tabWidget = QtWidgets.QTabWidget(qtStarMapWidget);\n        self.tabWidget.setFont(QtGui.QFont(\"Sans Serif\", 10))/g" bundle/src/qtstarmapwidget.py
	(cd bundle; $(CHIMERAX)/bin/ChimeraX --nogui --cmd "devel build . ; exit")
	cp ./bundle/dist/ChimeraX_StarMap-$(VER)-py3-none-any.whl ./dist/qt5/ChimeraX_StarMap-$(VER)-py3-none-any.whl

wheeldist-qt6: clean doc qt5_to_qt6
	(cd bundle; $(CHIMERAX)/bin/ChimeraX --nogui --cmd "devel build . ; exit")
	cp ./bundle/dist/ChimeraX_StarMap-$(VER)-py3-none-any.whl ./dist/ChimeraX_StarMap-$(VER)-py3-none-any.whl

bundle-install: clean doc qt5_to_qt6
	(cd bundle; $(CHIMERAX)/bin/ChimeraX --nogui --cmd "devel install . ; exit")

bundle-install-win: clean doc qt5_to_qt6
	(cd bundle; $(CHIMERAX)/bin/ChimeraX-console.exe --nogui --cmd "devel install . ; exit")

bundle-setup: tmpdirs
	mkdir -p ./bundle/src
	cp -r ./templates ./bundle/src
	cp -r ./contrib ./bundle/src
	cp starmap/*.py bundle/src
	cp LICENSE bundle/license.txt

doc: clean sed_version bundle-setup
	mkdir -p ./bundle/src/docs
	mkdir -p ./sphinx/_static
	(cd sphinx; make html)
	(cd sphinx; make epub)
	cp -rv ./sphinx/_build/html/* ./bundle/src/docs
	cp -rv ./sphinx/_build/epub/StarMap.epub ./bundle/src/docs
	cp *.txt *.md LICENSE ./bundle/src/docs

sed_version: env
	sed -e "s/@@VERSION@@/${VER}/g" <./sphinx/conf.py.in >./sphinx/conf.py
	sed -e "s/@@VERSION@@/${VER}/g" <./sphinx/install_guide.rst.in >./sphinx/install_guide.rst
	sed -e "s/@@VERSION@@/${VER}/g" <./bundle/bundle_info.xml.in >./bundle/bundle_info.xml
	sed -e "s/@@VERSION@@/${VER}/g" <./README.md.in >./README.md

qt5_to_qt6:
	./qt5_to_qt6.sh

pylint:
	pylint -r n '--msg-template={path}:{line}: [{msg_id}({symbol}), {obj}] {msg}' --disable=E0401,C0103,C0301,W0603,R1711,I1101,E0611,W0602,W0108,C0302,R0911 starmap/*.py | grep -v qtstarmapwidget

qtcreator:
	(cd qtstarmap; qtcreator qtstarmapwidget.ui)
	pyuic5 qtstarmap/qtstarmapwidget.ui -o qtstarmap/qtstarmapwidget.py
	pyuic5 qtstarmap/qtstarmapwidget.ui -o starmap/qtstarmapwidget.py

test_gui:
	(cd qtstarmap; $(CHIMERAX_PYTHON) test_gui.py)

test_config:
	$(CHIMERAX)/bin/ChimeraX -m chimerax.starmap.config

test_config_win:
	$(CHIMERAX)/bin/ChimeraX-console.exe -m chimerax.starmap.config

uninstall:
	/usr/bin/yes | $(CHIMERAX)/bin/ChimeraX -m pip uninstall ChimeraX-StarMap

deploy-pip-qt5: wheeldist-qt5 uninstall
	$(CHIMERAX)/bin/ChimeraX -m pip install ./dist/qt5/ChimeraX_StarMap-$(VER)-py3-none-any.whl

deploy-pip-user: wheeldist-qt6 uninstall
	$(CHIMERAX)/bin/ChimeraX -m pip install --user ./dist/ChimeraX_StarMap-$(VER)-py3-none-any.whl

bundle-clean:
	rm -rf ./bundle/src
	rm -rf ./bundle/build
	rm -rf ./bundle/dist
	rm -rf ./bundle/ChimeraX_StarMap.egg-info
	rm -f ./bundle/license.txt
	rm -f ./bundle/bundle_info.xml

clean: bundle-clean
	rm -rf ./starmap/__pycache__
	rm -rf ./qtstarmap/__pycache__
	rm -rf ./sphinx/_static
	rm -f ./sphinx/conf.py
	rm -f ./sphinx/install_guide.rst
	(cd sphinx; make clean)

distclean: clean
	rm -rf ./dist

tmpdirs:
	mkdir -p ./dist/qt5
	mkdir -p ./sphinx/_static

gitignore:
	echo .gitignore >.gitignore
	echo .project >>.gitignore
	echo .pydevproject >>.gitignore
	echo .settings >>.gitignore


