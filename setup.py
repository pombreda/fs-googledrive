from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys

tests_require = [
    'pytest',
    'pytest-cache',
    'pytest-cov',
    'mock',
]

install_requires = [
    'fs',
    'PyDrive'
]


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name="pyfs-googledrive",
    version="0.0.1",
    author="Lukas Martinelli",
    author_email="me@lukasmartinelli.ch",
    maintainer='Lukas Martinelli',
    maintainer_email='me@lukasmartinelli.ch',
    url="https://github.com/lukasmartinelli/fs-googledrive",
    description=("PyFilesystem for GoogleDrive."),
    long_description=open('README.rst').read(),
    install_requires=install_requires,
    extras_require={
        'test': tests_require
    },
    tests_require=tests_require,
    cmdclass={'test': PyTest},
    py_modules=['googledrivefs'],
    license='GPLv2',
    keywords = "fs googledrive",
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ),
)
