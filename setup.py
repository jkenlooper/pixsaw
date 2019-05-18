# https://packaging.python.org/en/latest/distributing.html
from setuptools import setup, find_packages
import os

__version__ = "0.2.0" # Also set in src/pixsaw/_version.py

name = "pixsaw"

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name=name,
    version=__version__,
    author='Jake Hickenlooper',
    author_email='jake@weboftomorrow.com',
    description="Cut a picture into pieces by cutting along pixel lines",
    long_description=read('README.rst'),
    url='https://github.com/jkenlooper/pixsaw',
    license='GPL',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Build Tools',
        'Environment :: Web Environment',
        ],
    package_dir={'': 'src'},
    packages=find_packages('src'),
    zip_safe=False,
    install_requires=[
        'future',
        'Pillow < 7',
      ],
    entry_points="""
    [console_scripts]
    pixsaw = pixsaw.script:main
    """,
)
