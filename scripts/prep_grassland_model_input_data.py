"""
Module Name: prep_grassland_model_input_data.py
Description: Download all input data and prepare as needed for grassland model simulations.

Developed in the BioDT project by Thomas Banitz (UFZ) with contributions by Franziska Taubert (UFZ)
and Tuomas Rossi (CSC).

Copyright (C) 2024
- Helmholtz Centre for Environmental Research GmbH - UFZ, Germany
- CSC - IT Center for Science Ltd., Finland

Licensed under the EUPL, Version 1.2 or - as soon they will be approved
by the European Commission - subsequent versions of the EUPL (the "Licence").
You may not use this work except in compliance with the Licence.

You may obtain a copy of the Licence at:
https://joinup.ec.europa.eu/software/page/eupl

This project has received funding from the European Union's Horizon Europe Research and Innovation
Programme under grant agreement No 101057437 (BioDT project, https://doi.org/10.3030/101057437).
The authors acknowledge the EuroHPC Joint Undertaking and CSC - IT Center for Science Ltd., Finland
for awarding this project access to the EuroHPC supercomputer LUMI, hosted by CSC - IT Center for
Science Ltd., Finland and the LUMI consortium through a EuroHPC Development Access call.
"""

import argparse
import warnings
from pathlib import Path

import check_if_grassland
import prep_management_data
import prep_soil_data
import prep_weather_data
import utils as ut


def data_processing(coordinates, years):
    """
    Process data to be used as grassland site information and model input:
        checks if the location is grassland according to different land cover sources,
        downloads and prepares weather data,
        downloads and prepares soil data,
        downloads and prepares management data.

    Parameters:
        coordinates (list of dict): List of dictionaries with 'lat' and 'lon' keys.
        years (list of int): Years list.
    """
    if "lat" in coordinates and "lon" in coordinates:
        # Init dialogue
        print(
            f"Preparing input data for latitude: {coordinates['lat']},",
            f"longitude: {coordinates['lon']} ...",
        )

        # Get location coordinates for file names and folder
        formatted_lat = f"lat{coordinates['lat']:.6f}"
        formatted_lon = f"lon{coordinates['lon']:.6f}"
        file_start = f"{formatted_lat}_{formatted_lon}"
        location_head_folder = Path(
            ut.get_package_root() / "grasslandModelInputFiles" / file_start
        )

        # Check if grassland according to all available land cover maps
        grassland_checks = []
        land_cover_map_keys = [
            "EUR_hrl_grassland",
            "EUR_Pflugmacher",
            "GER_Preidl",
            "GER_Schwieder_2017",
            "GER_Schwieder_2018",
            "GER_Schwieder_2019",
            "GER_Schwieder_2020",
            "GER_Schwieder_2021",
            "GER_Lange_2017",
            # "GER_Lange_2018", only 1 GER_Lange map needed as both use German ATKIS digital landscape model 2015
        ]

        # "EUR_eunis_habitat" only works for DEIMS.iDs
        if coordinates.get("deims_id"):
            land_cover_map_keys.append("EUR_eunis_habitat")

        for map_key in land_cover_map_keys:
            check_this_map = check_if_grassland.check_locations_for_grassland(
                [coordinates], map_key
            )
            grassland_checks.append(check_this_map[0])

        file_name = (
            location_head_folder
            / "landCover"
            / f"{file_start}__grasslandCheck__allMaps.txt"
        )
        grassland_checks.sort(key=lambda x: x["map_year"])
        check_if_grassland.check_results_to_file(grassland_checks, file_name=file_name)

        # Run weather script
        target_folder = location_head_folder / "weather"
        prep_weather_data.prep_weather_data(
            coordinates, years, target_folder=target_folder
        )

        # Run soil script
        file_name = location_head_folder / "soil" / f"{file_start}__2020__soil.txt"
        prep_soil_data.prep_soil_data(coordinates, file_name=file_name)

        # Run management script
        land_use_map_keys = ["GER_Lange", "GER_Schwieder"]

        for map_key in land_use_map_keys:
            file_name = (
                location_head_folder
                / "management"
                / f"{file_start}__{years[0]}-01-01_{years[-1]}-12-31__management__{map_key}.txt"
            )
            prep_management_data.prep_management_data(
                coordinates, years, map_key, file_name=file_name
            )

        # Finish dialogue
        print(
            f"Input data for latitude: {coordinates['lat']},",
            f"longitude: {coordinates['lon']} completed.",
        )
    else:
        warnings.warn(
            "Coordinates not correctly defined. Please provide as dictionary ",
            "({'lat': float, 'lon': float})! No input data generated.",
            UserWarning,
        )


def prep_grassland_model_input_data(
    coordinates, first_year, last_year, *, deims_id=None
):
    """
    Prepare all necessary data to be used as grassland model input.

    Parameters:
        coordinates (dict): Coordinates dictionary with 'lat' and 'lon', or 'None' using DEIMS.iD.
        first_year (int): First year of desired time period.
        last_year (int): Last year of desired time period.
        deims_id (str): DEIMS.iD (default is None).
    """
    first_year = int(first_year)
    last_year = int(last_year)

    if last_year < first_year:
        warnings.warn(
            f"First year {first_year} is after last year {last_year}! Last year set to {first_year}."
        )
        last_year = first_year

    years = list(range(first_year, last_year + 1))

    if coordinates:
        if "lat" in coordinates and "lon" in coordinates:
            data_processing(coordinates, years)
        else:
            raise ValueError(
                "Coordinates not correctly defined. Please provide as dictionary ({'lat': float, 'lon': float})!"
            )
    elif deims_id:
        location = ut.get_deims_coordinates(deims_id)

        if location["found"]:
            data_processing(location, years)
        else:
            raise ValueError(f"Coordinates for DEIMS.id '{deims_id}' not found!")
    else:
        # Example locations list
        locations = ut.parse_locations(
            "51.390427,11.876855;51.392331,11.883838;102ae489-04e3-481d-97df-45905837dc1a"
        )

        # # Example to get location coordinates from CSV file (for single plots/stations)
        # file_name = (
        #     ut.get_package_root()
        #     / "grasslandSites"
        #     / "DE_RhineMainObservatory_station.csv"
        # )
        # # file_name = (
        # #     ut.get_package_root() / "grasslandSites" / "AT_Hochschwab_station.csv"
        # # )
        # years = list(range(1992, 2024))
        # locations = ut.get_plot_locations_from_csv(file_name)

        for location in locations:
            data_processing(location, years)

        # Example to get multiple coordinates from DEIMS.iDs from XLS file, filter only Germany
        sites_file_name = (
            ut.get_package_root() / "grasslandSites" / "_elter_call_sites.xlsx"
        )
        sites_ids = ut.get_deims_ids_from_xls(
            sites_file_name, header_row=1, country="AT"
        )
        # sites_ids = ["4ac03ec3-39d9-4ca1-a925-b6c1ae80c90d"]
        # Hochschwab, AT,  1998, 2001, 02, 08, 15

        for deims_id in sites_ids:
            location = ut.get_deims_coordinates(deims_id)

            if location["found"]:
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
        "--coordinates",
        type=lambda s: dict(lat=float(s.split(",")[0]), lon=float(s.split(",")[1])),
        help="Coordinates as 'lat,lon'",
    )
    parser.add_argument(
        "--first_year",
        default=2013,
        type=int,
        help="First year for which to generate input data.",
    )
    parser.add_argument(
        "--last_year",
        default=2023,
        type=int,
        help="Last year for which to generate input data.",
    )
    parser.add_argument("--deims_id", help="DEIMS.iD")
    args = parser.parse_args()
    prep_grassland_model_input_data(
        coordinates=args.coordinates,
        first_year=args.first_year,
        last_year=args.last_year,
        deims_id=args.deims_id,
    )


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
