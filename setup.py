import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='zohocrm-python',
      version='0.1.5',
      description='API wrapper for ZohoCRM written in Python',
      long_description=read('README.md'),
      url='https://github.com/GearPlug/zohocrm-python',
      author='Nerio Rincon',
      author_email='nrincon.mr@gmail.com',
      license='GPL',
      packages=['zohocrm'],
      install_requires=[
          'requests',
      ],
      zip_safe=False)
