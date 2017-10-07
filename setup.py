import os
from setuptools import setup


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="yamlstruct",
    version="0",
    author="Dick Marinus",
    author_email="dick@mrns.nl",
    description=("YAML struct parser with simple heuristics"),
    license="GPL-3",
    keywords="YAML struct",
    packages=[
        'yamlstruct',
    ],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GPL-3 License",
    ],
    include_package_data=True,
    install_requires=[
        'PyYAML',
    ], )
