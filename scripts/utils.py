"""
Module Name: utils.py
Author: Thomas Banitz, Taimur Khan, Tuomas Rossi, Franziska Taubert, BioDT
Date: February, 2024
Description: Utility functions for uc-grassland building block. 
"""

import csv
from collections import Counter
from dotenv import dotenv_values
from pathlib import Path
import pandas as pd
import pyproj
import rasterio
import requests


def add_string_to_file_name(file_name, string_to_add):
    """
    Add a string before the suffix of a file name.

    Parameters:
    - file_name (Path): Path of the file.
    - string_to_add (str): String to add before the suffix.

    Returns:
    - new_file_name (Path): New file path with the added string.
    """
    # Convert the WindowsPath object to a stringdo_warning
    file_str = str(file_name)

    # Get the suffix (including the dot)
    suffix = file_name.suffix

    # Insert the string before the suffix
    new_file_str = file_str[: -len(suffix)] + string_to_add + suffix

    # Convert the modified string back to a WindowsPath object
    new_file_name = Path(new_file_str)

    return new_file_name


def replace_substrings(
    input_data,
    substrings_to_replace,
    replacement_string,
    at_end=False,
    warning_no_string=False,
):
    """
    Replace specified substrings with another string in a single string or a list of strings.

    Parameters:
    - input_data (str or list): String or list of strings.
    - substrings_to_replace (str or list): Substring or list of substrings to be replaced.
    - replacement_string (str): New string to replace the specified substring(s).
    - at_end (bool): Replace the substring(s) only if appearing at the end of each string (default is False).
    - warning_no_string (bool): Throw warning for input data list elements that are no string (default is False).

    Returns:
    - str or list: If input_data is a string, the modified string; if input_data is a list, a new list with the specified substrings replaced in each element.
    """

    # Nested functions for either replacing substring at the end or everywhere
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

    if isinstance(input_data, str):
        input_data = [input_data]

    # For list of input strings, replace list of substrings with the replacement string
    if isinstance(input_data, list):
        modified_list = []
        for original_string in input_data:
            modified_string = original_string

            if isinstance(modified_string, str):
                for substring in substrings_to_replace:
                    modified_string = (
                        replace_substring_at_end(modified_string, substring)
                        if at_end
                        else replace_substring(modified_string, substring)
                    )
            elif warning_no_string:
                # Warning for non string element in list.
                print(
                    f"Warning: {modified_string} is not a string. No replacements performed."
                )

            modified_list.append(modified_string)
    else:
        raise ValueError("Input data must be a string or a list of strings.")

    # Return only string if input data was just a string, list of strings otherwise
    return modified_list[0] if len(modified_list) == 1 else modified_list


def count_duplicates(lst):
    """
    Count occurrences of duplicate items in a list.

    Parameters:
    - lst (list): List to analyze.

    Returns:
    - dict: Dictionary where (sorted) keys are duplicate items and values are their counts.
    """
    counter = Counter(lst)
    duplicates = {item: count for item, count in sorted(counter.items()) if count > 1}

    return duplicates


def get_row_values(key, values):
    """
    Get row values based on the type of values.

    Parameters:
    - key (str): Key from the dictionary.
    - values (str or dict): Values associated with the key.

    Returns:
    - list: Row values to be written to the file.
    """
    if isinstance(values, dict):
        row_values = [key] + list(values.values())
    else:
        row_values = [key, values]

    return row_values


def dict_to_file(dict_to_write, column_names, file_name):
    """
    Write a dictionary to a text file (tab-separated) or an Excel file.

    Parameters:
    - dict_to_write (dict): Dictionary to be written to the file.
    - column_names (list): List of all column names (strings, includes first column for dict_to_write keys).
    - file_name (str or Path): Path of the output file.
    """
    file_path = Path(file_name)
    file_suffix = file_path.suffix.lower()

    if file_suffix == ".txt":
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter="\t")
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
                    pd.DataFrame([get_row_values(key, values)], columns=column_names),
                ],
                ignore_index=True,
            )

        df.to_excel(file_path, index=False)
    else:
        print(
            f"Error: Unsupported file format. Supported formats are '.txt' and '.xlsx'."
        )

    print(f"Dictionary written to file '{file_name}'.")


def list_to_file(list_to_write, column_names, file_name):
    """
    Write a list of tuples to a text file (tab-separated) or an Excel file.

    Parameters:
    - list_to_write (list): List of strings or tuples or dictionaries to be written to the file.
    - column_names (list): List of column names (strings).
    - file_name (str or Path): Path of the output file.
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
    # Check if all tuples in the list have the same length as the column_names list
    elif not all(len(entry) == len(column_names) for entry in list_to_write):
        print(
            f"Error: All tuples in the list must have {len(column_names)} entries (same as column_names)."
        )

        return

    file_path = Path(file_name)
    file_suffix = file_path.suffix.lower()

    if file_suffix == ".txt":
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter="\t")
            header = column_names
            writer.writerow(header)  # Header row

            for entry in list_to_write:
                writer.writerow(entry)
    elif file_suffix == ".xlsx":
        df = pd.DataFrame(list_to_write, columns=column_names)
        df.to_excel(file_path, index=False)
    else:
        print(
            f"Error: Unsupported file format. Supported formats are '.txt' and '.xlsx'."
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
        value_name_prev (str): Name for the existing values in the updated dictionary (default is 'info1').
        value_name_add (str): Name for the new values in the updated dictionary (default is 'info2').

    Returns:
        dict: Updated dictionary with combined old and new values.

    Raises:
        ValueError: If the keys in dict_prev and dict_to_add are not the same.
    """
    # Check if the keys are the same
    if set(dict_prev.keys()) != set(dict_to_add.keys()):
        raise ValueError(
            "Keys in previous dictionary and added dictionary must be the same."
        )

    # Convert dict_prev to a dictionary of dictionaries if not already
    if all(isinstance(value, dict) for value in dict_prev.values()):
        dict_added = dict_prev
    else:
        dict_added = {key: {value_name_prev: value} for key, value in dict_prev.items()}

    # Add the new values to each key
    for key, value in dict_to_add.items():
        dict_added[key][value_name_add] = value

    return dict_added


def add_to_list(list_prev, list_to_add):
    """
    Combine values from two lists of tuples based on the equality of the first column.

    Parameters:
        list_prev (list): Existing list of tuples.
        list_to_add (list): List of tuples with new values to add.

    Returns:
        list: Combined list of tuples with old and new values.

    Raises:
        ValueError: If the lists are not lists of tuples or if the first columns are not equal.
    """
    # Check if both lists are lists of tuples
    if not all(
        isinstance(item, tuple) and len(item) >= 2 for item in list_prev
    ) or not all(isinstance(item, tuple) and len(item) >= 2 for item in list_to_add):
        raise ValueError("Both lists must be lists of tuples with at least two values.")

    # Check if the first columns are the same
    if any(prev[0] != to_add[0] for prev, to_add in zip(list_prev, list_to_add)):
        raise ValueError(
            "First columns in the previous list and list to add must be the same."
        )

    # Add values from the second list to the tuples of the first list
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
        Value associated with the given key if found, or "not found" otherwise.
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
        list: List of tuples (original entries with info looked up added as the last entry).
    """
    info_list = []

    for entry in list_to_lookup:
        if isinstance(entry, tuple):
            info_list.append(entry + (lookup_info_in_dict(entry[0], info_dict),))
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
    Reduce a dictionary of dictionaries to a single information specified by the given info_name.

    Parameters:
        info_lookup (dict): Dictionary where values can be dictionaries.
        info_name (str): Name of the information to extract from the nested dictionaries.

    Returns:
        dict: Updated dictionary where each value is replaced with the specified information.

    Raises:
        KeyError: If the specified info_name is not found in any of the nested dictionaries.
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


def get_package_root():
    """
    Get the root directory of the package containing the current module.

    Returns:
    - Path: The path to the package root directory.
    """
    # Get the file path of the current module
    module_path = Path(__file__).resolve()

    # Navigate up from the module directory until the package root is found
    for parent in module_path.parents:
        if (parent / "setup.py").is_file():
            return parent

    raise FileNotFoundError("Could not find package root.")


def get_deims_ids_from_xls(xls_file, header_row):
    """
    Extract DEIMS IDs from an Excel file and return as a list of dictionaries.

    Parameters:
    - xls_file (Path): Path to the Excel file.
    - header_row (int): Row number containing the column names.

    Returns:
    - list: List of dictionaries containing DEIMS IDs.
    """
    if not xls_file.exists():
        raise FileNotFoundError(f"File '{xls_file}' not found.")

    # Load the Excel file into a DataFrame
    df = pd.read_excel(xls_file, header=header_row)

    # Extract the column containing the list of DEIMS.iDs and return as list of dicts
    return [{"deims_id": deims_id} for deims_id in df["DEIMS.ID"].tolist()]


def get_unique_keys(list_of_dicts):
    """
    Get the unique keys from a list of dictionaries.

    Parameters:
    - list_of_dicts (list): List of dictionaries.

    Returns:
    - list: List of unique keys.
    """
    unique_keys = []

    # Iterate over each dictionary in the list
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
    # Define the source CRS (EPSG:4326 - WGS 84, commonly used for lat/lon)
    src_crs = pyproj.CRS("EPSG:4326")

    # Create a transformer to convert from the source CRS to the target CRS
    # (always_xy: use lon/lat for source CRS and east/north for target CRS)
    transformer = pyproj.Transformer.from_crs(src_crs, target_crs, always_xy=True)

    # Reproject the coordinates (order is lon, lat!)
    east, north = transformer.transform(lon, lat)

    return east, north


def extract_raster_value(tif_file, location):
    """
    Extract values from raster file at specified coordinates.

    Parameters:
        tif_file (str): Path to TIF file.
        category_mapping (dict): Mapping of category indices to category names.
        location (dict): Dictionary with 'lat' and 'lon' keys.

    Returns:
        list: A list of extracted values.
    """
    with rasterio.open(tif_file) as src:
        # Get the target CRS (as str in WKT format) from the TIF file
        target_crs = src.crs.to_wkt()
        # (GER_Preidl, EUR_Pflugmacher use Lambert Azimuthal Equal Area in meters)

        # Reproject the coordinates to the target CRS
        east, north = reproject_coordinates(
            location["lat"], location["lon"], target_crs
        )

        # Extract the value at the specified coordinates
        value = next(src.sample([(east, north)]))

    return value[0]


def download_file_opendap(file_name, folder):
    """
    Download a file from OPeNDAP server, subfolder 'biodt-grassland-pdt'.
    Using OPeNDAP credentials from .env file.

    Args:
        file_name (str): Name of the file to download.
        folder (str): Folder where the file will be saved.

    Returns:
        None
    """
    print(f"Downloading file '{file_name}' from OPeNDAP server...")

    url = "http://134.94.199.14/grasslands-pdt/" + file_name
    response = requests.get(url)

    # # Variant with authentication
    # dotenv_config = dotenv_values(".env")
    # session = requests.Session()
    # session.auth = (dotenv_config["opendap_user"], dotenv_config["opendap_pw"])
    # response = session.get(url)

    if response.status_code == 404:
        print(
            f"Error: Specified file '{file_name}' not found in 'biodt-grassland-pdt'!"
        )
        return

    target_file = folder / file_name

    with open(target_file, "wb") as file:
        file.write(response.content)
