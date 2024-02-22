from setuptools import setup
from pathlib import Path

# Project metadata
name = "uc-grassland"
version = "0.1.0"
author = "Thomas Banitz, Franziska Taubert, Tuomas Rossi, BioDT"
description = "Run scripts for BioDT pDT Grassland"
url = "https://github.com/BioDT/uc-grassland"
license = "MIT"

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
    entry_points={
        "console_scripts": [
            "soilgrids_data_processing = soilgrids.data_processing:main"
        ]
    },
    install_requires=install_requires,
)
