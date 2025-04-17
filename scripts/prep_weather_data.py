"""
Module Name: prep_weather_data.py
Description: Download weather data and prepare as needed for grassland model input.

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

import utils as ut
from copernicus import data_processing as cop_dprc


def prep_weather_data(
    coordinates_list,
    years,
    *,
    months=list(range(1, 13)),
    download_whole_area=True,
    deims_id=None,
    target_folder="weatherDataPrepared",
):
    """
    Prepare weather data to be used as grassland model input.

    Parameters:
        coordinates (dict): Coordinates dictionary with 'lat' and 'lon', or 'None' using DEIMS.iD.
        years (list or None): List of years to process.
        months (list or None): List of months to process (default is [1, 2, ... 12]).
        deims_id (str): DEIMS.iD (default is None).
        target_folder (str or Path): Target folder for .txt files (default is 'weatherDataPrepared').
    """
    if years is None:
        years = list(range(1998, 1999))
        # years = list(range(1999, 2011))  # list(range(..., 2023))

    if coordinates_list:
        cop_dprc(
            years,
            coordinates_list,
            months=months,
            download_whole_area=download_whole_area,
            target_folder=target_folder,
        )
    elif deims_id:
        location = ut.get_deims_coordinates(deims_id)

        if location["found"]:
            cop_dprc(
                years,
                [location],
                months=months,
                download_whole_area=False,
                target_folder=target_folder,
            )
        else:
            raise ValueError(f"Coordinates for DEIMS.id '{deims_id}' not found!")
    else:
        # Example coordinates lists for testing

        # # # test location Samuel
        # coordinates = {"lat": 53.331387, "lon": 8.096045}

        # # test locations with larger time zone offset, eastern and western
        # coordinates_list = [
        #     # {"lat": 53, "lon": 48},
        #     {"lat": 53, "lon": -70},
        # ]

        # coordinates_list = [
        #     {"lat": 47.622021, "lon": 15.149292},
        #     {"lat": 47.622030, "lon": 15.149292},
        #     {"lat": 47.622120, "lon": 15.149292},
        #     {"lat": 47.623020, "lon": 15.149292},
        #     {"lat": 47.632020, "lon": 15.149292},
        #     {"lat": 47.722020, "lon": 15.149292},
        #     {"lat": 47.622019, "lon": 15.149292},
        #     {"lat": 47.622010, "lon": 15.149292},
        #     {"lat": 47.621920, "lon": 15.149292},
        #     {"lat": 47.621020, "lon": 15.149292},
        #     {"lat": 47.612020, "lon": 15.149292},
        #     {"lat": 47.522020, "lon": 15.149292},
        # ]

        # # example: GCEF small scale difference
        coordinates_list = [
            {"lat": 51.390427, "lon": 11.876855},  # GER, GCEF grassland site
            {"lat": 51.392331, "lon": 11.883838},  # GER, GCEF grassland site
            {
                "lat": 51.3919,
                "lon": 11.8787,
            },  # GER, GCEF grassland site, centroid, non-grassland in HRL
        ]

        cop_dprc(
            years,
            coordinates_list,
            months=months,
            download_whole_area=download_whole_area,
            target_folder=target_folder,
        )

        # deims_id = "102ae489-04e3-481d-97df-45905837dc1a"  # GCEF site
        # deims_id = "6ae2f712-9924-4d9c-b7e1-3ddffb30b8f1"  # Schrankogel, AT, 1994, 2004, 14
        deims_id = "4ac03ec3-39d9-4ca1-a925-b6c1ae80c90d"  # Hochschwab, AT,  1998, 2001, 02, 08, 15
        # # deims_id = "51d0598a-e9e1-4252-8850-60fc8f329aab"  # test Veronika
        # # deims_id = "474916b5-8734-407f-9179-109083c031d8"  # Doode Bemde site, Belgium
        location = ut.get_deims_coordinates(deims_id)

        if location["found"]:
            cop_dprc(
                years,
                [location],
                months=months,
                download_whole_area=False,
                target_folder=target_folder,
            )


def main():
    """
    Runs the script with default arguments for calling the script.
    """
    parser = argparse.ArgumentParser(
        description="Set default arguments for calling the script."
    )

    # Define command-line arguments
    parser.add_argument(
        "--coordinates_list",
        type=list,
        help="List of coordinates dictionaries with 'lat' and 'lon' keys.",
    )
    parser.add_argument("--years", type=list, help="List of years")
    parser.add_argument(
        "--months",
        type=list,
        default=list(range(1, 13)),
        help="List of months",
    )
    parser.add_argument(
        "--download_single_locations",
        action="store_false",
        dest="download_whole_area",
        help="Download single locations separately instead of whole area covering all coordinates in the list (default is False).",
    )
    parser.add_argument("--deims_id", help="DEIMS.iD")
    parser.add_argument(
        "--target_folder",
        default="weatherDataPrepared",
        help="Target folder for prepared weather data.",
    )
    args = parser.parse_args()
    prep_weather_data(
        coordinates_list=args.coordinates_list,
        years=args.years,
        months=args.months,
        download_whole_area=args.download_whole_area,
        deims_id=args.deims_id,
        target_folder=args.target_folder,
    )


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
