"""
Module Name: prep_soil_data.py
Description: Download soil data and prepare as needed for grassland model input.

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

from soilgrids import get_soil_data

from ucgrassland import utils as ut
from ucgrassland.logger_config import logger


def prep_soil_data(coordinates, *, deims_id=None, file_name=None):
    """
    Prepare soil data to be used as grassland model input.

    Parameters:
        coordinates (dict): Coordinates dictionary with 'lat' and 'lon', or 'None' using DEIMS.iD.
        deims_id (str): DEIMS.iD (default is None).
        file_name (str or Path): File name to save soil data (default is None, default file name is used if not provided).
    """

    if coordinates:
        get_soil_data(coordinates, file_name=file_name)
    elif deims_id:
        location = ut.get_deims_coordinates(deims_id)

        if location["found"]:
            get_soil_data(location, file_name=file_name)
        else:
            try:
                raise ValueError(f"Coordinates for DEIMS.id '{deims_id}' not found.")
            except ValueError as e:
                logger.error(e)
                raise
    else:
        # Several example coordinates for testing

        # # example: Jena experiment
        # coordinates = {"lat": 50.95132596412849, "lon": 11.621566774599533}

        # # example: GiFACE
        # coordinates = {"lat": 50.53262187949219, "lon": 8.684426520889202}

        # example: GCEF small scale difference
        coordinates_list = [
            {"lat": 51.390427, "lon": 11.876855},  # GER, GCEF grassland site
            {"lat": 51.392331, "lon": 11.883838},  # GER, GCEF grassland site
            {
                "lat": 51.3919,
                "lon": 11.8787,
            },  # GER, GCEF grassland site, centroid, non-grassland in HRL
        ]

        # # example: locations with missing data in one but not both of the sources
        # # no soilgrids, hihydrosoil available
        # coordinates = {"lat": 50.311208, "lon": 9.448670}
        # get_soil_data(coordinates)

        # # soilgrids available, no hihydrosoil
        # coordinates_list = [
        #     {"lat": 50.279263, "lon": 9.367577},
        #     {"lat": 50.134160, "lon": 8.940724},
        #     {"lat": 50.188000, "lon": 9.134750},
        #     {"lat": 50.134200, "lon": 8.941430},
        # ]

        for coordinates in coordinates_list:
            get_soil_data(coordinates)

        # example: call with single deims_id
        deims_id = "102ae489-04e3-481d-97df-45905837dc1a"  # GCEF site
        location = ut.get_deims_coordinates(deims_id)

        if location["found"]:
            get_soil_data(location)

        # # example: get multiple coordinates from DEIMS.iDs from XLS file
        # sites_file_name = (
        #     Path.cwd() / "grasslandSites" / "_elter_call_sites.xlsx"
        # )
        # sites_ids = ut.get_deims_ids_from_xls(sites_file_name, header_row=1)

        # for deims_id in sites_ids:
        #     location = ut.get_deims_coordinates(deims_id)

        #     if location["found"]:
        #         get_soil_data(location)


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
    parser.add_argument("--file_name", help="File name to save soil data")
    args = parser.parse_args()
    prep_soil_data(
        coordinates=args.coordinates, deims_id=args.deims_id, file_name=args.file_name
    )


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
