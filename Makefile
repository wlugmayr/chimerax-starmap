#
# Before calling make source and activate the development environment like:
#   source dev_functions.source
#   starmap_dev_chimerax13_maxwell_centos7
#   make dist
#

.EXPORT_ALL_VARIABLES:
.PHONY: env gitdirs qt5-to-qt6
BASEVER := $(shell grep __version__ ./starmap/__init__.py | cut -f2 -d'"' | cut -f1,2 -d'.' | head -1)
VER := $(shell grep __version__ ./starmap/__init__.py | cut -f2 -d'"' | head -1)

env:
	export VER=$(VER)
	export BASEVER=$(BASEVER)

dist: env distclean gitdirs doc wheeldist wheeldist-qt5 examplesdist
	ls -l dist/

wheeldist-qt5:
	sed -i "s/self.tabWidget = QtWidgets.QTabWidget(qtStarMapWidget)/self.tabWidget = QtWidgets.QTabWidget(qtStarMapWidget);\n        self.tabWidget.setFont(QtGui.QFont(\"Sans Serif\", 10))/g" starmap/qtstarmapwidget.py
	$(CHIMERAX_PYTHON) setup.py bdist_wheel
	git checkout starmap/qtstarmapwidget.py

wheeldist:
	./qt5_to_qt6.sh
	$(CHIMERAX_PYTHON) setup.py bdist_wheel
	git checkout setup.py
	git checkout starmap/__init__.py
	git checkout starmap/qtstarmapwidget.py
	git checkout starmap/tool.py
	
sourcedist:
	$(CHIMERAX_PYTHON) setup.py sdist

examplesdist:
	ln -s ./examples ./starmap_examples
	tar zchvf dist/ChimeraX-StarMap-$(BASEVER)-examples.tar.gz ./starmap_examples
	7z a dist/ChimeraX-StarMap-$(BASEVER)-examples.zip ./starmap_examples
	rm -f ./starmap_examples

doc: clean doc_version
	mkdir -p docs
	mkdir -p sphinx/_static
	(cd sphinx; make html)
	(cd sphinx; make epub)
	cp -rv ./sphinx/_build/html/* ./docs
	cp -rv ./sphinx/_build/epub/StarMap.epub ./docs
	cp *.txt ./docs

docdist: doc
	ln -s ./docs ./starmap_docs
	tar zchvf dist/ChimeraX-StarMap-$(BASEVER)-docs.tar.gz ./starmap_docs
	7z a dist/ChimeraX-StarMap-$(BASEVER)-docs.zip ./starmap_docs
	rm -f ./starmap_docs

doc_version: env
	sed -e "s/@@VERSION@@/${VER}/g" <./sphinx/conf.py.in >./sphinx/conf.py
	sed -e "s/@@VERSION@@/${VER}/g" <./sphinx/install_guide.rst.in >./sphinx/install_guide.rst

pylint:
	pylint -r n '--msg-template={path}:{line}: [{msg_id}({symbol}), {obj}] {msg}' --disable=E0401,C0103,C0301,W0603,R1711,I1101,E0611 starmap/*.py | grep -v qtstarmapwidget

qtcreator:
	(cd qtstarmap; qtcreator qtstarmapwidget.ui)
	pyuic5 qtstarmap/qtstarmapwidget.ui -o qtstarmap/qtstarmapwidget.py
	pyuic5 qtstarmap/qtstarmapwidget.ui -o starmap/qtstarmapwidget.py

test_gui:
	(cd qtstarmap; $(CHIMERAX_PYTHON) test_gui.py)

test_config:
	$(CHIMERAX)/bin/ChimeraX -m starmap.config

uninstall: 
	/usr/bin/yes | $(CHIMERAX)/bin/ChimeraX -m pip uninstall ChimeraX-StarMap

uninstall-qt5: 
	/usr/bin/yes | $(CHIMERAX)/bin/ChimeraX -m pip uninstall ChimeraX-StarMapQt5

deploy-qt5: distclean dist uninstall-qt5
	$(CHIMERAX)/bin/ChimeraX -m pip install ./dist/ChimeraX_StarMapQt5-$(VER)-py3-none-any.whl
		
deploy-user: uninstall
	$(CHIMERAX)/bin/ChimeraX -m pip install --user ./dist/ChimeraX_StarMap-$(VER)-py3-none-any.whl

clean:
	rm -rf starmap/__pycache__
	rm -rf qtstarmap/__pycache__
	rm -f ./sphinx/conf.py
	rm -f ./sphinx/install_guide.rst
	rm -rf ./ChimeraX_StarMapQt5.egg-info
	rm -rf ./ChimeraX_StarMap.egg-info

distclean: clean
	rm -rf ./build
	rm -rf ./docs
	#rm -rf ./dist
	rm -rf ./sphinx/_static
	rm -f MANIFEST
	(cd sphinx; make clean)

gitdirs:
	mkdir -p dist
	mkdir -p sphinx/_static

