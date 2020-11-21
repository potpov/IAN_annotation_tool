from cx_Freeze import setup, Executable
import os
import scipy
import skimage
import opcode
import sys

VENV_DIR = os.path.dirname(os.path.dirname(os.__file__))
LIB_DIR = os.path.join(VENV_DIR, "Lib")
SITE_PACKAGES_DIR = os.path.join(LIB_DIR, "site-packages")
PROJECT_DIR = os.path.abspath(os.path.curdir)

APP_NAME = 'IAN Annotation Tool'
SCRIPT_PATH = os.path.join(PROJECT_DIR, "annotation_tool.py")
ICON_PATH = os.path.join(PROJECT_DIR, "annotation", "images", "icon.ico")

## installs in Program Files --> the installer fails because it has not enough privileges
# if 'bdist_msi' in sys.argv:
#     sys.argv += ['--initial-target-dir', r'C:\Program Files\{}'.format(APP_NAME)]

version = "1.2"


def collect_dist_info(packages):
    """
    Recursively collects the path to the packages' dist-info.
    From https://github.com/marcelotduarte/cx_Freeze/issues/438#issuecomment-472954154
    """
    import pkg_resources
    from os.path import join, basename
    if not isinstance(packages, list):
        packages = [packages]
    dirs = []
    for pkg in packages:
        distrib = pkg_resources.get_distribution(pkg)
        for req in distrib.requires():
            dirs.extend(collect_dist_info(req.key))
        dirs.append((distrib.egg_info, join('Lib', basename(distrib.egg_info))))
    return dirs


packages_dist_info = ['apptools', 'configobj', 'envisage', 'mayavi', 'numpy', 'pygments',
                      'six', 'traits', 'traitsui', 'vtk', 'pyface', 'setuptools']

packages = ['sys', 'os', 'ctypes', 'platform', 'shutil', 'numpy', 'traits', 'traits.api', 'mayavi',
            'mayavi.core', 'traitsui', 'traitsui.qt4.toolkit', 'mayavi.core.ui', 'mayavi.core.ui.api',
            'tvtk', 'tvtk.tools', 'tvtk.api', 'json', 'math', 'time', 'sqlite3',
            'pyface', 'pyface.ui', 'pyface.ui.qt4', 'pkg_resources', 'pyface.qt.QtGui', 'pyface.qt.QtCore',
            'pkg_resources._vendor', 'pkg_resources.extern', "tvtk.pyface.ui.qt4", 'pygments', 'vtkmodules',
            'pyface.ui.qt4', 'pyface.qt', 'numpy', 'matplotlib', 'mayavi', 'traits', 'traitsui',
            'scipy.linalg', 'pyqt5', 'pyface']


def get_site_package(name):
    return ((os.path.join(SITE_PACKAGES_DIR, name)), name)


include_files = collect_dist_info(packages_dist_info)

# fix for scipy
scipy_path = os.path.dirname(scipy.__file__)
include_files.append((str(scipy_path), "scipy"))

# fix for skimage
skimage_path = os.path.dirname(skimage.__file__)
include_files.append((str(skimage_path), "skimage"))

# fix for mpl_toolkits
include_files.append(get_site_package('mpl_toolkits'))

# fix for distutils
# from https://gist.github.com/nicoddemus/ca0acd93a20acbc42d1d#workaround
distutils_path = os.path.join(os.path.dirname(opcode.__file__), 'distutils')
include_files.append((distutils_path, 'distutils'))

build_exe_options = {
    "packages": packages,
    "excludes": ['tkinter', 'multiprocessing.Pool'],
    "includes": [],
    "include_files": include_files
}

executable = Executable(
    script=SCRIPT_PATH,
    targetName="{}.exe".format(APP_NAME),
    base='Win32GUI',
    icon=ICON_PATH,
    shortcutName=APP_NAME,
    shortcutDir="DesktopFolder",
)

setup(name=APP_NAME,
      version=version,
      description=APP_NAME,
      author="AImageLab",
      options={"build_exe": build_exe_options},
      executables=[executable]
      )

# fix multiprocessing Pool.pyc --> pool.pyc
# from https://github.com/marcelotduarte/cx_Freeze/issues/353#issuecomment-376829379
multiprocessing_dir = os.path.join("build", "exe.win-amd64-3.7", "lib", "multiprocessing")
os.rename(os.path.join(multiprocessing_dir, "Pool.pyc"), os.path.join(multiprocessing_dir, "pool.pyc"))
