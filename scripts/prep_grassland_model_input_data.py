"""
Module Name: prep_grassland_model_input_data.py
Description: Download all input data and prepare as needed for grassland model simulations.

Copyright (C) 2024
- Thomas Banitz, Franziska Taubert, Helmholtz Centre for Environmental Research GmbH - UFZ, Leipzig, Germany
- Tuomas Rossi, CSC – IT Center for Science Ltd., Espoo, Finland

Licensed under the EUPL, Version 1.2 or - as soon they will be approved
by the European Commission - subsequent versions of the EUPL (the "Licence").
You may not use this work except in compliance with the Licence.

You may obtain a copy of the Licence at:
https://joinup.ec.europa.eu/software/page/eupl

This project has received funding from the European Union's Horizon Europe Research and Innovation
Programme under grant agreement No 101057437 (BioDT project, https://doi.org/10.3030/101057437).
The authors acknowledge the EuroHPC Joint Undertaking and CSC – IT Center for Science Ltd., Finland
for awarding this project access to the EuroHPC supercomputer LUMI, hosted by CSC – IT Center for
Science Ltd., Finlande and the LUMI consortium through a EuroHPC Development Access call.
"""

import argparse
import warnings
from pathlib import Path

import check_if_grassland
import prep_management_data
import prep_soil_data
import utils as ut


def data_processing(location, years):
    """ """
    if location["coordinates"]:
        # init dialogue
        print(
            f"Preparing input data for latitude: {location["coordinates"]["lat"]},",
            f"longitude: {location["coordinates"]["lon"]} ...",
        )

        # get location coordinates for file names and folder
        formatted_lat = f"lat{location['coordinates']['lat']:.6f}"
        formatted_lon = f"lon{location['coordinates']['lon']:.6f}"
        file_start = f"{formatted_lat}_{formatted_lon}"
        location_head_folder = Path(
            ut.get_package_root() / "grasslandModelInputFiles" / file_start
        )

        # check if grassland according to all available land cover maps
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
        if location["deims_id"]:
            land_cover_map_keys.append("EUR_eunis_habitat")

        for map_key in land_cover_map_keys:
            check_this_map = check_if_grassland.check_locations_for_grassland(
                [location], map_key
            )
            grassland_checks.append(check_this_map[0])

        file_name = (
            location_head_folder
            / "landCover"
            / f"{file_start}__grasslandCheck__allMaps.txt"
        )
        grassland_checks.sort(key=lambda x: x["map_year"])
        check_if_grassland.check_results_to_file(grassland_checks, file_name)

        # run weather script
        # TODO:

        # run soil script
        file_name = location_head_folder / "soil" / f"{file_start}__2020__soil.txt"
        prep_soil_data.prep_soil_data(
            location["coordinates"],
            None,  # deims_id
            file_name,
        )

        # run management script
        land_use_map_keys = ["GER_Lange", "GER_Schwieder"]
        fill_missing_data = "mean"
        mow_height = 0.05

        for map_key in land_use_map_keys:
            file_name = (
                location_head_folder
                / "management"
                / f"{file_start}__{years[0]}-01-01_{years[-1]}-12-31__management__{map_key}.txt"
            )
            prep_management_data.prep_management_data(
                map_key,
                fill_missing_data,
                mow_height,
                years,
                location["coordinates"],
                deims_id=None,
                file_name=file_name,
            )

        # finish dialogue
        print(
            f"Input data for latitude: {location['coordinates']['lat']},",
            f"longitude: {location['coordinates']['lon']} completed.",
        )
    else:
        warnings.warn(
            "Location coordinates missing! No input data generated.",
            UserWarning,
        )


def prep_grassland_model_input_data(locations, first_year, last_year):
    """ """
    first_year = int(first_year)
    last_year = int(last_year)
    years = list(range(first_year, last_year + 1))

    if last_year < first_year:
        warnings.warn(
            f"First year {first_year} is after last year {last_year}! Empty time period for generating input data defined."
        )

    if locations is None:
        # Example locations list
        locations = ut.parse_locations(
            "51.390427,11.876855;51.392331,11.883838;102ae489-04e3-481d-97df-45905837dc1a"
        )

        # # Example to get location coordinates via DEIMS.iDs from XLS file
        # file_name = ut.get_package_root() / "grasslandSites" / "_elter_call_sites.xlsx"
        # country_code = "DE"  # "DE" "AT"
        # locations = ut.get_deims_ids_from_xls(
        #     file_name, header_row=1, country=country_code
        # )

        # # Example to get location coordinates from CSV file (for single plots/stations)
        # file_name = ut.get_package_root() / "grasslandSites" / "DE_RhineMainObservatory_station.csv"
        # locations = ut.get_plot_locations_from_csv(file_name)

    for location in locations:
        if location.get("coordinates") is None:
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
        type=ut.parse_locations,
        help="List of locations, separated by ';', each as 'lat,lon' pair or 'DEIMS.iD'.",
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
    args = parser.parse_args()
    prep_grassland_model_input_data(
        locations=args.locations,
        first_year=args.first_year,
        last_year=args.last_year,
    )


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
