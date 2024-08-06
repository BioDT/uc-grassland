"""
Module Name: prep_grassmind_input_data.py
Author: Thomas Banitz, Franziska Taubert, BioDT
Date: August, 2024
Description: Download all input data and prepare as needed for GRASSMIND simulations.
             
Uses:   check_if_grassland.py
        prep_weather_data.py
        prep_soil_data.py
        prep_management_data.py
"""

import argparse
import check_if_grassland
import prep_soil_data
import utils as ut
import warnings


def data_processing(location, years):
    """
    
    """
    

    # init dialogue
    if location["coordinates"]:                
        print(f"Preparing input data for latitude: {location["coordinates"]["lat"]},",
              f"longitude: {location["coordinates"]["lon"]}...")
        
        # location for file names
        formatted_lat = f"lat{location["coordinates"]["lat"]:.6f}"  
        formatted_lon = f"lon{location["coordinates"]["lat"]:.6f}"  
        file_start = f"{formatted_lat}_{formatted_lon}"
        grassland_checks = []

        # check if grassland according to all available land cover maps
        land_cover_map_keys = [
            "HRL_Grassland",
            "EUR_Pflugmacher",
            "GER_Preidl",
            "GER_Schwieder_2017",
            "GER_Schwieder_2018",
            "GER_Schwieder_2019",
            "GER_Schwieder_2020",
            "GER_Schwieder_2021",
            "GER_Lange_2017", 
            # "GER_Lange_2018", only 1 map needed as both use German ATKIS digital landscape model 2015 
        ]
        
        # "eunisHabitat" only works for DEIMS.iDs
        if location["deims_id"]:
            land_cover_map_keys.append("eunisHabitat")

        for map_key in land_cover_map_keys:
            check_this_map = check_if_grassland.check_locations_for_grassland([location], map_key)
            grassland_checks.append(check_this_map[0])    

        file_name = (
            ut.get_package_root()
            / "landCoverCheckResults"
            / f"{file_start}__grasslandCheck__allMaps.txt"
        )
        check_if_grassland.check_results_to_file(grassland_checks, file_name)

        # run weather script

        # run soil script

        prep_soil_data.prep_soil_data(
            location["coordinates"],
            deims_id=None,
        )
        # run management script

        # prep_management_data(
        #     map_key=args.map_key,
        #     fill_missing_data=args.fill_missing_data,
        #     mow_height=args.mow_height,
        #     years=args.years,
        #     coordinates=args.coordinates,
        #     deims_id=args.deims_id,
        # )

        # move files to folder for location with subfolder structure for grassmind

        # finish dialogue
    else:
        warnings.warn(
            "Location coordinates missing! No input data generated.",
            UserWarning,
        )


def prep_grassmind_input_data(locations, first_year, last_year):
    """ """
    first_year = int(first_year)
    last_year = int(last_year)
    years = list(range(first_year, last_year + 1))

    if last_year < first_year:
        warnings.warn(
            f"First year {first_year} is after last year {last_year}! Empty time period for generating input data defined."
        )

    for location in locations:
        if location["coordinates"] is None:
            if location["deims_id"]:
                location["coordinates"] = ut.get_deims_coordinates(location["deims_id"])
            else:
                raise ValueError(
                    "No location defined. Please provide coordinates or DEIMS.iD!"
                )

        data_processing(location, years)


def main():
    """
    Run script with default arguments for calling the script.
    """
    parser = argparse.ArgumentParser(
        description="Set default arguments for calling the script."
    )

    # Define command-line arguments
    parser.add_argument(
        "--locations",
        default="51.390427,11.876855;51.392331,11.883838;102ae489-04e3-481d-97df-45905837dc1a",
        type=ut.parse_locations,
        help="List of locations, separated by ';', each as 'lat,lon' pair or 'DEIMS.iD'.",
    )
    parser.add_argument(
        "--first_year",
        default=2017,
        type=int,
        help="First year for which to generate input data.",
    )
    parser.add_argument(
        "--last_year",
        default=2014,
        type=int,
        help="Last year for which to generate input data.",
    )

    args = parser.parse_args()

    prep_grassmind_input_data(
        locations=args.locations,
        first_year=args.first_year,
        last_year=args.last_year,
    )


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
