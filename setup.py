#!/usr/bin/env python3

# -----------------------------------------------------------------------------
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from glob import glob  # @UnresolvedImport
from starmap import __version__ as starmap_version  # @UnresolvedImport

# -----------------------------------------------------------------------------
import os
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# -----------------------------------------------------------------------------
setup(name='ChimeraX-StarMapQt5',
    version=starmap_version,
    description='A mediator tool between ChimeraX and the Rosetta modeling software',
    long_description=read('README.md'),
    author='Wolfgang Lugmayr',
    author_email='w.lugmayr@uke.de',
    url='https://github.com/wlugmayr/chimerax-starmap/',
    license = "BSD 2-Clause License",
    platforms='any',
    packages=['starmap'],
    classifiers=[
      'Development Status :: 3 - Alpha' ,
      'License :: OSI Approved :: BSD 2-Clause License',
      'Operating System :: OS Independent',
      'Programming Language :: Python',
      'Programming Language :: Python :: 3',
      'Environment :: X11 Applications", "Framework :: ChimeraX',
      'Intended Audience :: Science/Research',
      'ChimeraX :: Bundle :: Volume Data :: 1,1 :: starmap :: starmap :: ',
      'ChimeraX :: Tool :: StarMap :: Volume Data :: Run Rosetta refinements',
      'ChimeraX :: Command :: stmconfig :: Volume Data :: Print StarMap configuration',
      'ChimeraX :: Command :: stmset :: Volume Data :: Set StarMap values',
      'ChimeraX :: Command :: stmrunfsc :: Volume Data :: Execute FSC model vs. map analysis',
      'ChimeraX :: Command :: stmrunlcc :: Volume Data :: Execute LCC per residue analysis',
      'ChimeraX :: Command :: stmrunzsc :: Volume Data :: Execute LCC zscore per residue analysis',
      'ChimeraX :: Command :: stmhelp :: Volume Data :: Show StarMap help'
      ],
    install_requires=['pyparsing', 'pyqtgraph', 'ChimeraX-Core==1.3'],
    data_files=[
        ('share/starmap/', glob('templates/s*.xml')),
        ('share/starmap/', glob('templates/rosetta_apix.xml')),
        ('share/starmap/', glob('templates/rosetta_tmpl_1.2.xml')),
        ('share/starmap/', glob('templates/*_local.tmpl.sh')),
        ('share/starmap/', glob('templates/*_cluster.tmpl.sh')),
        ('share/starmap/', glob('contrib/*')),
        ('share/starmap/docs/', glob('docs/*.*')),
        ('share/starmap/docs/_static/', glob('docs/_static/*')),
        ('share/starmap/docs/_sources/', glob('docs/_sources/*')),
        ('share/starmap/docs/_images/', glob('docs/_images/*')),
    ],
)
