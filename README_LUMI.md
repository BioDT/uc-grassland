# Usage on LUMI

## First time setup

Clone the git repository:

    git clone git@github.com:BioDT/uc-grassland.git /scratch/project_465000915/$USER/uc-grassland

Create a Python virtual environment:

    cd /scratch/project_465000915/$USER/uc-grassland
    module load cray-python/3.10.10
    python3 -m venv --system-site-packages .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -e .
    pip install git+ssh://git@github.com/BioDT/general-copernicus-weather-data.git@main
