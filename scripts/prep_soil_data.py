"""
Module Name: prep_soil_data.py
Description: Download soil data and prepare as needed for grassland model input.

Copyright (C) 2024
- Thomas Banitz, Franziska Taubert, Helmholtz Centre for Environmental Research GmbH - UFZ, Leipzig, Germany
- Tuomas Rossi, CSC – IT Center for Science Ltd., Espoo, Finland

Licensed under the EUPL, Version 1.2 or - as soon they will be approved
by the European Commission - subsequent versions of the EUPL (the "Licence").
You may not use this work except in compliance with the Licence.

You may obtain a copy of the Licence at:
https://joinup.ec.europa.eu/software/page/eupl
"""

import argparse

import utils as ut
from soilgrids import data_processing as dprc


def prep_soil_data(
    coordinates,
    deims_id,
    file_name=None,
):
    """
    Prepare soil data to be used as grassland model input.

    Parameters:
        coordinates (dict): Coordinates dictionary with 'lat' and 'lon', or 'None' using DEIMS.iD.
        deims_id (str or None): DEIMS.iD, or 'None' for default value.
        file_name (str or Path): File name to save soil data (default is None, default file name is used if not provided).
    """

    if coordinates is not None:
        if "lat" in coordinates and "lon" in coordinates:
            dprc.data_processing(coordinates, file_name=file_name)
        else:
            raise ValueError(
                "Coordinates not correctly defined. Please provide as dictionary ({'lat': float, 'lon': float})!"
            )
    else:
        # Several example coordinates

        # # example: Jena experiment
        # coordinates = {"lat": 50.95132596412849, "lon": 11.621566774599533}

        # # example: GiFACE
        # coordinates = {"lat": 50.53262187949219, "lon": 8.684426520889202}

        # example: GCEF small scale difference
        coordinates = {"lat": 51.390427, "lon": 11.876855}  # GER, GCEF grassland site
        coordinates = {"lat": 51.392331, "lon": 11.883838}  # GER, GCEF grassland site
        coordinates = {
            "lat": 51.3919,
            "lon": 11.8787,
        }  # GER, GCEF grassland site, centroid, non-grassland in HRL

        # example: locations with missing data in one but not both of the sources
        # no soilgrids, hhs available
        coordinates = {"lat": 50.311208, "lon": 9.448670}
        # soilgrids available, no hhs
        coordinates_list = [
            {"lat": 50.279263, "lon": 9.367577},
            {"lat": 50.134160, "lon": 8.940724},
            {"lat": 50.188000, "lon": 9.134750},
            {"lat": 50.134200, "lon": 8.941430},
        ]

        for coordinates in coordinates_list:
            dprc.data_processing(coordinates)

        # example: call with single deims_id
        coordinates = None
        if deims_id is None:
            deims_id = "102ae489-04e3-481d-97df-45905837dc1a"  # GCEF site

        if coordinates is None:
            if deims_id:
                coordinates = ut.get_deims_coordinates(deims_id)
            else:
                raise ValueError(
                    "No location defined. Please provide coordinates or DEIMS.iD!"
                )

        # # quick test for local cache file
        # hhs_cache = "c:/_D/biodt_data/soilMapsHiHydroSoil"
        # dprc.data_processing(coordinates, hhs_cache=hhs_cache)

        dprc.data_processing(coordinates)

        # example: get multiple coordinates from DEIMS.iDs from XLS file
        sites_file_name = (
            ut.get_package_root() / "grasslandSites" / "_elter_call_sites.xlsx"
        )
        locations = ut.get_deims_ids_from_xls(sites_file_name, header_row=1)

        for location in locations:
            coordinates = ut.get_deims_coordinates(location["deims_id"])
            dprc.data_processing(coordinates)


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
