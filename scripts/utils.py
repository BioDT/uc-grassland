"""
Module Name: utils.py
Description: Utility functions for uc-grassland building block.

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
import csv
import time
import warnings
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import deims
import pandas as pd
import pyproj
import rasterio
import requests


def add_string_to_file_name(file_name, string_to_add, *, new_suffix=None):
    """
    Add a string before the suffix of a file name.

    Parameters:
        file_name (Path): Path of the file.
        string_to_add (str): String to add before suffix.
        new_suffix (str): New file suffix (e.g. '.xls', default is None to keep old suffix).

    Returns:
        new_file_name (Path): New file path with added string.
    """
    if file_name:
        file_name = Path(file_name)

        if new_suffix is None:
            new_suffix = file_name.suffix

        return file_name.with_name(file_name.stem + string_to_add + new_suffix)

    return ""


def replace_substrings(
    input_data,
    substrings_to_replace,
    replacement_string,
    *,
    at_end=False,
    warning_no_string=False,
):
    """
    Replace specified substrings with another string in a single string or a list of strings.

    Parameters:
        input_data (str or list): String or list of strings.
        substrings_to_replace (str or list): Substring or list of substrings to be replaced.
        replacement_string (str): New string to replace the specified substring(s).
        at_end (bool): Replace substring(s) only if appearing at the end of each string (default is False).
        warning_no_string (bool): Throw warning for input data list elements that are no string (default is False).

    Returns:
        str or list: If input_data is a string, the modified string; if input_data is a list, a new list with specified substrings replaced in each element.
    """

    # Nested functions for either replacing substring at end or everywhere
    def replace_substring_at_end(original_string, substring_to_replace):
        return (
            original_string[: -len(substring_to_replace)] + replacement_string
            if original_string.endswith(substring_to_replace)
            else original_string
        )

    def replace_substring(original_string, substring_to_replace):
        return original_string.replace(substring_to_replace, replacement_string)

    # Convert single strings to lists for unified handling
    if isinstance(substrings_to_replace, str):
        substrings_to_replace = [substrings_to_replace]

    # Recursive function to handle strings and nested lists
    def process_item(item):
        if isinstance(item, str):
            modified_string = item
            for substring in substrings_to_replace:
                modified_string = (
                    replace_substring_at_end(modified_string, substring)
                    if at_end
                    else replace_substring(modified_string, substring)
                )
            return modified_string
        elif isinstance(item, list):
            return [process_item(sub_item) for sub_item in item]
        elif warning_no_string:
            warnings.warn(f"{item} is not a string. No replacements performed.")
        return item  # If it's not a string or list, return as is

    # Process input_data, which can be a string, list, or list of lists
    if isinstance(input_data, (str, list)):
        return process_item(
            input_data
        )  # Process both string and list of strings or list of lists
    else:
        raise ValueError(
            "Input data must be a string, a list of strings, or a list of lists."
        )

    # if isinstance(input_data, str):
    #     input_data = [input_data]

    # # For list of input strings, replace list of substrings with replacement string
    # if isinstance(input_data, list):
    #     modified_list = []

    #     for original_string in input_data:
    #         modified_string = original_string

    #         if isinstance(modified_string, str):
    #             for substring in substrings_to_replace:
    #                 modified_string = (
    #                     replace_substring_at_end(modified_string, substring)
    #                     if at_end
    #                     else replace_substring(modified_string, substring)
    #                 )
    #         elif warning_no_string:
    #             warnings.warn(
    #                 f"{modified_string} is not a string. No replacements performed.",
    #
    #             )

    #         modified_list.append(modified_string)
    # else:
    #     raise ValueError("Input data must be a string or a list of strings.")

    # # Return only string if input data was just a string, list of strings otherwise
    # return modified_list[0] if len(modified_list) == 1 else modified_list


def count_duplicates(lst):
    """
    Count occurrences of duplicate items in a list.

    Parameters:
        lst (list): List to analyze.

    Returns:
        dict: Dictionary where (sorted) keys are duplicate items and values are their counts.
    """
    counter = Counter(lst)
    duplicates = {item: count for item, count in sorted(counter.items()) if count > 1}
    return duplicates


def get_row_values(key, values):
    """
    Get row values based on type of values.

    Parameters:
        key (str): Key from the dictionary.
        values (str or dict): Values associated with the key.

    Returns:
        list: Row values.
    """
    if isinstance(values, dict):
        row_values = [key] + list(values.values())
    else:
        row_values = [key, values]

    return row_values


def dict_to_file(dict_to_write, column_names, file_name):
    """
    Write a dictionary to a text file (tab-separated) or csv file (;-separated) or an Excel file.

    Parameters:
        dict_to_write (dict): Dictionary to be written to file.
        column_names (list): List of all column names (strings, includes first column for dict_to_write keys).
        file_name (str or Path): Path of output file (suffix determines file type).
    """
    if file_name:
        file_path = Path(file_name)
        file_suffix = file_path.suffix.lower()

        # Create data directory if missing
        Path(file_name).parent.mkdir(parents=True, exist_ok=True)

        if file_suffix in [".txt", ".csv"]:
            with open(file_path, "w", newline="", encoding="utf-8") as file:
                writer = (
                    csv.writer(file, delimiter="\t")
                    if file_suffix == ".txt"
                    else csv.writer(file, delimiter=";")
                )
                header = column_names
                writer.writerow(header)  # Header row

                for key, values in dict_to_write.items():
                    writer.writerow(get_row_values(key, values))
        elif file_suffix == ".xlsx":
            df = pd.DataFrame(columns=column_names)

            for key, values in dict_to_write.items():
                df = pd.concat(
                    [
                        df,
                        pd.DataFrame(
                            [get_row_values(key, values)], columns=column_names
                        ),
                    ],
                    ignore_index=True,
                )

            df.to_excel(file_path, index=False)
        else:
            print(
                "Error: Unsupported file format. Supported formats are '.txt', '.csv' and '.xlsx'."
            )

        print(f"Dictionary written to file '{file_name}'.")


def find_column_index(raw_data, column_id, *, header_lines=1):
    """
    Find index of specified column in data frame or list of lists.

    Parameters:
        raw_data (pd.DataFrame or list): Data frame or list of lists to find column.
        column_id (str or int): Column identifier (name as string or index).
        header_lines (int): Number of header lines in list of lists (default is 1).

    Returns:
        int: Index of specified column, if found.

    Raises:
        KeyError: If column name is not found in the data frame or list of lists.
        ValueError: If column identifier is not a string or integer.
        TypeError: If raw_data is not a pandas DataFrame or a list of lists.
    """
    if isinstance(raw_data, pd.DataFrame):
        if isinstance(column_id, str):
            try:
                return raw_data.columns.get_loc(column_id)
            except KeyError:
                raise KeyError(f"Column '{column_id}' not found in the data frame.")
        elif isinstance(column_id, int):
            return column_id
        else:
            raise ValueError(
                "Invalid column identifier. Please provide a column name (str) or column number (int).",
            )
    elif isinstance(raw_data, list):
        if isinstance(column_id, str):
            if column_id in raw_data[header_lines - 1]:
                return raw_data[header_lines - 1].index(column_id)
            else:
                raise ValueError(
                    f"Column '{column_id}' not found in header line of .txt file."
                )
        elif isinstance(column_id, int):
            return column_id
        else:
            raise ValueError(
                "Invalid column identifier. Please provide a column name (str) or column number (int)."
            )
    else:
        raise TypeError("Input data must be a pandas DataFrame or a list of lists.")


def list_to_file(list_to_write, column_names, file_name):
    """
    Write a list of tuples to a text file (tab-separated) or csv file (;-separated) or an Excel file.

    Parameters:
        list_to_write (list): List of strings or tuples or dictionaries to be written to the file.
        column_names (list): List of column names (strings).
        file_name (str or Path): Path of output file (suffix determines file type).
    """
    # Convert string entries to single item tuples
    list_to_write = [
        (entry,) if isinstance(entry, str) else entry for entry in list_to_write
    ]

    # Check if list_to_write contains dictionaries
    if isinstance(list_to_write[0], dict):
        # Convert dictionaries to lists of values based on column_names
        list_to_write = [
            [entry.get(col, "") for col in column_names] for entry in list_to_write
        ]
    # Check if all tuples in list have the same length as the column_names list
    elif not all(len(entry) == len(column_names) for entry in list_to_write):
        print(
            f"Error: All tuples in the list must have {len(column_names)} entries (same as column_names)."
        )
        return

    file_path = Path(file_name)
    file_suffix = file_path.suffix.lower()

    # Create data directory if missing
    Path(file_name).parent.mkdir(parents=True, exist_ok=True)

    if file_suffix in [".txt", ".csv"]:
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = (
                csv.writer(file, delimiter="\t")
                if file_suffix == ".txt"
                else csv.writer(file, delimiter=";")
            )
            header = column_names
            writer.writerow(header)  # Header row

            for entry in list_to_write:
                writer.writerow(entry)
    elif file_suffix == ".xlsx":
        df = pd.DataFrame(list_to_write, columns=column_names)
        df.to_excel(file_path, index=False)
    else:
        raise ValueError(
            "Unsupported file format. Supported formats are '.txt', '.csv' and '.xlsx'."
        )

    print(f"List written to file '{file_name}'.")


def add_to_dict(
    dict_prev, dict_to_add, value_name_prev="info1", value_name_add="info2"
):
    """
    Add values from a dictionary to an existing dictionary under a specified key.

    Parameters:
        dict_prev (dict): Existing dictionary.
        dict_to_add (dict): Dictionary of new values to add.
        value_name_prev (str): Name for existing values in the updated dictionary (default is 'info1').
        value_name_add (str): Name for new values in the updated dictionary (default is 'info2').

    Returns:
        dict: Updated dictionary with combined old and new values.

    Raises:
        ValueError: If keys in dict_prev and dict_to_add are not the same.
    """
    # Check if keys are the same
    if set(dict_prev.keys()) != set(dict_to_add.keys()):
        raise ValueError(
            "Keys in previous dictionary and added dictionary must be the same."
        )

    # Convert dict_prev to a dictionary of dictionaries if not already
    if all(isinstance(value, dict) for value in dict_prev.values()):
        dict_added = dict_prev
    else:
        dict_added = {key: {value_name_prev: value} for key, value in dict_prev.items()}

    # Add new values to each key
    for key, value in dict_to_add.items():
        dict_added[key][value_name_add] = value

    return dict_added


def add_to_list(list_prev, list_to_add):
    """
    Combine values from two lists of tuples based on equality of the first column.

    Parameters:
        list_prev (list): Existing list of tuples.
        list_to_add (list): List of tuples with new values to add.

    Returns:
        list: Combined list of tuples with old and new values.

    Raises:
        ValueError: If lists are not lists of tuples or if first columns are not equal.
    """
    # Check if both lists are lists of tuples
    if not all(
        isinstance(item, tuple) and len(item) >= 2 for item in list_prev
    ) or not all(isinstance(item, tuple) and len(item) >= 2 for item in list_to_add):
        raise ValueError("Both lists must be lists of tuples with at least two values.")

    # Check if first columns are the same
    if any(prev[0] != to_add[0] for prev, to_add in zip(list_prev, list_to_add)):
        raise ValueError(
            "First columns in previous list and list to add must be the same."
        )

    # Add values from second list to the tuples of the first list
    list_added = [
        (*prev[0:], *to_add[1:]) for prev, to_add in zip(list_prev, list_to_add)
    ]
    return list_added


def lookup_info_in_dict(key, info_lookup):
    """
    Look up info for a given key in a dictionary.

    Parameters:
        key: Key to look up.
        info_lookup (dict): Dictionary containing key-value pairs.

    Returns:
        Value associated with given key if found, or "not found" otherwise.
    """
    if key in info_lookup:
        return info_lookup[key]

    return "not found"


def add_info_to_list(list_to_lookup, info_dict):
    """
    Extend a list with information looked up from a dictionary.

    Parameters:
        list_to_lookup (list or list of tuples): List or list of tuples with keys to look up in first column.
        info_lookup (dict): Dictionary containing key-value pairs.

    Returns:
        list: List of tuples (original entries with info looked up added as last entry).
    """
    info_list = []

    for entry in list_to_lookup:
        if isinstance(entry, tuple):
            info_list.append(entry + (lookup_info_in_dict(entry[0], info_dict),))
        elif isinstance(entry, list):
            info_list.append(entry + [lookup_info_in_dict(entry[0], info_dict)])
        else:
            info_list.append((entry, lookup_info_in_dict(entry, info_dict)))

    return info_list


def add_infos_to_list(list_to_lookup, *info_dicts):
    """
    Extend a list with information looked up from multiple dictionaries.

    Parameters:
        list_to_lookup (list or list of tuples): List or list of tuples with keys to look up in first column.
        *info_dicts: Variable number of dictionaries containing key-value pairs.

    Returns:
        list: List of tuples (original entries with infos looked up added at end).
    """
    for info_dict in info_dicts:
        list_to_lookup = add_info_to_list(list_to_lookup, info_dict)

    return list_to_lookup


def reduce_dict_to_single_info(info_lookup, info_name):
    """
    Reduce a dictionary of dictionaries to a single information specified by given info_name.

    Parameters:
        info_lookup (dict): Dictionary where values can be dictionaries.
        info_name (str): Name of the information to extract from the nested dictionaries.

    Returns:
        dict: Updated dictionary where each value is replaced with the specified information.
    """
    for key, value in info_lookup.items():
        if isinstance(value, dict):
            try:
                info_lookup[key] = value[info_name]
            except KeyError:
                raise KeyError(
                    f"Info '{info_name}' not found in the dictionary for key '{key}'."
                )

    return info_lookup


def sort_and_cleanup_list(input_list):
    """
    Sort a list to remove duplicates and handle warnings based on criteria.

    Parameters:
        input_list (list): List of strings or a list of lists.

    Returns:
        list: A processed list with sorted and unique entries.
    """

    # Check if the input is a list of strings or a list of lists
    if not isinstance(input_list, list):
        raise ValueError("Input must be a list of strings or a list of lists.")

    # Convert all entries to strings
    input_list = [
        [str(entry) for entry in sublist] if isinstance(sublist, list) else str(sublist)
        for sublist in input_list
    ]

    # Replace nan (also "#NV" for absence of species? ["nan", "#NV"])
    input_list = replace_substrings(
        input_list, ["nan", "#NV"], "", at_end=True, warning_no_string=True
    )

    # # Replace entries with 2 values separated by " / " with default format
    # for entry in input_list:
    #     if isinstance(entry, list):
    #         for idx, item in enumerate(entry):
    #             if " / " in item:
    #                 entry[idx] = (
    #                     f"conflicting ({item.split(' / ')[0]} vs. {item.split(' / ')[1]})"
    #                 )

    # If input is a list of strings, return unique entries
    if all(isinstance(item, str) for item in input_list):
        return sorted(set(input_list))

    # If input is a list of lists
    unique_entries = defaultdict(list)

    # Collect all unique rows, rows with same entry in column 0 assigned to same key
    for entry in input_list:
        if isinstance(entry, list):
            unique_entries[entry[0]].append(entry)
        else:
            warnings.warn(f"{entry} is not a list. Skipping this entry.")

    unique_entries = {key: unique_entries[key] for key in sorted(unique_entries)}
    processed_list = []

    for key, group in unique_entries.items():
        if len(group) == 1:
            # Only one entry with this key, keep it
            processed_list.append(group[0])
        else:
            # Check if all entries are identical
            first_entry = group[0]
            processed_list.append(first_entry)
            differing_entries = [entry for entry in group if entry != first_entry]

            if differing_entries:
                # If there are differing entries, keep all of them
                processed_list.extend(differing_entries)
                warnings.warn(
                    f"Entries with the same first column value '{key}' differ in other columns."
                    "Keeping all unique entries."
                )

    return processed_list


def get_package_root():
    """
    Get root directory of the package containing the current module.

    Returns:
        Path: Path to package root directory.
    """
    # Get file path of current module
    module_path = Path(__file__).resolve()

    # Navigate up from module directory until package root is found
    for parent in module_path.parents:
        if (parent / "setup.py").is_file():
            return parent

    raise FileNotFoundError("Could not find package root.")


def get_deims_coordinates(deims_id):
    """
    Get coordinates for a DEIMS.iD.

    Parameters:
        deims_id (str): DEIMS.iD.

    Returns:
        dict: Location dictionary with keys:
            'lat': Site latitude (float), if found.
            'lon': Site longitude (float), if found.
            'deims_id': DEIMS.iD as provided (str).
            'found': Flag whether coordinates were found (bool).
            'name': Site name (str), if found.
    """
    if deims_id != deims._normaliseDeimsID(deims_id):
        print(
            f"Coordinates for DEIMS.iD '{deims_id}' not found (iD deviates from standard format)!"
        )
    else:
        try:
            deims_gdf = deims.getSiteCoordinates(deims_id, filename=None)
            # option: collect all coordinates from deims_gdf.boundary[0] ...
            # deims_gdf = deims.getSiteBoundaries(deims_id, filename=None)

            lon = deims_gdf.geometry[0].x
            lat = deims_gdf.geometry[0].y
            name = deims_gdf.name[0]
            print(f"Coordinates for DEIMS.iD '{deims_id}' found ({name}).")
            print(f"Latitude: {lat}, Longitude: {lon}")
            return {
                "lat": lat,
                "lon": lon,
                "deims_id": deims_id,
                "found": True,
                "name": name,
            }
        except Exception as e:
            print(f"Coordinates for DEIMS.iD '{deims_id}' not found ({e})!")

    return {"deims_id": deims_id, "found": False}


def get_deims_ids_from_xls(xls_file, header_row, country="ALL"):
    """
    Extract DEIMS IDs from an Excel file and return as a list of dictionaries.

    Parameters:
        xls_file (Path): Path to Excel file.
        header_row (int): Row number containing column names.
        country (str): Code to return only one country (e.g. "AT", "DE", ..., default is "ALL").

    Returns:
        list: List of dictionaries containing DEIMS.iDs.
    """
    if not xls_file.exists():
        raise FileNotFoundError(f"File '{xls_file}' not found.")

    # Load Excel file into a DataFrame
    df = pd.read_excel(xls_file, header=header_row)

    # Filter by country code
    if not country == "ALL":
        df = df[df["Country"] == country]

        if df.empty:
            warnings.warn(f"No entries found for country code '{country}'.")

    # Extract column containing list of DEIMS.iDs and return as list of dicts
    return df["DEIMS.ID"].tolist()


def get_plot_locations_from_csv(csv_file, *, header_row=0, sep=";"):
    """
    Extract plot locations from a CSV file and return as list of dictionaries.

    Parameters:
        csv_file (Path): Path to CSV file.
        header_row (int): Row number containing column names (default is 0).
        sep (str): Column separator between entries in rows (default is ';').

    Returns:
        list: List of dictionaries containing each unique location (latitude, longitude,
              station code(s), site code(s), and DEIMS.iD, if found).
    """
    if not csv_file.exists():
        raise FileNotFoundError(f"File '{csv_file}' not found.")

    # Load CSV file into a DataFrame
    df = pd.read_csv(csv_file, header=header_row, encoding="ISO-8859-1", sep=sep)

    if df.empty:
        warnings.warn(
            f"No entries found in file '{csv_file}'. Returning empty plot locations list."
        )
        return []
    else:
        locations = []
        entries_required = ["lat", "lon", "station_code", "site_code"]
        # or leave out site code and station code?

        # Helper function to check if coordinates already exist in locations
        def find_existing_location(lat, lon):
            for location in locations:
                if location["lat"] == lat and location["lon"] == lon:
                    return location

            return None

        # Extract all entries from station file
        for _, row in df.iterrows():
            entries_raw = {col.lower(): row[col] for col in df.columns}
            entries_missing = False

            for item in entries_required:
                if item not in entries_raw:
                    warnings.warn(
                        f"No '{item}' entry found. Skipping plot location row."
                    )
                    entries_missing = True
                    break

            if not entries_missing:
                # Use only items needed, could be extended, e.g. using also altitude
                lat = entries_raw["lat"]
                lon = entries_raw["lon"]
                station_code = entries_raw["station_code"]
                site_code = entries_raw["site_code"]
                deims_id = site_code.split("/")[-1]
                deims_id_check = get_deims_coordinates(deims_id)

                if deims_id_check["found"]:
                    if lat != deims_id_check["lat"] or lon != deims_id_check["lon"]:
                        warnings.warn(
                            f"Station coordinates (lat.: {lat}, lon.: {lon}) differ from "
                            f"representative coordinates for DEIMS.iD (lat.: {deims_id_check["lat"]}, "
                            f"lon: {deims_id_check["lon"]})! Using station coordinates."
                        )

                # Check if coordinates already exist in locations
                existing_location = find_existing_location(lat, lon)

                if existing_location:
                    if station_code not in existing_location["station_code"]:
                        existing_location["station_code"].append(station_code)
                    if site_code not in existing_location["site_code"]:
                        existing_location["site_code"].append(site_code)
                    if (
                        deims_id_check["found"]
                        and deims_id != existing_location["deims_id"]
                    ):
                        raise ValueError(
                            "Different valid DEIMS.iDs found for identical spatial coordinates!"
                        )
                        # existing_location["deims_id"].append(deims_id)
                else:
                    location = {
                        "lat": lat,
                        "lon": lon,
                        "station_code": [station_code],
                        "site_code": [site_code],
                    }
                    if deims_id_check["found"]:
                        location.update(
                            deims_id=deims_id, found=True, name=deims_id_check["name"]
                        )

                    locations.append(location)

        return locations


def parse_locations(locations_str):
    """
    Parse a string of locations (separated by semicolons) into a list of dictionaries.

    Args:
        locations_str (str): String containing locations separated by semicolons. Each location can be in the
                             format 'lat,lon' for coordinates or a plain string for a DEIMS.iD.

    Returns:
        list: List of dictionaries. Each dictionary contains 'lat' and 'lon' keys with float values,
              and keys 'deims_id' (str), 'found' (TRUE), 'name' (str) if DEIMS.iD was provided and found.
    """
    locations = []
    print("Parsing locations from input string ...")

    for item in locations_str.split(";"):
        if "," in item:
            try:
                lat, lon = map(float, item.split(","))
                locations.append({"lat": lat, "lon": lon})
                print(f"Latitude: {lat}, Longitude: {lon}")

            except ValueError:
                raise argparse.ArgumentTypeError(
                    f"Invalid coordinate input: {item}. Expected format is 'lat,lon'."
                )
        else:
            location = get_deims_coordinates(item)

            if location["found"]:
                locations.append(location)
            else:
                raise ValueError(f"Coordinates for DEIMS.id '{item}' not found!")

    return locations


def get_unique_keys(
    list_of_dicts,
):
    """
    Get the unique keys from a list of dictionaries.

    Parameters:
        list_of_dicts (list): List of dictionaries.

    Returns:
        list: List of unique keys.
    """
    unique_keys = []

    for d in list_of_dicts:
        for key in d.keys():
            if key not in unique_keys:
                unique_keys.append(key)

    return unique_keys


def reproject_coordinates(lat, lon, target_crs):
    """
    Reproject latitude and longitude coordinates to a target CRS.

    Parameters:
        lat (float): Latitude.
        lon (float): Longitude.
        target_crs (str): Target Coordinate Reference System in WKT format.

    Returns:
        tuple (float): Reprojected coordinates (easting, northing).
    """
    # Define source CRS (EPSG:4326 - WGS 84, commonly used for lat/lon)
    src_crs = pyproj.CRS("EPSG:4326")

    # Create a transformer to convert from source CRS to target CRS
    # (always_xy: use lon/lat for source CRS and east/north for target CRS)
    transformer = pyproj.Transformer.from_crs(src_crs, target_crs, always_xy=True)

    # Reproject coordinates (order is lon, lat!)
    east, north = transformer.transform(lon, lat)
    return east, north


def extract_raster_value(tif_file, location, *, band_number=1, attempts=5, delay=2):
    """
    Extract value from raster file at specified coordinates.

    Parameters:
        tif_file (str): TIF file path or URL.
        coordinates (dict): Dictionary with 'lat' and 'lon' keys ({'lat': float, 'lon': float}).
        band_number (int): Band number for which the value shall be extracted (default is 1).
        attempts (int): Number of attempts to open the TIF file in case of errors (default is 5).
        delay (int): Number of seconds to wait between attempts (default is 2).

    Returns:
        tuple: Extracted value (None if extraction failed), and time stamp.
    """
    while attempts > 0:
        time_stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

        try:
            with rasterio.open(tif_file) as src:
                # Get target CRS (as str in WKT format) from TIF file
                target_crs = src.crs.to_wkt()

                # Reproject coordinates to target CRS
                east, north = reproject_coordinates(
                    location["lat"], location["lon"], target_crs
                )

                # Extract value from specified band number at specified coordinates
                value = next(src.sample([(east, north)], indexes=band_number))

            return value[0], time_stamp
        except rasterio.errors.RasterioIOError as e:
            attempts -= 1
            print(f"Reading TIF file failed (Error {e}).")

            if attempts > 0:
                print(f"Retrying in {delay} seconds ...")
                time.sleep(delay)
            else:
                return None, time_stamp


def check_url(url, attempts=5, delay=2):
    """
    Check if a file exists at specified URL and retrieve its content type.

    Parameters:
        url (str): URL to check.
        attempts (int): Number of attempts in case of connection errors or specific status codes (default is 5).
        delay (int): Number of seconds to wait between attempts (default is 2).

    Returns:
        str: URL if existing (original or redirected), None otherwise.
    """
    if not url:
        return None

    retry_status_codes = {502, 503, 504}

    while attempts > 0:
        try:
            response = requests.head(url, allow_redirects=True)

            if response.status_code == 200:
                return response.url
            elif response.status_code in retry_status_codes:
                attempts -= 1

                if attempts > 0:
                    time.sleep(delay)
            else:
                return None
        except requests.ConnectionError:
            attempts -= 1

            if attempts > 0:
                time.sleep(delay)

    return None


def download_file_opendap(file_name, source_folder, target_folder):
    """
    Download a file from OPeNDAP server 'grasslands-pdt'.

    Args:
        file_name (str): Name of file to download.
        source_folder (str): Folder where file is expected on OPeNDAP server.
        target_folder (str): Folder where file will be saved.

    Returns:
        None
    """
    # will be "https://opendap.biodt.eu"
    url = f"http://opendap.biodt.eu/grasslands-pdt/{source_folder}/{file_name}"
    print(f"Downloading '{url}' ...")
    response = requests.get(url)

    # # Variant with authentication using OPeNDAP credentials from .env file.
    # dotenv_config = dotenv_values(".env")
    # session = requests.Session()
    # session.auth = (dotenv_config["opendap_user"], dotenv_config["opendap_pw"])
    # response = session.get(url)

    if response.status_code == 404:
        print(f"Error: Specified file '{url}' not found!")
        return None

    # Specify target file, create directory if missing, save target file
    target_file = target_folder / file_name
    Path(target_file).parent.mkdir(parents=True, exist_ok=True)

    with open(target_file, "wb") as file:
        file.write(response.content)


def day_of_year_to_date(year, day_of_year, leap_year_considered=True):
    """
    Convert a day of a year to corresponding date.

    Args:
        year (int): Year.
        day_of_year (int): Day of year (count from 1 for January 1st).
        leap_year_considered (bool): Day of year correctly accounts for leap year (default is True).

    Returns:
        datetime: Corresponding date.
    """
    # Adjust days after Feb 29 for leap year, if not correct already
    if (not leap_year_considered) and is_leap_year(year) and (day_of_year > 59):
        delta_days = day_of_year
    else:
        delta_days = day_of_year - 1

    return datetime(year, 1, 1) + timedelta(days=delta_days)


def is_leap_year(year):
    """
    Check if a given year is a leap year.

    Parameters:
        year (int): Year.

    Returns:
        bool: True if the year is a leap year, False otherwise.
    """
    # A year is a leap year if it is divisible by 4,
    # except for years that are divisible by 100 but not by 400
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
