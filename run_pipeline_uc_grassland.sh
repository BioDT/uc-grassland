#!/usr/bin/bash
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

# Format LAT and LON to 6 decimal places to match Python's formatting
# Python uses: f"lat{coordinates['lat']:.6f}" which always produces 6 decimals
LAT_FORMATTED=$(printf "%.6f" "$LAT")
LON_FORMATTED=$(printf "%.6f" "$LON")

echo "Running with LAT=$LAT_FORMATTED, LON=$LON_FORMATTED, startYear=$startYear, endYear=$endYear, DEIMS=$DEIMS"

####################################
## create input data ##############
####################################

cd /uc-grassland-model/scenarios
python <<EOF
from ucgrassland import prep_grassland_model_input_data
prep_grassland_model_input_data([{'lat': ${LAT_FORMATTED}, 'lon': ${LON_FORMATTED}}], ${startYear}, ${endYear})
EOF

cd /uc-grassland-model
cp -r "scenarios/grasslandModelInputFiles/lat${LAT_FORMATTED}_lon${LON_FORMATTED}" "scenarios/lat${LAT_FORMATTED}_lon${LON_FORMATTED}"

rm -rf scenarios/grasslandModelInputFiles

####################################
## create & modify config ##########
####################################

cd simulations
mkdir -p "project_${LAT_FORMATTED}_${LON_FORMATTED}"
cp "project_template/latLAT_lonLON__startYear-01-01_endYear-12-31__configuration__generic_v1.txt" "project_${LAT_FORMATTED}_${LON_FORMATTED}/"
cp "project_template/latLAT_lonLON__startYear-01-01_endYear-12-31__outputWritingDates.txt" "project_${LAT_FORMATTED}_${LON_FORMATTED}/"
cp "project_template/runSimulation.cmd" "project_${LAT_FORMATTED}_${LON_FORMATTED}/" 2>/dev/null || true

cd "project_${LAT_FORMATTED}_${LON_FORMATTED}"
configDir="$(pwd)"

# Rename the template files with actual coordinates and dates
mv "${configDir}/latLAT_lonLON__startYear-01-01_endYear-12-31__configuration__generic_v1.txt" \
   "${configDir}/lat${LAT_FORMATTED}_lon${LON_FORMATTED}__${startYear}-01-01_${endYear}-12-31__configuration__generic_v1.txt"

mv "${configDir}/latLAT_lonLON__startYear-01-01_endYear-12-31__outputWritingDates.txt" \
   "${configDir}/lat${LAT_FORMATTED}_lon${LON_FORMATTED}__${startYear}-01-01_${endYear}-12-31__outputWritingDates.txt"

# Run the config modification script
python ../modifyConfig.py "$LAT_FORMATTED" "$LON_FORMATTED" "$startYear" "$endYear" "$DEIMS"

####################################
####### run the simulation #########
####################################

python ../runReplicatedSimulations.py "$LAT_FORMATTED" "$LON_FORMATTED" "$startYear" "$endYear"

echo "Simulation completed successfully!"

mkdir -p /output/simulations/project_lat${LAT_FORMATTED}_lon${LON_FORMATTED}
cp -r ./* /output/simulations/project_lat${LAT_FORMATTED}_lon${LON_FORMATTED}/ 2>/dev/null || true

mkdir -p /output/scenarios
cp -r /uc-grassland-model/scenarios/lat${LAT_FORMATTED}_lon${LON_FORMATTED}/* /output/scenarios/

# Save a copy of the parameters used by the model into the output folder so they are
# preserved alongside the simulation results. This will include any in-place edits
# performed by modifyConfig.py.
mkdir -p /output/parameters
cp -r /uc-grassland-model/parameters/* /output/parameters/ 2>/dev/null || true

echo "Results saved to ./output/"

exit 0