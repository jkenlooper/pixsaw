# https://packaging.python.org/en/latest/distributing.html
from setuptools import setup, find_packages
import os

name = "pixsaw"

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name=name,
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
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
        'Programming Language :: Python :: 2.6',
        'Topic :: Software Development :: Build Tools',
        'Environment :: Web Environment',
        ],
    package_dir={'': 'src'},
    packages=find_packages('src'),
    zip_safe=False,
    install_requires=[
        'Pillow',
      ],
    entry_points="""
    [console_scripts]
    pixsaw = pixsaw.script:main
    """,
)
