# Usage on LUMI

## First time setup

## Clone the git repository:

    git clone git@github.com:BioDT/uc-grassland.git /scratch/project_465000915/$USER/uc-grassland

   ## same for other repositories needed
    git clone git@github.com:BioDT/general-copernicus-weather-data.git /scratch/project_465000915/$USER/general-copernicus-weather-data
    git clone git@github.com:BioDT/general-soilgrids-soil-data.git /scratch/project_465000915/$USER/general-soilgrids-soil-data

## Create a Python virtual environment:

    cd /scratch/project_465000915/$USER/uc-grassland
    module load cray-python/3.10.10
    python3 -m venv --system-site-packages .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -e .
    
   ## Install packages from cloned "local" folders to allow for instant updates
    pip install -e ../general-copernicus-weather-data
    pip install -e ../general-soilgrids-soil-data

   ## Alternative, install package once, updates require re-install
    pip install git+ssh://git@github.com/BioDT/general-copernicus-weather-data.git@main
    pip install git+ssh://git@github.com/BioDT/general-soilgrids-soil-data.git@main

## Run jobs
   sbatch example_submission_lumi.sh

   ## check status
   squeue --me
