#!/usr/bin/env python
import sys

from setuptools import setup, find_packages

# Requirements.
setup_requirements = ['pytest-runner'] if {'pytest', 'test', 'ptr'}.intersection(sys.argv) else []
install_requirements = ['ipykernel', 'pyreadline; platform_system == "Windows"']
test_requirements = ['pytest', 'pytest-pep8', 'pytest-flakes']

# Fetch readme content.
with open('README.rst', 'r') as readme_file:
    readme = readme_file.read()

setup(name='pyprinter',
      version='1.5.3',
      description='Print Everything!',
      long_description=readme,
      author='Ofir Brukner',
      author_email='ofirbrukner@gmail.com',
      url='https://github.com/ofir123/py-printer',
      download_url='https://github.com/ofir123/py-printer/archive/1.5.3.tar.gz',
      license="MIT",
      packages=find_packages(),
      setup_requires=setup_requirements,
      install_requires=install_requirements,
      tests_require=test_requirements,
      extras_require={
          'test': test_requirements
      },
      include_package_data=True,
      keywords='Python, Python3, color, print, unicode, encoding',
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'Natural Language :: English',
                   'License :: OSI Approved :: MIT License',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.6',
                   'Programming Language :: Python :: 3.7',
                   'Topic :: Software Development :: Libraries',
                   'Topic :: Utilities'])
