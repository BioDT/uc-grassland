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
   European Union’s Copernicus Land Monitoring Service.
   High Resolution Layer Grasslands datasets:

    - Grassland 2017 - Present (raster 10m), Europe, yearly, Nov. 2024.
      https://doi.org/10.2909/0b6254bb-4c7d-41d9-8eae-c43b05ab2965.

    - Herbaceous cover 2017 - Present (raster 10m), Europe, yearly, Nov. 2024.
      https://doi.org/10.2909/9da6ca39-043a-4bdd-8d0a-41a7bed6e439.

    - Grassland Mowing Events 2017 - Present (raster 10m), Europe, yearly, Nov. 2024.
      https://doi.org/10.2909/114e8cae-1cd7-4adc-8c5f-a04863fc6af9.

    - Grassland Mowing Dates 2017 - Present (raster 10m), Europe, yearly – 4 layers, Nov. 2024
      https://doi.org/10.2909/660d00f1-c6de-4db6-9979-0be124ceb7f0.

    Dataset documentation: https://land.copernicus.eu/en/products/high-resolution-layer-grasslands

    Access via WEkEO HDA API Client:
    - Project page: https://pypi.org/project/hda/
    - Documentation: https://hda.readthedocs.io/en/latest/
    - License: Apache License 2.0, https://github.com/ecmwf/hda/blob/master/LICENSE.txt
"""

import time
import zipfile
from pathlib import Path
from types import MappingProxyType

import hda
from copernicus.utils import get_area_coordinates, upload_file_opendap

from ucgrassland.logger_config import logger
from ucgrassland.utils import (
    download_file_opendap,
    reproject_coordinates,
    set_no_data_value,
)

# # debug logging for inspecting API calls
# import logging
# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger("requests").setLevel(logging.DEBUG)
# logging.getLogger("hda").setLevel(logging.DEBUG)
# logging.getLogger("urllib3").setLevel(logging.DEBUG)

HDA_SPECS = MappingProxyType(
    {
        "EUR_hda_grassland": {
            "product_type": "Grassland",
            "no_data_value": 255,
            "file_starts": ["CLMS_HRLVLCC_GRA_S"],
        },
        "EUR_hda_herb_cover": {
            "product_type": "Herbaceous Cover",
            "no_data_value": "tbd",
            "file_starts": ["tbd"],
        },
        "EUR_hda_mowing_events": {
            "product_type": "Grassland Mowing Events",
            "no_data_value": 255,
            "file_starts": ["CLMS_HRLVLCC_GRAME_S"],
        },
        "EUR_hda_mowing_dates": {
            "product_type": "Grassland Mowing Dates (4 Dates per Year)",
            "no_data_value": 65535,
            "file_starts": [
                "CLMS_HRLVLCC_GRAMD1_S",
                "CLMS_HRLVLCC_GRAMD2_S",
                "CLMS_HRLVLCC_GRAMD3_S",
                "CLMS_HRLVLCC_GRAMD4_S",
            ],
        },
    }
)


def create_hda_client(hda_configuration_folder=None, retry_max=6, sleep_max=8):
    """
    Create a WEkEO HDA API Client for accessing the Copernicus High-Resolution Layers (HRL) data.

    Creates a configuration file (.hdarc) containing user credentials (username and password)
    in the user's home directory if it does not already exist.

    Parameters:
        hda_configuration_folder (str or Path): Path to the folder where the .hdarc file should be created.
            (default is None, if None the user's home directory will be used).
        retry_max (int): Maximum number of retry attempts for the client creation (default is 6).
        sleep_max (int): Maximum sleep time in seconds between retry attempts for the client creation (default is 8).

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

    hda_client = hda.Client(retry_max=retry_max, sleep_max=sleep_max)
    logger.info("HDA Client created successfully.")

    return hda_client


def request_hda_grassland_data(
    map_key,
    year,
    coordinates_list,
    *,
    dataset_id="EO:EEA:DAT:HRL:GRA",
    resolution="10m",
    opendap_folder="landCoverMaps/EUR_hda_grassland/",
    target_folder=None,
    max_files=100,
    upload_opendap=True,
    retry_attempts=6,
    retry_delay=8,
    force_download=False,
):
    """
    Request and download High Resolution Layer (HRL) grassland data from WEkEO HDA API.

    Parameters:
        map_key (str): Key to identify the type of HDA data to request.
        year (int): Year for which the HDA data is requested.
        coordinates_list (list): List of dictionaries containing latitude and longitude coordinates.
        dataset_id (str): Dataset ID for the HDA data (default is "EO:EEA:DAT:HRL:GRA").
        resolution (str): Resolution of the data to be requested (default is "10m").
        years_available (list): List of years for which data is available (default includes 2015, 2017-2021).
        opendap_folder (str): Folder on the opendap server where the data is stored
            (default is "landCoverMaps/EUR_hda_grassland/").
        target_folder (str or Path): Folder where the downloaded data will be stored
            (default is None, which uses the opendap folder in the current working directory).
        max_files (int): Maximum number of files to download (default is 100).
        upload_opendap (bool): Upload the newly requested files to opendap server
            (requires permission, default is True).
        retry_attempts (int): Total number of attempts (default is 6).
        retry_delay (int): Initial delay in seconds for request errors (default is 8, increasing exponentially).
        force_download (bool): Force re-download of files even if they already exist locally or on opendap server (default is False).

    Returns:
        hda_file_stems (list): List of file stems of the downloaded HDA data.
    """
    if target_folder is None:
        target_folder = Path.cwd() / opendap_folder
    elif isinstance(target_folder, str):
        target_folder = Path.cwd() / target_folder

    if map_key == "EUR_hda_grassland":
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

        if map_key in HDA_SPECS.keys():
            # Create target folder if it does not exist
            if not target_folder.is_dir():
                logger.info(f"Creating target folder: {target_folder} ...")
                target_folder.mkdir(parents=True, exist_ok=True)

            # Get area (bounding box) of all coordinates
            area_coordinates = get_area_coordinates(coordinates_list)
            logger.info(
                f"Looking for HDA data for map_key '{map_key}', year '{year}', "
                f"latitude {area_coordinates['lat_start']}-{area_coordinates['lat_end']}, "
                f"longitude {area_coordinates['lon_start']}-{area_coordinates['lon_end']} "
                "from 'HRL Grasslands' dataset ..."
            )

            # Check if all files are already available
            if not force_download:
                hda_file_stems = []
                files_missing = False

                for coordinates in coordinates_list:
                    (easting, northing) = reproject_coordinates(
                        coordinates["lat"], coordinates["lon"], "EPSG:3035"
                    )
                    east_index = int(easting // 100000)
                    north_index = int(northing // 100000)

                    for layer, file_start in enumerate(
                        HDA_SPECS[map_key]["file_starts"]
                    ):
                        hda_file_start = f"{file_start}{year}_R{resolution}_E{east_index}N{north_index}_03035"
                        hda_files_found = list(
                            target_folder.glob(f"{hda_file_start}*.tif")
                        )

                        # try to find the file on opendap if not found locally
                        if len(hda_files_found) == 0:
                            for version in ["V01", "V02"]:
                                hda_file_tif = Path(
                                    target_folder
                                    / f"{hda_file_start}_{version}_R00.tif"
                                )
                                download_file_opendap(
                                    hda_file_tif.name,
                                    opendap_folder,
                                    hda_file_tif.parent,
                                    warn_not_found=False,
                                )

                                # stop searching if file is found
                                if hda_file_tif.is_file():
                                    hda_files_found.append(hda_file_tif)
                                    break

                        if len(hda_files_found) == 1:
                            hda_file_stems.append(hda_files_found[0].stem)
                        elif len(hda_files_found) > 1:
                            logger.warning(
                                f"Multiple HDA files found for map_key '{map_key}', year '{year}', layer '{layer + 1}', "
                                f"{coordinates}: {hda_files_found}. Using first file."
                            )
                            hda_file_stems.append(hda_files_found[0].stem)
                        else:
                            files_missing = True
                            break

            if force_download or files_missing:
                # Request HDA data
                request = {
                    "dataset_id": dataset_id,
                    "bbox": [
                        area_coordinates["lon_start"],
                        area_coordinates["lat_end"],
                        area_coordinates["lon_end"],
                        area_coordinates["lat_start"],
                    ],
                    "productType": HDA_SPECS[map_key]["product_type"],
                    "resolution": resolution,
                    "year": str(year),
                    "itemsPerPage": 100,
                    "startIndex": 0,
                }

                # Get request results and download if needed including retry loop
                while retry_attempts > 0:
                    retry_attempts -= 1
                    try:
                        hda_client = create_hda_client()
                        matches = hda_client.search(request)
                        hda_file_stems = []
                        file_count = min(len(matches), max_files)

                        for match in matches[:file_count]:
                            hda_file_stem = match.results[0]["id"]
                            hda_file_stems.append(hda_file_stem)
                            hda_file_tif = Path(target_folder / f"{hda_file_stem}.tif")

                            # If file not locally available, try download from opendap server
                            if not hda_file_tif.is_file() and not force_download:
                                download_file_opendap(
                                    hda_file_tif.name,
                                    opendap_folder,
                                    hda_file_tif.parent,
                                    warn_not_found=False,
                                )

                            # If file still not available, download from HDA API
                            if not hda_file_tif.is_file() or force_download:
                                logger.info(
                                    f"Downloading '{hda_file_stem + '.zip'}' from WEkEO HDA API Client to '{target_folder}' ..."
                                )
                                match.download(download_dir=target_folder)
                                hda_file_zip = Path(
                                    target_folder / f"{hda_file_stem}.zip"
                                )

                                if hda_file_zip.is_file():
                                    logger.info(
                                        f"Extracting files from '{hda_file_zip}' ..."
                                    )

                                    with zipfile.ZipFile(hda_file_zip, "r") as zip_ref:
                                        file_type = ".tif"
                                        files_found = [
                                            name
                                            for name in zip_ref.namelist()
                                            if name.endswith(file_type)
                                        ]

                                        if len(files_found) == 1:
                                            extracted_path = zip_ref.extract(
                                                files_found[0], target_folder
                                            )
                                            logger.info(
                                                f"Extracted '{extracted_path}'."
                                            )
                                            set_no_data_value(
                                                extracted_path,
                                                HDA_SPECS[map_key]["no_data_value"],
                                            )

                                            if upload_opendap:
                                                # Try upload new file to opendap server (requires permission)
                                                upload_file_opendap(
                                                    Path(extracted_path), opendap_folder
                                                )
                                        elif len(files_found) == 0:
                                            logger.warning(
                                                f"No {file_type} file found in the zip file '{hda_file_zip.name}'. Skipping extraction."
                                            )
                                        else:
                                            logger.warning(
                                                f"Multiple {file_type} files found in the zip file '{hda_file_zip.name}'. Skipping extraction."
                                            )

                                    # Remove zip file after extraction
                                    hda_file_zip.unlink(missing_ok=True)
                                    logger.info(f"Removed zip file '{hda_file_zip}'.")
                                else:
                                    # Error if the zip file is not found
                                    raise FileNotFoundError(
                                        f"Zip file '{hda_file_zip}' not found after download."
                                    )
                        break
                    except Exception as e:
                        logger.error(
                            f"Error while requesting/downloading HDA data: {e}"
                        )

                        if retry_attempts > 0:
                            logger.info(
                                f"Recreating HDA client and retrying in {retry_delay} seconds ..."
                            )
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            logger.error(
                                "Maximum number of attempts reached. Exiting without downloading data."
                            )
                            matches = []

                if file_count == 0:
                    logger.warning(
                        f"No data found for map_key '{map_key}' and year '{year}' in the specified area."
                    )
                elif file_count < len(matches):
                    logger.warning(
                        f"More than {max_files} files found ({len(matches)} files) for map_key '{map_key}' and year '{year}' in the specified area. "
                        f"Using only the first {max_files} files."
                    )
        else:
            try:
                raise ValueError(
                    f"Invalid map_key '{map_key}'. Valid keys are: {list(HDA_SPECS.keys())}"
                )
            except ValueError as e:
                logger.error(e)
                return []
    else:
        logger.warning(
            f"'{map_key}' map not available for {year}. Valid years are: {', '.join(str(y) for y in years_available)}."
        )
        return []

    return hda_file_stems


def main():
    # Example usage
    map_key = "EUR_hda_grassland"
    year = 2020
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

    hda_file_stems = request_hda_grassland_data(map_key, year, coordinates_list)
    print(f"HDA File Stems: {hda_file_stems}")


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
