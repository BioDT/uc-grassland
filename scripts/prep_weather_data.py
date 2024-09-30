"""
Module Name: prep_weather_data.py
Description: Download weather data and prepare as needed for grassland model input.

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

import utils as ut
from copernicus import data_processing as dprc


def prep_weather_data(
    years,
    months,
    coordinates,
    *,
    deims_id=None,
):
    """
    Prepare weather data to be used as grassland model input.

    Parameters:
        years (list or None): List of years to process, or 'None' for default value.
        months (list or None): List of months to process, or 'None' for default value.
        coordinates (dict): Coordinates dictionary with 'lat' and 'lon', or 'None' using DEIMS.iD.
        deims_id (str): DEIMS.iD (default is None).
    """
    if years is None:
        years = list(range(1998, 1999))  # list(range(..., 2023))

    if months is None:
        months = list(range(1, 13))  # list(range(1, 13))

    if coordinates:
        if "lat" in coordinates and "lon" in coordinates:
            dprc.data_processing(
                years,
                months,
                coordinates,
            )
        else:
            raise ValueError(
                "Coordinates not correctly defined. Please provide as dictionary ({'lat': float, 'lon': float})!"
            )
    elif deims_id:
        location = ut.get_deims_coordinates(deims_id)

        if location["found"]:
            dprc.data_processing(
                years,
                months,
                location,
            )
        else:
            raise ValueError(f"Coordinates for DEIMS.id '{deims_id}' not found!")
    else:
        # Example coordinates for testing

        # # # test location Samuel
        # coordinates = {"lat": 53.331387, "lon": 8.096045}
        # dprc.data_processing(
        #     years,
        #     months,
        #     coordinates,
        # )

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

        # for coordinates in coordinates_list:
        #     dprc.data_processing(years, months, coordinates)

        # deims_id = "102ae489-04e3-481d-97df-45905837dc1a"  # GCEF site
        # deims_id = "6ae2f712-9924-4d9c-b7e1-3ddffb30b8f1"  # Schrankogel, AT, 1994, 2004, 14
        deims_id = "4ac03ec3-39d9-4ca1-a925-b6c1ae80c90d"  # Hochschwab, AT,  1998, 2001, 02, 08, 15
        # deims_id = "51d0598a-e9e1-4252-8850-60fc8f329aab"  # test Veronika
        # deims_id = "474916b5-8734-407f-9179-109083c031d8"  # Doode Bemde site, Belgium
        location = ut.get_deims_coordinates(deims_id)

        if location["found"]:
            dprc.data_processing(
                years,
                months,
                location,
            )


def main():
    """
    Runs the script with default arguments for calling the script.
    """
    parser = argparse.ArgumentParser(
        description="Set default arguments for calling the script."
    )

    # Define command-line arguments
    parser.add_argument("--years", nargs="*", type=int, help="List of years")
    parser.add_argument("--months", nargs="*", type=int, help="List of months")
    parser.add_argument(
        "--coordinates",
        type=lambda s: dict(lat=float(s.split(",")[0]), lon=float(s.split(",")[1])),
        help="Coordinates as 'lat,lon'",
    )
    parser.add_argument("--deims_id", help="DEIMS.iD")
    args = parser.parse_args()
    prep_weather_data(
        years=args.years,
        months=args.months,
        coordinates=args.coordinates,
        deims_id=args.deims_id,
    )


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
