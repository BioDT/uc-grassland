"""
Module Name: prep_weather_data.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: November, 2023
Description: Download weather data and prepare as needed for GRASSMIND input. 
"""

import argparse
from copernicus import data_processing as dprc


def prep_weather_data(
    data_sets,
    years,
    months,
    coordinates,
    deims_id,
):
    """
    Prepare weather data to be used as GRASSMIND input.

    Parameters:
        data_sets (list): List of data set names from which to download.
        years (list or None): List of years to process, or 'None' for default value.
        months (list or None): List of months to process, or 'None' for default value.
        coordinates (dict): Coordinates dictionary with 'lat' and 'lon', or 'None' using DEIMS.iD.
        deims_id (str or None): DEIMS.iD, or 'None' for default value.
    """
    if years is None:
        years = list(range(2013, 2023))  # list(range(..., ...))

    if months is None:
        months = list(range(1, 13))  # list(range(1, 13))

    if coordinates is None:
        if deims_id is None:
            deims_id = "102ae489-04e3-481d-97df-45905837dc1a"  # GCEF site
            # deims_id = "51d0598a-e9e1-4252-8850-60fc8f329aab"  # test Veronika
            # deims_id = "474916b5-8734-407f-9179-109083c031d8"  # Doode Bemde site, Belgium

    # Final resolution as needed for GRASSMIND.
    final_resolution = "daily"

    dprc.data_processing(
        data_sets,
        final_resolution,
        years,
        months,
        coordinates,
        deims_id,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Set default arguments for calling the script."
    )

    # Define command-line arguments
    parser.add_argument(
        "--data_sets",
        nargs="*",
        default=["reanalysis-era5-land"],
        help="List of data sets",
    )
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
        data_sets=args.data_sets,
        years=args.years,
        months=args.months,
        coordinates=args.coordinates,
        deims_id=args.deims_id,
    )


if __name__ == "__main__":
    main()
