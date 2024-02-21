"""
Module Name: prep_soil_data.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: February, 2024
Description: Download soil data and prepare as needed for GRASSMIND input. 
"""

import argparse
from soilgrids import data_processing as dprc


def prep_soil_data(
    coordinates,
    deims_id,
):
    """
    Prepare soil data to be used as GRASSMIND input.

    Parameters:
        coordinates (dict): Coordinates dictionary with 'lat' and 'lon', or 'None' using DEIMS.iD.
        deims_id (str or None): DEIMS.iD, or 'None' for default value.
    """

    if coordinates is None:
        if deims_id is None:
            deims_id = "102ae489-04e3-481d-97df-45905837dc1a"  # GCEF site

    dprc.data_processing(
        coordinates,
        deims_id,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Set default arguments for calling the script."
    )

    # Define command-line arguments
    parser.add_argument(
        "--coordinates",
        type=lambda s: dict(lat=float(s.split(",")[0]), lon=float(s.split(",")[1])),
        help="Coordinates as 'lat,lon'",
    )
    parser.add_argument("--deims_id", help="DEIMS.iD")

    args = parser.parse_args()

    prep_soil_data(
        coordinates=args.coordinates,
        deims_id=args.deims_id,
    )


if __name__ == "__main__":
    main()
