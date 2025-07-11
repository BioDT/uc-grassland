"""
Module Name: prep_management_data.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: April, 2024
Description: Download management data and prepare as needed for grassland model input.

Developed in the BioDT project by Thomas Banitz (UFZ) with contributions by Franziska Taubert (UFZ),
Tuomas Rossi (CSC) and Taimur Haider Khan (UFZ).

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

Data sources:
    "GER_Lange" map:
    - Lange, M., Feilhauer, H., Kühn, I., Doktor, D. (2022).
      Mapping land-use intensity of grasslands in Germany with machine learning and Sentinel-2 time series,
      Remote Sensing of Environment, https://doi.org/10.1016/j.rse.2022.112888
    - Based on grassland classification according to: German ATKIS digital landscape model 2015.

    "GER_Schwieder" map:
    - Schwieder, M., Wesemeyer, M., Frantz, D., Pfoch, K., Erasmi, S., Pickert, J., Nendel, C., Hostert, P. (2022).
      Mapping grassland mowing events across Germany based on combined Sentinel-2 and Landsat 8 time series,
      Remote Sensing of Environment, https://doi.org/10.1016/j.rse.2021.112795
    - Based on grassland classification according to:
      Blickensdörfer, L., Schwieder, M., Pflugmacher, D., Nendel, C., Erasmi, S., Hostert, P. (2021).
      National-scale crop type maps for Germany from combined time series of Sentinel-1, Sentinel-2 and
      Landsat 8 data (2017, 2018 and 2019), https://zenodo.org/records/5153047.

    Mowing default dates:
    - Filipiak, M., Gabriel, D., Kuka, K. (2022).
      Simulation-based assessment of the soil organic carbon sequestration in grasslands in relation to
      management and climate change scenarios, https://doi.org/10.1016/j.heliyon.2023.e17287
    - See also:
      Schmid, J. (2022).
      Modeling species-rich ecosystems to understand community dynamics and structures emerging from
      individual plant interactions, PhD thesis, Chapter 4, Table C.7, https://doi.org/10.48693/160
"""

import argparse
import calendar
from pathlib import Path

import numpy as np

from ucgrassland import utils as ut
from ucgrassland.logger_config import logger


def construct_management_data_file_name(
    coordinates,
    years,
    map_key,
    *,
    folder="managementDataFolder",
    data_specifier="noInfo",
    file_suffix=".txt",
):
    """
    Construct management data file name and create folder if missing.

    Parameters:
        coordinates (dict): Dictionary with 'lat' and 'lon' keys ({'lat': float, 'lon': float}).
        years (list): List of years covered by management data.
        map_key (str): Key to identify land use map ('GER_Lange' or 'GER_Schwieder').
        folder (str or Path): Folder where data file will be stored (default is 'managementDataFolder').
        data_specifier (str): Data specifier (e.g. 'raw', 'fill_mean', default is 'noInfo').
        file_suffix (str): File suffix (default is '.txt').

    Returns:
        Path: Constructed data file name as a Path object.
    """
    # Get folder with path appropriate for different operating systems, create folder if missing
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    if "lat" in coordinates and "lon" in coordinates:
        formatted_lat = f"lat{coordinates['lat']:.6f}"
        formatted_lon = f"lon{coordinates['lon']:.6f}"
        formatted_years = f"{years[0]}-01-01_{years[-1]}-12-31"
        file_name = (
            folder
            / f"{formatted_lat}_{formatted_lon}__{formatted_years}__management__{map_key}__{data_specifier}{file_suffix}"
        )
    else:
        try:
            raise ValueError(
                "Coordinates not correctly defined. Please provide as dictionary ({'lat': float, 'lon': float})!"
            )
        except ValueError as e:
            logger.error(e)
            raise

    return file_name


def management_data_to_txt_file(
    location,
    years,
    map_key,
    management_data,
    data_query_protocol,
    *,
    is_raw_data=False,
    map_properties=[],
    fill_mode="mean",
    file_name=None,
):
    """
    Write management data to a text file.

    Parameters:
        location (str or dict): Location information ('DEIMS.iD' or {'lat': float, 'lon': float}).
        years (list): List of years covered by management data.
        map_key (str): Key to identify land use map ('GER_Lange' or 'GER_Schwieder').
        management_data (numpy.ndarray): Management data.
        data_query_protocol (list): List of sources and time_stamps from retrieving management data.
        is_raw_data (bool): Whether data are raw (default is False).
        map_properties (list): List of map properties (default is [], for 'is_raw_data' only).
        fill_mode (str): Method for completing missing data (default is 'mean', for Not 'is_raw_data' only).
        file_name (str or Path): File name to save management data (default is None, default file name used if not provided).

    Returns:
        None
    """
    # Create data file name and header line
    if is_raw_data:
        if not file_name:
            file_name = construct_management_data_file_name(
                location,
                years,
                map_key,
                folder="managementDataRaw",
                data_specifier="raw",
            )

        # Header line, capitalize only the first letter of each string
        management_columns = [s.capitalize() for s in ["Year"] + map_properties]
        management_fmt = "%.0f" + "\t%.4f" * len(map_properties)  # no digits for year
        log_message = (
            f"Raw management data from '{map_key}' map written to file '{file_name}'."
        )
    else:
        if not file_name:
            file_name = construct_management_data_file_name(
                location,
                years,
                map_key,
                folder="managementDataPrepared",
                data_specifier=f"fill_{fill_mode}",
            )

        management_columns = [
            "Date",
            "MowHeight[m]",
            "Fertilizer[gm-2]",
            "Irrigation[mm]",
            "Seeds_PFT1",
            "Seeds_PFT2",
            "Seeds_PFT3",
            "Data source",
        ]
        management_fmt = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"
        log_message = f"Processed management data from '{map_key}' map written to file '{file_name}'."

        # Prepare empty management data for writing to file
        if not management_data:
            management_data = np.empty((0, len(management_columns)), dtype=str)

    file_name.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(
        file_name,
        management_data,
        delimiter="\t",
        fmt=management_fmt,
        header="\t".join(management_columns),
        comments="",
    )
    logger.info(log_message)

    if data_query_protocol:
        file_name = ut.add_string_to_file_name(file_name, "__data_query_protocol")
        ut.list_to_file(
            data_query_protocol, file_name, column_names=["data_source", "time_stamp"]
        )


def get_management_map_file(
    map_key, year, *, property="mowing", applicability=False, cache=None
):
    """
    Generate file path or URL for a management map based on provided map key, property name and year.

    Parameters:
        map_key (str): Key to identify land use map ('GER_Lange' or 'GER_Schwieder').
        year (str): Year.
        property (str): Management property (default is 'mowing').
        applicability (bool): Get area-of-applicability-map (default is False).
        cache (Path): Path for local management map directory (optional).

    Returns:
        str or pathlib.Path: URL or local path to the land use map file, or None if not found.
    """
    if map_key == "GER_Lange":
        if cache is not None:
            # Look for local map file
            file_name = (
                f"S2_Germany_{year}_AOA_{property}.tif"
                if applicability
                else f"S2_Germany_{year}_{property}.tif"
            )
            map_file = Path(cache) / file_name

            if map_file.is_file():
                return map_file
            else:
                logger.error(
                    f"Local file '{map_file}' not found. Trying to access via URL ..."
                )

        # Nested dictionary for file names
        file_names = {
            2017: {
                True: {
                    "mowing": "98d7c7ab-0a8f-4c2f-a78f-6c1739ee9354",
                    "fertilisation": "7a4b70a9-95b3-4a06-ae8b-082184144494",
                    "grazing": "e83a9d4a-ea55-44dd-b3fb-2ee7cb046e92",
                    "LUI": "4e7ab052-bd47-4ccf-9560-57ceb080945a",
                },
                False: {
                    "mowing": "14a1d2b6-11c8-4e31-ac19-45a7b805428d",
                    "fertilisation": "deaca5bf-8999-4ccf-beac-ab47210051f6",
                    "grazing": "611798da-e43d-4de6-9ff5-d5fb562fbf46",
                    "LUI": "54995bd6-2811-4198-ba55-675386510260",
                },
            },
            2018: {
                True: {
                    "mowing": "d871429a-b2a6-4592-b3e5-4650462a9ac3",
                    "fertilisation": "3b24279c-e9ab-468d-86b8-fe1fadc121bf",
                    "grazing": "69701524-ed47-4e4b-9ef2-e355f5103d76",
                    "LUI": "0efe31de-1275-4cab-b470-af1ce9f28363",
                },
                False: {
                    "mowing": "0eb6a466-417b-4b30-b5f8-070c3f2c99c3",
                    "fertilisation": "aa81ef4f-4ed4-489a-9d52-04d1fd3a357a",
                    "grazing": "2bc29d3f-08d1-4508-a0ca-c83517216f69",
                    "LUI": "28b419a6-c282-42fa-a23a-72676a288171",
                },
            },
        }

        try:
            file_name = file_names[year][applicability][property]
        except KeyError:
            logger.warning(f"'{map_key}' {property} map not available for {year}.")
            return None

        map_file = (
            f"https://data.mendeley.com/public-files/datasets/m9rrv26dvf/files/"
            f"{file_name}/file_downloaded"
        )
    elif map_key == "GER_Schwieder":
        if year in [2017, 2018, 2019, 2020, 2021]:
            file_name = f"GLU_GER_{year}_SUM_DOY_COG.tif"
        else:
            logger.warning(f"'{map_key}' {property} map not available for {year}.")
            return None

        if cache is not None:
            map_file = Path(cache) / file_name

            if map_file.is_file():
                return map_file
            else:
                logger.error(
                    f"Local file '{map_file}' not found. Trying to access via URL ..."
                )

        # Get map file URL
        map_file = f"https://zenodo.org/records/10609590/files/{file_name}"

    # Return map file URL, if found
    if ut.check_url(map_file):
        return map_file
    else:
        logger.error(f"File '{map_file}' not found. Returning None.")
        return None


def get_GER_Lange_data(coordinates, map_properties, years):
    """
    Read management data for given coordinates from 'GER_Lange' map for respective year and return as array.
    Only works for locations classified as grassland according to German ATKIS digital landscape model 2015.

    Properties:
        Mowing: number of moving events.
        Fertilisation: information aggregated into fertilised or not fertilised.
        Grazing: classification bases on grazing intensity (G), given as livestock units (depending on species and
            age) per ha and day (Class 0: G=0, Class 1: 0 < G <= 0.33, Class 2: 0.33 < G <=0.88, Class 3: G > 0.88).
        LUI calculation based on Mowing, Fertilisation and Grazing (cf. Lange et al. 2022).

        Each property's model has a separate area of applicability for each year.

    Parameters:
        coordinates (tuple): Coordinates ('lat', 'lon') to extract management data.
        map_properties (list): List of properties to extract.
        years (list): List of years to process.

    Returns:
        tuple: Property data for given years (2D numpy.ndarray, nan if no grassland or outside area of applicability),
            and list of query sources and time stamps.
    """
    map_key = "GER_Lange"
    logger.info(f"Reading management data from '{map_key}' map ...")
    query_protocol = []

    # Initialize property_data array with nans
    property_data = np.full((len(years), len(map_properties) + 1), np.nan, dtype=float)
    warn_no_grassland = True

    # Extract values from tif maps for each year and each property
    for y_index, year in enumerate(years):
        # Add year to management data
        property_data[y_index, 0] = year

        # Add management properties from tif maps
        for p_index, property in enumerate(map_properties, start=1):
            # Extract property value
            map_file = get_management_map_file(
                map_key, year, property=property, applicability=False
            )

            if map_file:
                logger.info(
                    f"{property[0].upper() + property[1:]} map for {year} found. Using '{map_file}'."
                )

                # Extract and check AOA value
                aoa_file = get_management_map_file(
                    map_key, year, property=property, applicability=True
                )

                if aoa_file:
                    logger.info(
                        f"{property[0].upper() + property[1:]} map AOA for {year} found. Using '{aoa_file}'."
                    )
                    within_aoa, time_stamp = ut.extract_raster_value(
                        aoa_file, coordinates
                    )
                    query_protocol.append([aoa_file, time_stamp])

                    if within_aoa == -1:
                        if warn_no_grassland:
                            logger.warning(
                                f"Location not classified as grassland in '{map_key}' map."
                            )
                            warn_no_grassland = False
                        break

                    property_value, time_stamp = ut.extract_raster_value(
                        map_file, coordinates
                    )
                    query_protocol.append([map_file, time_stamp])

                    if within_aoa:
                        logger.info(
                            f"{year}, {property} : {property_value}. Within area of applicability."
                        )
                        property_data[y_index, p_index] = property_value
                    else:
                        logger.warning(
                            f"{year}, {property} : {property_value}. Not used, outside area of applicability."
                        )

    return property_data, query_protocol


def get_GER_Schwieder_data(coordinates, map_properties, years):
    """
    Read mowing data for given coordinates from 'GER_Schwieder' map for respective year and return as array.
    Only works for locations classified as (permanent) grassland in 2017, 2018 and 2019 according to Blickensdörfer et al. (2021).

    Properties:
        Mowing: number of moving events (max. 6) and their dates (day of year).

    Parameters:
        coordinates (tuple): Coordinates ('lat', 'lon') to extract management data.
        map_properties (list): List of properties to extract.
        years (list): List of years to process.

    Returns:
        tuple: Property data for given years (2D numpy.ndarray, nan if no grassland or no mowing event),
            and list of query sources and time stamps.
    """
    map_key = "GER_Schwieder"
    logger.info(f"Reading management data from '{map_key}' map ...")
    query_protocol = []
    map_bands = len(map_properties)
    property = map_properties[0]

    if property != "mowing":
        try:
            raise ValueError(
                f"First property to read from '{map_key}' map must be 'mowing'."
            )
        except ValueError as e:
            logger.error(e)
            raise

    # Initialize property_data array with nans
    property_data = np.full((len(years), map_bands + 1), np.nan, dtype=object)
    warn_no_grassland = True

    # Extract values from tif maps for each year and each property
    for y_index, year in enumerate(years):
        # Add year to management data
        property_data[y_index, 0] = year
        map_file = get_management_map_file(map_key, year)

        if map_file:
            logger.info(
                f"{property.capitalize()} map for {year} found. Using '{map_file}'."
            )

            # Read mowing events (band 1)
            band_index = 1
            band_value, time_stamp = ut.extract_raster_value(
                map_file, coordinates, band_number=band_index
            )
            query_protocol.append([map_file, time_stamp])

            if band_value == -9999:
                if warn_no_grassland:
                    logger.warning(
                        f"Location not classified as grassland in '{map_key}' map."
                    )
                    warn_no_grassland = False
            else:
                property_data[y_index, band_index] = band_value
                logger.info(f"{year}, {property}: {band_value} event(s).")

                # Add mowing dates if available (bands 2 to end)
                for band_index in range(2, map_bands + 1):
                    band_value, time_stamp = ut.extract_raster_value(
                        map_file, coordinates, band_number=band_index
                    )

                    if band_value != 0:
                        property_data[y_index, band_index] = band_value
                        query_protocol.append([map_file, time_stamp])
                        band_date = ut.day_of_year_to_date(year, int(band_value))
                        logger.info(
                            f"{property.capitalize()} event {band_index - 1}: {band_date.strftime('%Y-%m-%d')}."
                        )

    return property_data, query_protocol


def get_mow_events(
    year, mow_days, data_source, *, mow_height=0.05, leap_year_considered=True
):
    """
    Generate mowing event entries for a given year based on specified days and height.

    Parameters:
        year (int): Year for which to generate mowing events.
        mow_days (list of int): Days of year to schedule mowing.
        data source (str): Datea source for mowing events (e.g. 'date observed', 'event assumed (...)').
        mow_height (float): Height of mowing (in meters, default is 0.05).
        leap_year_considered (bool): Whether leap year was already considered for mow_days (default is True).

    Returns:
        list of list: list of mowing events in grassland model management input data format,
        one row for each mow_day, containing:
            column 0: date string in format YYYY-MM-DD.
            column 1: value of mow_height.
            columns 2 to 6: 'NaN' (for no fertilisation, no irrigation and no seeds at this management event).
            column 7: 'data_source' string to specify data source.
    """
    # Create result array, date and mow height in first rows, NaN for all other management rows
    mow_events = []
    for day_of_year in mow_days:
        mow_date = ut.day_of_year_to_date(year, day_of_year, leap_year_considered)
        row = [
            mow_date.strftime("%Y-%m-%d"),
            mow_height,
            "NaN",
            "NaN",
            "NaN",
            "NaN",
            "NaN",
            data_source,
        ]
        mow_events.append(row)

    return mow_events


def get_mow_schedule(year, mow_count, data_source, mow_height=0.05):
    """
    Generate a schedule of mowing dates based on number of mowings (mow_count) for a given year.

    Parameters:
        year (int): Year for which to generate the schedule.
        mow_count (float): Number of mowing events (expected to be between 1 and 5).
        data source (str): Data source for mowing events (e.g. 'event assumed (...)').
        mow_height (float): Height of mowing (in meters, default is 0.05).

    Returns:
        numpy.ndarray: Array with mowing events in grassland model management input data format,
        mow_count rows, each row containing:
            column 0: date string in format YYYY-MM-DD.
            column 1: value of mow_height.
            columns 2 to 6: value NaN (for no fertilisation, no irrigation and no seeds at this management event).
            column 7: 'data_source' string to specify data source.
    """
    # Check if mow_count is NaN
    if np.isnan(mow_count):
        logger.warning("mow_count is NaN. No schedule will be generated.")

        return np.array([])

    # Check if mow_count is between 1 and 5
    if mow_count < 1:
        mow_count = 1
        logger.warning(
            "'mow_count' is smaller than 1. Value between 1 and 5 expected. Set to 1."
        )
    elif mow_count > 5:
        mow_count = 5
        logger.warning(
            "'mow_count' is greater than 5. Value between 1 and 5 expected. Set to 5."
        )

    # Convert mow_count to int
    mow_count = int(mow_count)

    # Define specific days for each number of mow events (cf. Filipiak et al. 2022, Table S6)
    mow_days = {
        1: [213],  # 08-01
        2: [121, 244],  # 05-01, 09-01
        3: [121, 182, 244],  # 05-01, 07-01, 09-01
        4: [105, 166, 213, 274],  # 04-15, 06-15, 08-01, 10-01
        5: [91, 135, 182, 227, 288],  # 04-01, 05-15, 07-01, 08-15, 10-15
    }

    mow_events = get_mow_events(
        year,
        mow_days[mow_count],
        data_source,
        mow_height=mow_height,
        leap_year_considered=False,
    )

    return mow_events


def get_fert_days(mow_days, year):
    """
    Calculate fertilisation dates based on mowing dates for a given year.
    Using time differences between fertilization and mowing events, respectively,
        according to Filipiak et al. 2022, Table S6.

    Parameters:
        mow_days (list of int): List with day of year for each mowing event.
        year (int): Year for which to calculate the fertlization events.

    Returns:
        list of int: List with day of year for each fertilisation event.
    """
    event_count = len(mow_days)
    days_ahead = {
        0: [],  # allow empty mow day lists
        1: [122],
        2: [30, 78],
        3: [47, 47, 48],
        4: [45, 45, 31, 47],
        5: [31, 30, 30, 31, 44],
    }

    if event_count not in days_ahead:
        try:
            raise ValueError(
                f"No fertilisation day values defined for list of {event_count} mow days."
            )
        except ValueError as e:
            logger.error(e)
            raise

    deltas = days_ahead[event_count]
    fert_days = []

    # Set earliest possible fertilisation date to 03-01
    earliest_fert_day = 61 if calendar.isleap(year) else 60
    earliest_fert_date_str = ut.day_of_year_to_date(year, earliest_fert_day).strftime(
        "%Y-%m-%d"
    )

    # Calculate fertilisation dates using specific days ahead of corresponding mow events
    for index, mow_day in enumerate(mow_days):
        fert_day = mow_day - deltas[index]

        if fert_day < earliest_fert_day:
            logger.warning(
                "Calculated fertilisation date"
                f" {ut.day_of_year_to_date(year, fert_day).strftime('%Y-%m-%d')}"
                f" is before earliest date allowed. Set to {earliest_fert_date_str}."
            )
            fert_day = earliest_fert_day

        fert_days.append(fert_day)

    return fert_days


def fert_days_from_mow_days(mow_days_per_year, years):
    """
    Calculate fertilisation dates based on mowing dates.
    Using time differences between fertilization and mowing events, respectively,
        according to Filipiak et al. 2022, Table S6.

    Parameters:
        mow_days (list of list): List of lists with day of year for each mowing event for each year.
        yeard (list of int): Year for which to calculate the fertlization events.

    Returns:
        list of list: List of lists with day of year for each fertilisation event for each year.
    """
    fert_days_per_year = []

    for index, year in enumerate(years):
        fert_days = get_fert_days(mow_days_per_year[index], year)
        fert_days_per_year.append(fert_days)

    return fert_days_per_year


def get_fert_schedule(year, fert_count, data_source, fert_days=None):
    """
    Generate schedule of fertilisation dates based on number of events for a given year.

    Parameters:
        year (int): Year for which to generate the schedule.
        fert_count (float): Number of fertilisation events (expected to be between 1 and 5).
        data source (str): Data source for mowing events (e.g. 'event assumed (...)').
        fert_days (list of int): List with day of year for each event (default is None).

    Returns:
        numpy.ndarray: Array with fertilisation events in grassland model management input data format,
        fert_count rows, each row containing:
            column 0: date string in format YYYY-MM-DD.
            column 1: value NaN (for no mowing at this management event).
            column 2: value of fert_amount.
            columns 3 to 6: value NaN (for no irrigation and no seeds at this management event).
            column 7: 'data_source' string to specify data source.
    """
    # Check if fert_count is NaN
    if np.isnan(fert_count):
        logger.warning("fert_count is NaN. No schedule will be generated.")

        return np.array([])

    # Check if fert_count is between 1 and 5
    if fert_count < 1:
        fert_count = 1
        logger.warning(
            "'fert_count' is smaller than 1. Value between 1 and 5 expected. Set to 1."
        )
    elif fert_count > 5:
        fert_count = 5
        logger.warning(
            "'fert_count' is greater than 5. Value between 1 and 5 expected. Set to 5."
        )

    # Convert fert_count to int
    fert_count = int(fert_count)

    # Check if specific days for fertilisation events are provided
    if fert_days:
        if len(fert_days) > fert_count:
            logger.warning(
                f"List of fertilisation days for {year} has more entries than 'fert_count'."
                f" Only first {fert_count} days will be used."
            )
        elif len(fert_days) < fert_count:
            logger.warning(
                f"List of fertilisation days for {year} has fewer entries than expected for 'fert_count' = {fert_count}."
                " List not used, replaced by standard schedule."
            )
            fert_days = None

    if not fert_days:
        # Define specific days for each number of fertilisation events (cf. Filipiak et al. 2022, Table S6)
        fert_days_default = {
            1: [91],  # 04-01
            2: [91, 166],  # 04-01, 06-15
            3: [74, 135, 196],  # 03-15, 05-15, 07-15
            4: [60, 121, 182, 227],  # 03-01, 05-01, 07-01, 08-15
            5: [60, 105, 152, 196, 244],  # 03-01, 04-15, 06-01, 07-15, 09-01
        }
        fert_days = fert_days_default[fert_count]

        if calendar.isleap(year):
            fert_days = [day + 1 for day in fert_days]  # Adjust for leap year

    # Define specific amounts for each number of fertilisation events (cf. Filipiak et al. 2022, Table S6)
    fert_amounts = {  # in g/m²
        1: [5.5],
        2: [6.5, 3.5],
        3: [12.5, 3.25, 3.25],
        4: [16.5, 4, 2, 2],
        5: [21, 2.5, 2.5, 2.5, 2.5],
    }

    # Create result array, date in first row, fertilisation amount in third row, NaN for all other management rows
    fert_events = []

    for d_index, day_of_year in enumerate(fert_days):
        fert_date = ut.day_of_year_to_date(year, day_of_year)
        row = [
            fert_date.strftime("%Y-%m-%d"),
            "NaN",
            fert_amounts[fert_count][d_index],
            "NaN",
            "NaN",
            "NaN",
            "NaN",
            data_source,
        ]
        fert_events.append(row)

    return fert_events


def convert_management_data(
    management_data_raw,
    map_key,
    *,
    fill_mode="mean",
    mow_height=0.05,
    mow_count_default=2,
):
    """
    Convert raw management data into structured mowing and fertilisation events.

    Parameters:
        management_data_raw (list of list): Raw management data containing yearly mowing and fertilisation info.
        map_key (str): Key to identify land use map ('GER_Lange' or 'GER_Schwieder').
        fill_mode (str): Method for completing missing data (default is 'mean').
        mow_height (float): Height of mowing (in meters, default is 0.05).
        mow_count_default (int): Number of annual events when using fill_mode 'default' for completing data (default is 2).

    Returns:
        list of list: List of mowing events in grassland model management input data format,
        one row for each management event, containing:
            column 0: date string in format YYYY-MM-DD.
            column 1: value of mowing height (if mowing event, otherwise 'NaN').
            column 2: value of fertilisation amount (if fertilisation event, otherwise 'NaN').
            columns 3 to 6: 'NaN' (for no irrigation and no seeds at this management event).
            column 7: 'data_source' string to specify data source.
    """
    management_events = []
    years = np.array([int(entry[0]) for entry in management_data_raw])
    years_with_mow_data = np.array([])
    mow_days_per_year = [[] for _ in range(len(years))]
    fert_days_per_year = [[] for _ in range(len(years))]
    fert_source_per_year = np.full(years.shape, "", dtype=object)

    # MOWING
    if map_key in ["GER_Lange", "GER_Schwieder"]:
        # Read mowing, same column for "GER_Lange" and "GER_Schwieder"
        mow_count_per_year = np.array([entry[1] for entry in management_data_raw])
        years_with_mow_data = years[~np.isnan(mow_count_per_year)]

        if map_key == "GER_Lange":
            # Add mowing events to management events, using default schedule
            for index in np.where(mow_count_per_year > 0)[0]:
                mow_schedule = get_mow_schedule(
                    years[index],
                    mow_count_per_year[index],
                    "event observed (date: schedule)",
                    mow_height=mow_height,
                )
                management_events.extend(mow_schedule)
        elif map_key == "GER_Schwieder":
            # Get specific mowing dates for each year with mowing, add to management events
            for index in np.where(mow_count_per_year > 0)[0]:
                entry = management_data_raw[index]
                mow_days_per_year[index] = [
                    int(x) for x in entry[2 : int(mow_count_per_year[index]) + 2]
                ]
                mow_events = get_mow_events(
                    years[index],
                    mow_days_per_year[index],
                    "date observed",
                    mow_height=mow_height,
                    leap_year_considered=True,
                )
                management_events.extend(mow_events)

    # Fill mowing for years without data
    fill_mode = fill_mode.lower()
    epsilon = 1e-10
    mow_count_fill = 0
    no_mow_data_for_mean = False

    if fill_mode == "mean":
        # Use means of data retrieved for remaining years as well
        logger.info("Completing management data with means from years with data ...")

        if years_with_mow_data.size > 0:
            mow_count_float = np.nanmean(mow_count_per_year)
            mow_count_fill = round(mow_count_float + epsilon)
            logger.info(
                f"Mean annual mowing events: {mow_count_float:.4f} "
                f"(from {years_with_mow_data.size} years). "
                f"Using {mow_count_fill} events per year."
            )
            data_source_str = f"event assumed (fill mode: {fill_mode}, date: schedule)"
        else:
            # No data for any of the years, use default option instead
            logger.warning(
                "No mowing data for any year to calculate mean and complete other years."
            )
            no_mow_data_for_mean = True

    if fill_mode == "default" or no_mow_data_for_mean:
        # Use default management settings for years without data
        mow_count_fill = mow_count_default
        logger.info(
            "Completing management data with default values ... "
            f"Using {mow_count_fill} events per year."
        )
        data_source_str = "event assumed (fill mode: default, date: schedule)"

    mow_count_per_year[np.isnan(mow_count_per_year)] = mow_count_fill

    # Add all remaining mowing events to schedule
    for index, year in enumerate(years):
        if mow_count_per_year[index] > 0 and year not in years_with_mow_data:
            mow_schedule = get_mow_schedule(
                year,
                mow_count_fill,
                data_source_str,
                mow_height=mow_height,
            )
            management_events.extend(mow_schedule)

    # FERTILISATION
    if map_key == "GER_Lange":
        # Read fertilisation data for "GER_Lange"
        fertilised_per_year = np.array([entry[2] for entry in management_data_raw])
        fert_count_per_year = np.zeros_like(fertilised_per_year)

        # If data say fertilisation, adapt number of events to mowing events (even if mowing==0)!
        for index in np.where(fertilised_per_year == 1)[0]:
            fert_count_per_year[index] = mow_count_per_year[index]
            fert_source_per_year[index] = "event observed (date: schedule)"

        # Fill fertilisation years without data
        index_to_fill = np.where(np.isnan(fertilised_per_year))[0]
        no_fert_data_for_mean = False

        if fill_mode == "mean":
            if np.any(~np.isnan(fertilised_per_year)):
                # Use means of data retrieved for remaining years as well
                fert_count_float = np.mean(
                    fert_count_per_year[~np.isnan(fertilised_per_year)]
                )
                fert_count_fill = round(fert_count_float + epsilon)
                logger.info(
                    f"Mean number of fertilisation events: {fert_count_float:.4f} per year. "
                    f"Using {fert_count_fill} events per year (but never more than mowing events of the same year)."
                )

                # Fill in fertilisation events, but not more than mowing events of the same year
                fert_count_per_year[index_to_fill] = np.minimum(
                    fert_count_fill, mow_count_per_year[index_to_fill]
                )
                fert_source_per_year[index_to_fill] = (
                    f"event assumed (fill mode: {fill_mode}, date: schedule)"
                )
            else:
                # No data for any of the years, use default option instead
                logger.warning(
                    "No fertilisation data for any year to calculate mean and complete other years."
                )
                no_fert_data_for_mean = True

        if fill_mode == "default" or no_fert_data_for_mean:
            # Use number of mowing events as default for years without fertilisation data
            logger.info(
                "Using the same number of fertilisation events as mowing events for each year."
            )
            fert_count_per_year[index_to_fill] = mow_count_per_year[index_to_fill]
            fert_source_per_year[index_to_fill] = (
                "event assumed (fill mode: like mowing, date: schedule)"
            )
    elif map_key == "GER_Schwieder":
        fert_count_per_year = np.zeros_like(mow_count_per_year)

        if fill_mode in ["mean", "default"]:
            # No fertilisation data, use number of mowing events as default
            logger.warning(
                f"'{map_key}' map has no fertilisation data. "
                "Using the same number of fertilisation events as mowing events for each year."
            )
            fert_count_per_year = mow_count_per_year
            fert_days_per_year = fert_days_from_mow_days(mow_days_per_year, years)
            fert_source_per_year[:] = (
                "event assumed (fill mode: like mowing, date: based on mowing)"
            )

    # Add all fertilisation events to schedule
    for index, year in enumerate(years):
        if fert_count_per_year[index] > 0:
            fert_schedule = get_fert_schedule(
                year,
                fert_count_per_year[index],
                fert_source_per_year[index],
                fert_days=fert_days_per_year[index],
            )
            management_events.extend(fert_schedule)

    try:
        management_events.sort(key=lambda x: x[0])
    except TypeError as e:
        logger.error(f"Sorting failed due to incompatible data types ({e}).")
    return management_events


def get_management_data(
    coordinates,
    years,
    map_key,
    *,
    fill_mode="mean",
    mow_height="0.05",
    file_name=None,
):
    """
    Read management data from land use map. Write to .txt files.

    Parameters:
        coordinates (dict): Dictionary with 'lat' and 'lon' keys ({'lat': float, 'lon': float}).
        years (list of int): List of years.
        map_key (str): Key to identify land use map ('GER_Lange' or 'GER_Schwieder').
        fill_mode (str): String to identify method for filling missing data ('mean', 'default', 'none', default is 'mean').
        mow_height (float): Height of mowing (in meters, default is 0.05).on.
        file_name (str or Path): File name to save final management data (default is None, default file name used if not provided).
    """
    if "lat" in coordinates and "lon" in coordinates:
        logger.info(
            f"Preparing management data for latitude: {coordinates['lat']}, longitude: {coordinates['lon']} ..."
        )
    else:
        try:
            raise ValueError(
                "Coordinates not correctly defined. Please provide as dictionary ({'lat': float, 'lon': float})!"
            )
        except ValueError as e:
            logger.error(e)
            raise

    if map_key == "GER_Lange":
        map_properties = ["mowing", "fertilisation", "grazing", "LUI"]
        management_data_raw, data_query_protocol = get_GER_Lange_data(
            coordinates, map_properties, years
        )
    elif map_key == "GER_Schwieder":
        map_properties = [
            "mowing",
            "date_1",
            "date_2",
            "date_3",
            "date_4",
            "date_5",
            "date_6",
        ]
        management_data_raw, data_query_protocol = get_GER_Schwieder_data(
            coordinates, map_properties, years
        )
    else:
        try:
            raise ValueError(
                f"Map key '{map_key}' not found. Please provide valid map key!"
            )
        except ValueError as e:
            logger.error(e)
            raise

    management_data_to_txt_file(
        coordinates,
        years,
        map_key,
        management_data_raw,
        data_query_protocol,
        is_raw_data=True,
        map_properties=map_properties,
    )

    management_data_prepared = convert_management_data(
        management_data_raw,
        map_key,
        fill_mode=fill_mode,
        mow_height=mow_height,
    )

    management_data_to_txt_file(
        coordinates,
        years,
        map_key,
        management_data_prepared,
        data_query_protocol,
        is_raw_data=False,
        fill_mode=fill_mode,
        file_name=file_name,
    )


def prep_management_data(
    coordinates,
    years,
    map_key,
    *,
    fill_mode="mean",
    mow_height=0.05,
    deims_id=None,
    file_name=None,
):
    """
    Prepare management data to be used as grassland model input.

    Parameters:
        coordinates (dict): Coordinates dictionary with 'lat' and 'lon', or 'None' using DEIMS.iD.
        years (list or None): List of years to process, or 'None' for default value.
        map_key (str): Key to identify land use map ('GER_Lange' or 'GER_Schwieder').
        fill_mode (str): String to identify the method for filling missing data ('mean', 'default', 'none', default is 'mean').
        mow_height (float): Height of mowing (in meters, default is 0.05).
        deims_id (str): DEIMS.iD (default is None).
        file_name (str or Path): File name to save management data (default is None, default file name used if not provided).
    """
    if years is None:
        years = list(range(2013, 2024))  # list(range(2017, 2019))

    if coordinates:
        get_management_data(
            coordinates,
            years,
            map_key,
            fill_mode=fill_mode,
            mow_height=mow_height,
            file_name=file_name,
        )
    elif deims_id:
        location = ut.get_deims_coordinates(deims_id)

        if location["found"]:
            get_management_data(
                location,
                years,
                map_key,
                fill_mode=fill_mode,
                mow_height=mow_height,
                file_name=file_name,
            )
        else:
            try:
                raise ValueError(f"Coordinates for DEIMS.id '{deims_id}' not found.")
            except ValueError as e:
                logger.error(e)
                raise
    else:
        # Example to get multiple coordinates from DEIMS.iDs from XLS file, filter only Germany
        sites_file_name = Path.cwd() / "grasslandSites" / "_elter_call_sites.xlsx"
        sites_ids = ut.get_deims_ids_from_xls(
            sites_file_name, header_row=1, country="DE"
        )
        sites_ids = ["fd8b85c0-93ef-4a41-8706-3c4be9dec8e5"]

        for deims_id in sites_ids:
            location = ut.get_deims_coordinates(deims_id)

            if location["found"]:
                get_management_data(
                    location,
                    years,
                    map_key,
                    fill_mode=fill_mode,
                    mow_height=mow_height,
                    file_name=file_name,
                )

        # Example coordinates for checking without DEIMS.iDs
        locations = [
            {"lat": 51.390427, "lon": 11.876855},  # GER, GCEF grassland site
            {
                "lat": 51.3919,
                "lon": 11.8787,
            },  # GER, GCEF grassland site, centroid, non-grassland in HRL!
            {"lat": 51.3521825, "lon": 12.4289394},  # GER, UFZ Leipzig
            {"lat": 51.4429008, "lon": 12.3409231},  # GER, Schladitzer See, lake
            {"lat": 51.3130786, "lon": 12.3551142},  # GER, Auwald, forest within city
            {"lat": 51.7123725, "lon": 12.5833917},  # GER, forest outside of city
            {"lat": 46.8710811, "lon": 11.0244728},  # AT, should be grassland
            {"lat": 64.2304403, "lon": 27.6856269},  # FIN, near LUMI site
            {"lat": 64.2318989, "lon": 27.6952722},  # FIN, LUMI site
            {"lat": 49.8366436, "lon": 18.1540575},  # CZ, near IT4I Ostrava
            {"lat": 43.173, "lon": 8.467},  # Mediterranean Sea
            {"lat": 30, "lon": 1},  # out of Europe
        ]

        for location in locations:
            get_management_data(
                location,
                years,
                map_key,
                fill_mode=fill_mode,
                mow_height=mow_height,
                file_name=file_name,
            )


def main():
    """
    Run script with default arguments for calling the script.
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
    parser.add_argument("--years", nargs="*", type=int, help="List of years")
    parser.add_argument(
        "--map_key",
        type=str,
        default="GER_Lange",
        choices=["GER_Lange", "GER_Schwieder"],
        help="Options: 'GER_Lange', 'GER_Schwieder'. (Can be extended.)",
    )
    parser.add_argument(
        "--fill_mode",
        type=str,
        default="mean",
        choices=["mean", "default", "none"],
        help="Options: 'mean', 'default', 'none'.",
    )
    parser.add_argument(
        "--mow_height",
        type=float,
        default=0.05,
        help="Height of mowing (in meters).",
    )
    parser.add_argument("--deims_id", type=int, help="DEIMS.iD")
    parser.add_argument("--file_name", help="File name to save final management data")
    args = parser.parse_args()
    prep_management_data(
        coordinates=args.coordinates,
        years=args.years,
        map_key=args.map_key,
        fill_mode=args.fill_mode,
        mow_height=args.mow_height,
        deims_id=args.deims_id,
        file_name=args.file_name,
    )


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
