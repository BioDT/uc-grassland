"""
Module Name: prep_soil_data.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: February, 2024
Description: Download soil data and prepare as needed for GRASSMIND input. 
"""

import argparse
from soilgrids import data_processing as dprc
import utils as ut


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

    # # test Jena experiment
    # coordinates = {"lat": 50.95132596412849, "lon": 11.621566774599533}

    # # test GiFACE
    # coordinates = {"lat": 50.53262187949219, "lon": 8.684426520889202}

    # # test GCEF small scale difference
    # coordinates = {"lat": 51.390427, "lon": 11.876855}  # GER, GCEF grassland site
    # coordinates = {"lat": 51.392331, "lon": 11.883838}  # GER, GCEF grassland site
    # coordinates = {
    #     "lat": 51.3919,
    #     "lon": 11.8787,
    # }  # GER, GCEF grassland site, centroid, non-grassland in HRL

    # # Example call with single deims_id
    if coordinates is None:
        if deims_id is None:
            deims_id = "102ae489-04e3-481d-97df-45905837dc1a"  # GCEF site

    dprc.data_processing(coordinates, deims_id)

    # # test get multiple coordinates from DEIMS.iDs from XLS file
    # file_name = ut.get_package_root() / "grasslandSites" / "_elter_call_sites.xlsx"
    # locations = ut.get_deims_ids_from_xls(file_name, header_row=1)

    # for location in locations:
    #     dprc.data_processing(coordinates=None, deims_id=location["deims_id"])


def main():
    """
    Runs the script with default arguments for calling the script.
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
    parser.add_argument("--deims_id", help="DEIMS.iD")

    args = parser.parse_args()

    prep_soil_data(
        coordinates=args.coordinates,
        deims_id=args.deims_id,
    )


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
