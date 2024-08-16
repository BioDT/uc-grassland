#!/bin/bash
#SBATCH --account=project_465000915
#SBATCH --job-name=grassland-test 
#SBATCH --nodes=1 
#SBATCH --ntasks-per-node=1 
#SBATCH --cpus-per-task=1 
#SBATCH --mem-per-cpu=1G 
#SBATCH --partition=debug 
#SBATCH --time=00:30:00

source .venv/bin/activate
python scripts/check_if_grassland.py --map_key="GER_Preidl"    # "EUR_hrl_grassland"