#
# Before calling make source and activate the development environment like:
#   source dev_functions.source
#   starmap_build_chimerax_centos9
#   make bundle-install
#

.EXPORT_ALL_VARIABLES:
.PHONY: env gitdirs qt5-to-qt6 doc bundle
BASEVER := $(shell grep __version__ ./starmap/__init__.py | cut -f2 -d'"' | cut -f1,2 -d'.' | head -1)
VER := $(shell grep __version__ ./starmap/__init__.py | cut -f2 -d'"' | head -1)

env:
	export VER=$(VER)
	export BASEVER=$(BASEVER)

wheeldist-qt5: distclean doc
	sed -i "s/self.tabWidget = QtWidgets.QTabWidget(qtStarMapWidget)/self.tabWidget = QtWidgets.QTabWidget(qtStarMapWidget);\n        self.tabWidget.setFont(QtGui.QFont(\"Sans Serif\", 10))/g" bundle/src/qtstarmapwidget.py
	(cd bundle; $(CHIMERAX)/bin/ChimeraX --nogui --cmd "devel build . ; exit")
	cp ./bundle/dist/ChimeraX_StarMap-$(VER)-py3-none-any.whl ./bundle/wheels/qt5/ChimeraX_StarMap-$(VER)-py3-none-any.whl 

wheeldist-qt6: distclean doc
	./qt5_to_qt6.sh
	(cd bundle; $(CHIMERAX)/bin/ChimeraX --nogui --cmd "devel build . ; exit")
	cp ./bundle/dist/ChimeraX_StarMap-$(VER)-py3-none-any.whl ./bundle/wheels/ChimeraX_StarMap-$(VER)-py3-none-any.whl 

bundle-install: distclean doc
	./qt5_to_qt6.sh
	(cd bundle; $(CHIMERAX)/bin/ChimeraX --nogui --cmd "devel install . ; exit")
	
bundle-setup:
	mkdir -p ./bundle/src
	mkdir -p ./bundle/wheels/qt5
	cp -r ./templates ./bundle/src
	cp -r ./contrib ./bundle/src
	cp starmap/*.py bundle/src
	cp LICENSE bundle/license.txt
	
doc: clean sed_version bundle-setup
	mkdir -p docs
	mkdir -p sphinx/_static
	(cd sphinx; make html)
	(cd sphinx; make epub)
	cp -rv ./sphinx/_build/html/* ./docs
	cp -rv ./sphinx/_build/epub/StarMap.epub ./docs
	cp *.txt *.md LICENSE ./docs
	cp -rv ./docs ./bundle/src/docs

sed_version: env
	sed -e "s/@@VERSION@@/${VER}/g" <./sphinx/conf.py.in >./sphinx/conf.py
	sed -e "s/@@VERSION@@/${VER}/g" <./sphinx/install_guide.rst.in >./sphinx/install_guide.rst
	sed -e "s/@@VERSION@@/${VER}/g" <./bundle/bundle_info.xml.in >./bundle/bundle_info.xml
	sed -e "s/@@VERSION@@/${VER}/g" <./README.md.in >./README.md

pylint:
	pylint -r n '--msg-template={path}:{line}: [{msg_id}({symbol}), {obj}] {msg}' --disable=E0401,C0103,C0301,W0603,R1711,I1101,E0611 starmap/*.py | grep -v qtstarmapwidget

qtcreator:
	(cd qtstarmap; qtcreator qtstarmapwidget.ui)
	pyuic5 qtstarmap/qtstarmapwidget.ui -o qtstarmap/qtstarmapwidget.py
	pyuic5 qtstarmap/qtstarmapwidget.ui -o starmap/qtstarmapwidget.py

test_gui:
	(cd qtstarmap; $(CHIMERAX_PYTHON) test_gui.py)

test_config:
	$(CHIMERAX)/bin/ChimeraX -m chimerax.starmap.config

uninstall: 
	/usr/bin/yes | $(CHIMERAX)/bin/ChimeraX -m pip uninstall ChimeraX-StarMap

deploy-pip-qt5: wheeldist-qt5 uninstall
	$(CHIMERAX)/bin/ChimeraX -m pip install ./bundle/wheels/qt5/ChimeraX_StarMap-$(VER)-py3-none-any.whl
		
deploy-pip-user: wheeldist uninstall
	$(CHIMERAX)/bin/ChimeraX -m pip install --user ./bundle/wheels/ChimeraX_StarMap-$(VER)-py3-none-any.whl

bundle-clean:
	rm -rf ./bundle/src
	rm -rf ./bundle/build
	rm -rf ./bundle/dist
	rm -rf ./bundle/ChimeraX_StarMap.egg-info
	rm -f ./bundle/license.txt
	rm -f ./bundle/bundle_info.xml
	
clean: bundle-clean
	rm -rf starmap/__pycache__
	rm -rf qtstarmap/__pycache__
	rm -f ./sphinx/conf.py
	rm -f ./sphinx/install_guide.rst

distclean: clean
	rm -rf ./docs
	rm -rf ./sphinx/_static
	(cd sphinx; make clean)

realclean: distclean
	rm -rf bundle/wheels
	
gitdirs:
	mkdir -p dist
	mkdir -p sphinx/_static

gitignore:
	echo .gitignore >.gitignore
	echo .project >>.gitignore
	echo .pydevproject >>.gitignore
	echo .settings >>.gitignore
