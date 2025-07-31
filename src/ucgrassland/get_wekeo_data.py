"""
Module Name: get_wekeo_data.py
Description: Request and download Copernicus data from WEkEO.

Developed by Thomas Banitz (UFZ) with contributions by Franziska Taubert (UFZ).

Copyright (C) 2025
- Helmholtz Centre for Environmental Research GmbH - UFZ, Germany

Licensed under the EUPL, Version 1.2 or - as soon they will be approved
by the European Commission - subsequent versions of the EUPL (the "Licence").
You may not use this work except in compliance with the Licence.

You may obtain a copy of the Licence at:
https://joinup.ec.europa.eu/software/page/eupl

Data sources:
   High Resolution Layer Grasslands product is part of the European Union’s Copernicus Land Monitoring Service.'


   "Grass cover within the context of the products is understood as herbaceous vegetation with at least 30% ground
    cover and with at least 30% graminoid species such as Poaceae, Cyperaceae and Juncaceae. Additional non-woody
    plants such as lichens, mosses and ferns can be tolerated."
"""

import zipfile
from pathlib import Path
from types import MappingProxyType

import hda
from copernicus.utils import get_area_coordinates

from ucgrassland.logger_config import logger

HDA_PRODUCT_TYPES = MappingProxyType(
    {
        "hda_grassland": "Grassland",
        "hda_herb_cover": "Herbaceous Cover",
        "hda_mowing_events": "Grassland Mowing Events",
        "hda_mowing_dates": "Grassland Mowing Dates (4 Dates per Year)",
    }
)


def create_hda_client(hda_configuration_folder=None):
    """
    Create a HDA client for accessing the Copernicus High-Resolution Layers (HRL) data.

    Creates a configuration file (.hdarc) containing user credentials (username and password)
    in the user's home directory if it does not already exist.

    Parameters:
        hda_configuration_folder (str or Path, optional): Path to the folder where the .hdarc file should be created.
            If None, the default is the user's home directory.

    Returns:
        hda.Client: An instance of the HDA client configured with the user's credentials.
    """
    hdarc_file = (
        Path(Path.home() / ".hdarc")
        if hda_configuration_folder is None
        else Path(hda_configuration_folder) / ".hdarc"
    )

    # Create hda configuration file (only if it does not already exist)
    if not hdarc_file.is_file():
        import getpass

        USERNAME = input("Enter your username: ")
        PASSWORD = getpass.getpass("Enter your password: ")

        with open(Path.home() / ".hdarc", "w") as f:
            f.write(f"user:{USERNAME}\n")
            f.write(f"password:{PASSWORD}\n")

    hda_client = hda.Client()

    return hda_client


def request_hda_grassland_data(
    map_key,
    year,
    coordinates_list,
    *,
    dataset_id="EO:EEA:DAT:HRL:GRA",
    resolution="10m",
    target_folder="hdaDataRaw",
    max_files=100,
):
    """
    Request and download High Resolution Layer (HRL) grassland data from WEkEO by HDA API.

    Parameters:
        map_key (str): Key to identify the type of HDA data to request.
        year (int): Year for which the HDA data is requested.
        coordinates_list (list): List of dictionaries containing latitude and longitude coordinates.
        dataset_id (str): Dataset ID for the HDA data (default is "EO:EEA:DAT:HRL:GRA").
        resolution (str): Resolution of the data to be requested (default is "10m").
        years_available (list): List of years for which data is available (default includes 2015, 2017-2021).
        target_folder (str or Path): Folder where the downloaded data will be stored (default is "hdaDataRaw").
        max_files (int): Maximum number of files to download (default is 100).

    Returns:
        tuple: A tuple containing:
            - hda_file_stems (list): List of file stems of the downloaded HDA data.
            - time_stamp (str): Timestamp of the request in ISO format.
    """
    target_folder = Path(target_folder)

    if map_key == "hda_grassland":
        years_available = [2015, 2017, 2018, 2019, 2020, 2021]
    else:
        years_available = [2017, 2018, 2019, 2020, 2021]

    if year in years_available:
        if year == 2015 and resolution == "10m":
            # Note: also 20m resolution seems not downloadable for 2015
            logger.warning(
                "HDA grassland data for 2015 is only available at 20m or 100m resolution. "
                "Using 20m resolution instead of 10m."
            )
            resolution = "20m"

        if map_key in HDA_PRODUCT_TYPES.keys():
            # Get area (bounding box) of all coordinates
            area_coordinates = get_area_coordinates(coordinates_list)
            hda_file_stems = []

            # Create target folder if it does not exist
            if not target_folder.is_dir():
                logger.info(f"Creating target folder: {target_folder}...")
                target_folder.mkdir(parents=True, exist_ok=True)

            # Request HDA data
            hda_client = create_hda_client()  # create HDA client
            logger.info(
                f"Looking for HDA data for map_key '{map_key}', year '{year}', and area: {area_coordinates} "
                f"from '{hda_client.dataset(dataset_id)['metadata']['_source']['datasetTitle']}' dataset..."
            )
            request = {
                "dataset_id": dataset_id,
                "product_type": HDA_PRODUCT_TYPES[map_key],
                "resolution": resolution,
                "year": year,
                "bbox": [
                    area_coordinates["lon_start"],
                    area_coordinates["lat_start"],
                    area_coordinates["lon_end"],
                    area_coordinates["lat_end"],
                ],
                "itemsPerPage": 200,
                "startIndex": 0,
            }
            matches = hda_client.search(request)
            file_count = len(matches)

            if file_count == 0:
                logger.warning(
                    f"No data found for map_key '{map_key}' and year '{year}' in the specified area."
                )
                return hda_file_stems

            if file_count > max_files:
                logger.warning(
                    f"More than {max_files} files found ({file_count} files) for map_key '{map_key}' and year '{year}' in the specified area. "
                    f"Using only the first {max_files} files."
                )
                file_count = max_files

            # Download files, if not already existing in the target folder
            for match in matches:
                hda_file_stem = match.results[0]["id"]
                hda_file_stems.append(hda_file_stem)
                hda_file_tif = Path(target_folder / f"{hda_file_stem}.tif")

                if not hda_file_tif.is_file():
                    logger.info(
                        f"Downloading '{hda_file_stem + '.zip'}' to '{target_folder}'..."
                    )
                    match.download(download_dir=target_folder)
                    hda_file_zip = Path(target_folder / f"{hda_file_stem}.zip")

                    if hda_file_zip.is_file():
                        logger.info(f"Extracting files from '{hda_file_zip}' ...")

                        with zipfile.ZipFile(hda_file_zip, "r") as zip_ref:
                            for file_type in [".tif", ".tif.aux.xml"]:
                                files_found = [
                                    name
                                    for name in zip_ref.namelist()
                                    if name.endswith(file_type)
                                ]

                                if len(files_found) == 1:
                                    extracted_path = zip_ref.extract(
                                        files_found[0], target_folder
                                    )
                                    logger.info(f"Extracted '{extracted_path}'.")
                                elif len(files_found) == 0:
                                    logger.warning(
                                        f"No {file_type} file found in the zip file '{hda_file_zip.name}'. Skipping extraction."
                                    )
                                else:
                                    logger.warning(
                                        f"Multiple {file_type} files found in the zip file '{hda_file_zip.name}'. Skipping extraction."
                                    )

                        # Remove the zip file after extraction
                        hda_file_zip.unlink(missing_ok=True)
                        logger.info(f"Removed zip file '{hda_file_zip}'.")
        else:
            try:
                raise ValueError(
                    f"Invalid map_key '{map_key}'. Valid keys are: {list(HDA_PRODUCT_TYPES.keys())}"
                )
            except ValueError as e:
                logger.error(e)
                return []
    else:
        try:
            raise ValueError(
                f"Invalid year '{year}'. Valid years are: {years_available}"
            )
        except ValueError as e:
            logger.error(e)
            return []

    return hda_file_stems


def main():
    # Example usage
    map_key = "hda_grassland"
    year = 2021
    # # example: GCEF small scale difference
    coordinates_list = [
        {"lat": 51.390427, "lon": 11.876855},  # GER, GCEF grassland site
        {"lat": 51.392331, "lon": 11.883838},  # GER, GCEF grassland site
        {
            "lat": 51.3919,
            "lon": 11.8787,
        },  # GER, GCEF grassland site, centroid, non-grassland in HRL
        {"lat": 54.94, "lon": 14.23},  # test for larger are
    ]

    hda_file_stems, time_stamp = request_hda_grassland_data(
        map_key, year, coordinates_list
    )

    print(f"HDA File Stems: {hda_file_stems}")
    print(f"Timestamp: {time_stamp}")


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
