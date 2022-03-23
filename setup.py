# https://packaging.python.org/en/latest/distributing.html
from setuptools import setup, find_packages
import os

__version__ = "0.3.3"  # Also set in src/pixsaw/_version.py

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
    license="LGPLv3+",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Build Tools',
        'Environment :: Web Environment',
        ],
    package_dir={'': 'src'},
    packages=find_packages('src'),
    zip_safe=False,
    install_requires=[
        'future',
        'Pillow >= 8.4.0, < 10',
      ],
    entry_points="""
    [console_scripts]
    pixsaw = pixsaw.script:main
    """,
)
