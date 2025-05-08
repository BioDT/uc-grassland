from setuptools import find_packages, setup

# Project metadata
name = "ucgrassland"
version = "0.1.0"
author = "Thomas Banitz, Franziska Taubert, Tuomas Rossi, Taimur Haider Khan, BioDT"
description = "Run scripts for BioDT pDT Grassland"
url = "https://github.com/BioDT/uc-grassland"
license = "EUPL v1.2"

# Specify project dependencies from a requirements.txt file
with open("requirements.txt", "r") as req_file:
    install_requires = req_file.readlines()

# Setup configurationpip
setup(
    name=name,
    version=version,
    author=author,
    description=description,
    url=url,
    license=license,
    install_requires=install_requires,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
