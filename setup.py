__author__="cjh66"
__date__ ="$May 11, 2010 11:28:14 AM$"

from setuptools import setup, find_packages

import py2exe

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.version = "0.5.0"
        self.company_name = "No Company"
        self.copyright = "no copyright"
        self.name = "py2exe sample files"


myservice = Target(
    description = "A sample Windows NT service",
    modules = ['service'],
    cmdline_style='pywin32'
)

#setup(
#    options = {"py2exe": {"compressed": 1, "bundle_files": 1} },
#    console=["service.py"],
#    zipfile = None,
#    service=[myservice]
#)

setup (
  name = 'Munin_Node',
  version = '0.1',
  packages = find_packages(),

  # Declare your packages' dependencies here, for eg:
  #install_requires=['foo>=3'],

  # Fill in these to make your Egg ready for upload to
  # PyPI
  author = 'cjh66',
  author_email = '',

  options = {"py2exe": {
    "compressed": 1,
    "bundle_files": 3,
    "includes":"win32com,win32service,win32serviceutil,win32event",
    "packages":"encodings",
    } },
  console=["service.py"],
  service=[myservice],

  summary = 'Just another Python package for the cheese shop',
  url = '',
  license = '',
  long_description= 'Long description of the package',

  # could also include long_description, download_url, classifiers, etc.


)
