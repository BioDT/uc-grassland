#!/usr/bin/env bash
# Bash equivalent of the Windows batch script excerpt
# Requires environment variables: LAT, LON, startYear, endYear, DEIMS

set -e  # Exit on error

# Check required environment variables
if [ -z "$LAT" ] || [ -z "$LON" ] || [ -z "$startYear" ] || [ -z "$endYear" ]; then
    echo "Error: Required environment variables not set"
    echo "Usage: LAT=<lat> LON=<lon> startYear=<year> endYear=<year> DEIMS=<deims_id> $0"
    exit 1
fi

# DEIMS is optional, default to empty string
DEIMS="${DEIMS:-}"

# Check for CDS API credentials (required for Copernicus weather data)
if [ -z "$CDSAPI_KEY" ]; then
    echo "Error: CDS API credentials not found"
    echo "The script needs Copernicus Climate Data Store (CDS) API credentials to download weather data."
    echo ""
    echo "Set environment variables:"
    echo "  export CDSAPI_URL=\"https://cds.climate.copernicus.eu/api\""
    echo "  export CDSAPI_KEY=\"YOUR_API_KEY\""
    echo ""
    echo "Get your credentials from: https://cds.climate.copernicus.eu/how-to-api"
    exit 1
fi

echo "Running with LAT=$LAT, LON=$LON, startYear=$startYear, endYear=$endYear, DEIMS=$DEIMS"

####################################
## create input data ##############
####################################

cd scenarios
python <<EOF
from ucgrassland import prep_grassland_model_input_data
prep_grassland_model_input_data([{'lat': ${LAT}, 'lon': ${LON}}], ${startYear}, ${endYear})
EOF

cd ..
cp -r "scenarios/grasslandModelInputFiles/lat${LAT}_lon${LON}" "scenarios/lat${LAT}_lon${LON}"

rm -rf scenarios/grasslandModelInputFiles

####################################
## create & modify config ##########
####################################

cd simulations
mkdir -p "project_${LAT}_${LON}"
cp "project_template/latLAT_lonLON__startYear-01-01_endYear-12-31__configuration__generic_v1.txt" "project_${LAT}_${LON}/"
cp "project_template/latLAT_lonLON__startYear-01-01_endYear-12-31__outputWritingDates.txt" "project_${LAT}_${LON}/"
cp "project_template/runSimulation.cmd" "project_${LAT}_${LON}/" 2>/dev/null || true

cd "project_${LAT}_${LON}"
configDir="$(pwd)"

# Rename the template files with actual coordinates and dates
mv "${configDir}/latLAT_lonLON__startYear-01-01_endYear-12-31__configuration__generic_v1.txt" \
   "${configDir}/lat${LAT}_lon${LON}__${startYear}-01-01_${endYear}-12-31__configuration__generic_v1.txt"

mv "${configDir}/latLAT_lonLON__startYear-01-01_endYear-12-31__outputWritingDates.txt" \
   "${configDir}/lat${LAT}_lon${LON}__${startYear}-01-01_${endYear}-12-31__outputWritingDates.txt"

# Run the config modification script
python ../modifyConfig.py "$LAT" "$LON" "$startYear" "$endYear" "$DEIMS"

####################################
####### run the simulation #########
####################################

python ../runReplicatedSimulations.py "$LAT" "$LON" "$startYear" "$endYear"

echo "Simulation completed successfully!"

mkdir -p /output/simulations/project_lat${LAT}_lon${LON}
cp -r ./* /output/simulations/project_lat${LAT}_lon${LON}/ 2>/dev/null || true

mkdir -p /output/scenarios
cp -r /uc-grassland-model/scenarios/lat${LAT}_lon${LON}/* /output/scenarios/

# Save a copy of the parameters used by the model into the output folder so they are
# preserved alongside the simulation results. This will include any in-place edits
# performed by modifyConfig.py.
mkdir -p /output/parameters
cp -r /uc-grassland-model/parameters/* /output/parameters/ 2>/dev/null || true

echo "Results saved to ./output/"