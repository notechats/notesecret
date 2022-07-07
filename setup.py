import subprocess
import sys
from os import path

from setuptools import find_packages, setup

try:
    from notebuild.tool import read_version
except Exception as e:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "notebuild"])
    from notebuild.tool import read_version



version_path = path.join(path.abspath(path.dirname(__file__)), 'script/__version__.md')

version = read_version(version_path)


install_requires = ['notebuild']


setup(name='notesecret',
      version=version,
      description='notesecret',
      author='niuliangtao',
      author_email='1007530194@qq.com',
      url='https://github.com/1007530194',
      packages=find_packages(),
      install_requires=install_requires,
      )
