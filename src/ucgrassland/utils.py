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
import calendar
import csv
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import MappingProxyType

import deims
import pandas as pd
import pyproj
import rasterio
import requests
from dateutil.parser import parse

from ucgrassland.logger_config import logger

# will be "https://opendap.biodt.eu/..."
OPENDAP_ROOT = "http://opendap.biodt.eu/grasslands-pdt/"
NON_DEIMS_LOCATIONS = MappingProxyType(
    {
        # KU Leuven site, rough mean of coordinates of all plots
        "KUL-site": {
            "lat": 51.0,
            "lon": 5.0,
            "deims_id": "KUL-site",
            "found": True,
            "name": "KUL-site (KU Leuven)",
        }
    }
)


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


def get_source_from_elter_data_file_name(
    file_name, *, split_delimiter="_", front_strings_to_remove=2
):
    """
    Extract source name from an eLTER data file name.

    Parameters:
        file_name (str or Path): File name to extract source from.
        split_delimiter (str): Delimiter to replace dots and split file name string (default is '_').
        front_strings_to_remove (int): Number of front substrings to remove (default is 2 for country code and site short name).
    """

    if isinstance(file_name, Path):
        file_name = file_name.name

    if isinstance(file_name, str):
        # Remove file extension, replace dots with underscores
        source = split_delimiter.join(file_name.split(".")[:-1])

        # Remove front substrings as specified
        source = split_delimiter.join(
            source.split(split_delimiter)[front_strings_to_remove:]
        )

        return source
    else:
        try:
            raise ValueError("Input must be a string or a Path object.")
        except ValueError as e:
            logger.error(e)
            raise


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
            logger.warning(f"{item} is not a string. No replacements performed.")
        return item  # If it's not a string or list, return as is

    # Process input_data, which can be a string, list, or list of lists
    if isinstance(input_data, (str, list)):
        return process_item(
            input_data
        )  # Process both string and list of strings or list of lists
    else:
        try:
            raise ValueError(
                "Input data must be a string, a list of strings, or a list of lists."
            )
        except ValueError as e:
            logger.error(e)
            raise


def get_tuple_list(
    input_list,
    *,
    replace_nan="nan",
    replace_none="None",
    columns_to_remove=[],
    return_sorted=False,
    header_lines=0,
):
    """
    Convert a list of lists to a list of tuples.

    Parameters:
        input_list (list): List of lists.

    Returns:
        list: List of tuples.
    """
    # Convert each sublist to a tuple, if not already
    tuple_list = []

    for entry in input_list[header_lines:]:
        if isinstance(entry, list):
            tuple_list.append(tuple(entry))
        elif isinstance(entry, tuple):
            tuple_list.append(entry)
        elif isinstance(entry, str):
            tuple_list.append((entry,))
        else:
            logger.warning(f"List entry '{entry}' is not a list, tuple, or string.")

    if replace_nan:
        tuple_list = [
            tuple(replace_nan if pd.isna(x) else x for x in entry)
            for entry in tuple_list
        ]

    if replace_none:
        tuple_list = [
            tuple(replace_none if x is None else x for x in entry)
            for entry in tuple_list
        ]

    if columns_to_remove:
        tuple_list = [
            tuple(x for index, x in enumerate(entry) if index not in columns_to_remove)
            for entry in tuple_list
        ]

    if return_sorted:
        tuple_list.sort(key=lambda x: x)

    return input_list[:header_lines] + tuple_list


def count_duplicates(input_list, *, key_column=0, columns_to_ignore=[]):
    """
    Count occurrences of duplicate items in a list.

    Parameters:
        input_list (list): List to analyze.
        key_column (int): Index of column to use as key for counting duplicates (default is 0).
        columns_to_ignore (list): List of column indices to ignore when comparing all entries (default is []).

    Returns:
        dict: Dictionary where (sorted) keys are duplicate items and values are their counts.
    """
    filtered_list = get_tuple_list(input_list, columns_to_remove=columns_to_ignore)
    counter = Counter(filtered_list)

    if key_column == "all":
        duplicates = {
            item: count for item, count in sorted(counter.items()) if count > 1
        }
    else:
        duplicates = {
            item[key_column]: count
            for item, count in sorted(counter.items())
            if count > 1
        }

    return duplicates


def remove_duplicates(input_list, *, duplicates=None, header_lines=0):
    """
    Remove duplicate items from a list.

    Parameters:
        input_list (list): List to remove duplicates from.
        duplicates (dict): Dictionary of duplicate items and their counts (default is None to count duplicates here).
    """
    if duplicates is None:
        duplicates = count_duplicates(input_list, key_column="all")

    tuple_list = get_tuple_list(
        input_list, return_sorted=True, header_lines=header_lines
    )
    unique_list = []

    for entry in tuple_list[header_lines:]:
        if entry in duplicates:
            duplicates[entry] -= 1

            # Remove entry from duplicates if count reaches 1
            if duplicates[entry] == 1:
                duplicates.pop(entry)
        else:
            unique_list.append(list(entry))

    # Sort by all columns
    unique_list.sort(key=lambda x: x)

    return tuple_list[:header_lines] + unique_list


def get_row_values(key, values):
    """
    Get row values based on type of values.

    Parameters:
        key (str): Key from the dictionary.
        values (str or dict): Values associated with the key.

    Returns:
        list: Row values.
    """
    if isinstance(key, tuple):
        key = list(key)
    elif not isinstance(key, list):
        key = [key]

    if isinstance(values, dict):
        row_values = key + list(values.values())
    elif isinstance(values, list):
        row_values = key + values
    else:
        row_values = key + [values]

    return row_values


def dict_to_file(dict_to_write, file_name, *, column_names=["key", "value"]):
    """
    Write a dictionary to a text file (tab-separated) or csv file (;-separated) or an Excel file.

    Parameters:
        dict_to_write (dict): Dictionary to be written to file.
        file_name (str or Path): Path of output file (suffix determines file type).
        column_names (list): List of column names (strings) to write as header line (default is ['key', 'value']).
    """
    if file_name:
        file_path = Path(file_name)
        file_suffix = file_path.suffix.lower()

        # Create data directory if missing
        Path(file_name).parent.mkdir(parents=True, exist_ok=True)

        if file_suffix in [".txt", ".csv"]:
            with open(
                file_path, "w", newline="", encoding="utf-8", errors="replace"
            ) as file:
                writer = (
                    csv.writer(file, delimiter="\t")
                    if file_suffix == ".txt"
                    else csv.writer(file, delimiter=";")
                )

                if column_names is not None:
                    writer.writerow(column_names)  # Header row

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
            logger.error(
                "Unsupported file format. Supported formats are '.txt', '.csv' and '.xlsx'."
            )

        logger.info(f"Dictionary written to file '{file_name}'.")


def find_column_index(raw_data, column_id, *, header_lines=1, warn_not_found=True):
    """
    Find index of specified column in data frame or list of lists.

    Parameters:
        raw_data (pd.DataFrame or list): Data frame or list of lists to find column.
        column_id (str or int): Column identifier (name as string or index).
        header_lines (int): Number of header lines in list of lists (default is 1).
        warn_not_found (bool): Warn if column is not found (default is True).

    Returns:
        int: Index of specified column, if found.
    """
    if column_id is None:
        logger.error(
            "Column identifier is None. Cannot find column in data. Returning None."
        )
        return None

    if isinstance(raw_data, pd.DataFrame):
        if isinstance(column_id, str):
            try:
                return raw_data.columns.get_loc(column_id)
            except KeyError:
                # If exact match not found, try lowercase match
                lower_column_id = column_id.lower()

                for col in raw_data.columns:
                    if col.lower() == lower_column_id:
                        return raw_data.columns.get_loc(col)

                logger.error(f"Column '{column_id}' not found in DataFrame.")
        elif isinstance(column_id, int):
            if column_id in range(len(raw_data.columns)):
                return column_id
            else:
                try:
                    raise ValueError(
                        f"Column number '{column_id}' out of range in DataFrame."
                    )
                except ValueError as e:
                    logger.error(e)
                    raise
        # elif isinstance(column_id, list):
        #     for col in column_id:
        #         index = find_column_index(raw_data, col)

        #         if index is not None:
        #             return index
        else:
            try:
                raise ValueError(
                    "Invalid column identifier. Please provide a column name (str) or column "
                    "number (int) or a list of column names (strings)."
                )
            except ValueError as e:
                logger.error(e)
                raise
    elif isinstance(raw_data, list):
        if isinstance(column_id, str):
            if column_id in raw_data[header_lines - 1]:
                return raw_data[header_lines - 1].index(column_id)
            elif column_id.lower() in raw_data[header_lines - 1]:
                # If exact match not found, try lowercase match
                return raw_data[header_lines - 1].index(column_id.lower())
        elif isinstance(column_id, int):
            if column_id in range(len(raw_data[header_lines - 1])):
                return column_id
            else:
                try:
                    raise ValueError(
                        f"Column number '{column_id}' out of range in header line of list."
                    )
                except ValueError as e:
                    logger.error(e)
                    raise
        # elif isinstance(column_id, list):
        #     for col in column_id:
        #         index = find_column_index(raw_data, col)

        #         if index is not None:
        #             return index
        else:
            try:
                raise ValueError(
                    "Invalid column identifier. Please provide a column name (str) or column "
                    "number (int) or a list of column names (strings)."
                )
            except ValueError as e:
                logger.error(e)
                raise
    else:
        try:
            raise TypeError("Input data must be a pandas DataFrame or a list of lists.")
        except TypeError as e:
            logger.error(e)
            raise

    if warn_not_found:
        logger.error(f"Column '{column_id}' not found. Returning None.")

    return None


def list_to_file(list_to_write, file_name, *, column_names=None):
    """
    Write a list of tuples to a text file (tab-separated) or csv file (;-separated) or an Excel file.

    Parameters:
        list_to_write (list): List of strings or tuples or dictionaries to be written to the file.
        file_name (str or Path): Path of output file (suffix determines file type).
        column_names (list): List of column names (strings) to write as header line (default is None).
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
    elif column_names is not None and not all(
        len(entry) == len(column_names) for entry in list_to_write
    ):
        logger.error(
            f"All tuples in the list must have {len(column_names)} entries (same as column_names)."
        )
        return

    file_path = Path(file_name)
    file_suffix = file_path.suffix.lower()

    # Create data directory if missing
    Path(file_name).parent.mkdir(parents=True, exist_ok=True)

    if file_suffix in [".txt", ".csv"]:
        with open(
            file_path, "w", newline="", encoding="utf-8", errors="replace"
        ) as file:
            writer = (
                csv.writer(file, delimiter="\t")
                if file_suffix == ".txt"
                else csv.writer(file, delimiter=";")
            )

            if column_names is not None:
                writer.writerow(column_names)  # Header row

            for entry in list_to_write:
                writer.writerow(entry)
    elif file_suffix == ".xlsx":
        df = pd.DataFrame(list_to_write, columns=column_names)
        df.to_excel(file_path, index=False)
    else:
        try:
            raise ValueError(
                "Unsupported file format. Supported formats are '.txt', '.csv' and '.xlsx'."
            )
        except ValueError as e:
            logger.error(e)
            raise

    logger.info(f"List written to file '{file_name}'.")


def format_datestring(input_str, *, target_format="%Y-%m-%d", indicator_dayfirst="."):
    """
    Convert date strings to standard date format for sorting.

    Parameters:
        input_str (str): Date string to convert.
        target_format (str): Target date format (default is '%Y-%m-%d').
        indicator_dayfirst (str): Indicator for day-first date format (default is '.').
            This indicator needs to be present in the input string twice to assume that
            the input string is in day-first format.

    Returns:
        str: Formatted date string.
    """
    if not isinstance(input_str, str):
        # logger.warning(f"Input date '{input_str}' is not a string. Returning unchanged.")
        return input_str

    # Apply only to full data strings (length 10)
    if len(input_str) != 10:
        logger.warning(
            f"Input date string '{input_str}' is not of length 10. Returning unchanged."
        )
        return input_str

    try:
        # dayfirst=True if 2 times 'indicator_dayfirst' in input string (e.g. split by '.' results in 3 parts)
        dayfirst = len(input_str.split(indicator_dayfirst)) == 3
        formatted_date_str = parse(input_str, dayfirst=dayfirst).strftime(target_format)
        return formatted_date_str
    except ValueError:
        logger.warning(
            f"Could not parse input date string '{input_str}'. Returning unchanged."
        )
        return input_str


def get_unique_values_from_column(input_list, column_index, *, header_lines=1):
    """
    Get unique values from a column in a list of lists.

    Parameters:
        input_list (list): List of lists.
        column_index (int): Index of the column to extract unique values from.
        header_lines (int): Number of header lines to ignore in list of lists (default is 1).

    Returns:
        list: List of unique values from the specified column.
    """
    column_index = find_column_index(input_list, column_index)
    column_values = [row[column_index] for row in input_list[header_lines:]]

    # Convert nan to string for sorting and usability as selection criterion later
    column_values = ["nan" if pd.isna(value) else value for value in column_values]
    unique_values = sorted(set(column_values))

    return unique_values


def get_rows_with_value_in_column(input_list, column_index, value):
    """
    Get rows with a specified value in a column in a list of lists.

    Parameters:
        input_list (list): List of lists.
        column_index (int): Index of the column to search for the value.
        value: Value to search for in the specified column.

    Returns:
        list: List of rows with the specified value in the specified column.
    """
    column_index = find_column_index(input_list, column_index)
    rows_with_value = [row for row in input_list if row[column_index] == value]

    return rows_with_value


def get_list_of_columns(input_list, columns_wanted):
    """
    Get a list containing only specified columns from a list of lists.

    Parameters:
        input_list (list): List of lists.
        columns_wanted (list): List of column names or indices to extract.
    """
    column_indexes = []
    columns_found = []

    for column in columns_wanted:
        column_index = find_column_index(input_list, column)

        if column_index is not None:
            column_indexes.append(column_index)
            columns_found.append(column)

    sublist = [[row[index] for index in column_indexes] for row in input_list]

    return sublist, columns_found


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
    """
    # Check if keys are the same
    if set(dict_prev.keys()) != set(dict_to_add.keys()):
        try:
            raise ValueError(
                "Keys in previous dictionary and added dictionary must be the same."
            )
        except ValueError as e:
            logger.error(e)
            raise

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
    """
    # Check if both lists are lists of tuples
    if not all(
        isinstance(item, tuple) and len(item) >= 2 for item in list_prev
    ) or not all(isinstance(item, tuple) and len(item) >= 2 for item in list_to_add):
        try:
            raise ValueError(
                "Both lists must be lists of tuples with at least two values."
            )
        except ValueError as e:
            logger.error(e)
            raise

    # Check if first columns are the same
    if any(prev[0] != to_add[0] for prev, to_add in zip(list_prev, list_to_add)):
        try:
            raise ValueError(
                "First columns in previous list and list to add must be the same."
            )
        except ValueError as e:
            logger.error(e)
            raise

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


def add_columns_to_list(input_list, columns_to_add):
    """
    Add items from columns_to_add to each sublist in input_list.

    Parameters:
        input_list (list of lists): List of sublists to which items will be added.
        columns_to_add (list): List of items or sublists to add to each sublist in input_list.

    Returns:
        list: Combined list with items added to each sublist.
    """
    # Ensure both lists have the same length
    if len(input_list) != len(columns_to_add):
        try:
            raise ValueError("Both lists must have the same length!")
        except ValueError as e:
            logger.error(e)
            raise

    # Ensure each entry in input_list is a sublist
    normalized_input_list = [
        sublist if isinstance(sublist, list) else [sublist] for sublist in input_list
    ]

    # Add the item(s) to each sublist
    combined_list = [
        sublist + (item if isinstance(item, list) else [item])
        for sublist, item in zip(normalized_input_list, columns_to_add)
    ]

    return combined_list


def add_info_to_list(list_to_lookup, info_dict):
    """
    Extend a list with information looked up from a dictionary.

    Parameters:
        list_to_lookup (list or list of tuples list of lists): List with keys to look up in first column.
        info_lookup (dict): Dictionary containing key-value pairs.

    Returns:
        list: List of tuples or list of lists (original entries with info looked up added as last entry).
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
                try:
                    raise KeyError(
                        f"Info '{info_name}' not found in the dictionary for key '{key}'."
                    )
                except KeyError as e:
                    logger.error(e)
                    raise

    return info_lookup


def combine_info_strings(info_1, info_2):
    """
    Combine infos for a species.

    Parameters:
        info_1 (str): First info entry.
        info_2 (str): Second info entry.

    Returns:
        str: Combined info entry.
    """
    info_1_core = replace_substrings(info_1, ["(", ")", "conflicting "], "")
    info_2_core = replace_substrings(info_2, ["(", ")", "conflicting "], "")

    # Allow combination without conflict of infos that can be woody
    woody_infos = [
        "woody",
        "tree",
        "shrub",
        "shrub/tree",
        "legume?",
        "legume?/tree",
        "legume?/shrub",
        "legume?/shrub/tree",
    ]

    # Return one info, if it already contains the other info
    if info_1_core in info_2_core:
        return info_2
    elif info_2_core in info_1_core:
        return info_1
    else:
        info_both = sorted((info_1_core, info_2_core))

        # Combine without conflict, if both infos are woody (PFT or Woodiness)
        if info_1_core in woody_infos and info_2_core in woody_infos:
            return f"({info_both[0]}/{info_both[1]})"
        # Combine as conflicting otherwise
        else:
            return f"conflicting ({info_both[0]} vs. {info_both[1]})"


def sort_and_cleanup_list(
    input_list, *, unique_entry_column=0, combine_differing_entries=False
):
    """
    Sort a list to remove duplicates and handle warnings based on criteria.

    Parameters:
        input_list (list): List of strings or a list of lists.
        unique_entry_column (int): Index of column to use for keeping unique entries (default is 0).
        combine_differing_entries (bool): Combine differing entries (with same info in first
            column) into one (default is False).

    Returns:
        list: A processed list with sorted and unique entries.
    """

    # Check if the input is a list of strings or a list of lists
    if not isinstance(input_list, list):
        try:
            raise ValueError("Input must be a list of strings or a list of lists.")
        except ValueError as e:
            logger.error(e)
            raise

    # Convert all entries to strings
    input_list = [
        [str(entry) for entry in sublist] if isinstance(sublist, list) else str(sublist)
        for sublist in input_list
    ]

    # Replace nan (also "#NV" for absence of species? ["nan", "#NV"])
    input_list = replace_substrings(
        input_list, ["nan", "#NV"], "", at_end=True, warning_no_string=True
    )

    # If input is a list of strings, return unique entries
    if all(isinstance(entry, str) for entry in input_list):
        return sorted(set(input_list))

    # If input is a list of lists, check for entries with same unique_entry_column value but differing other columns
    if all(isinstance(entry, list) for entry in input_list):
        # Replace tabs within strings (e.g. resulting from heterogeneous input format)
        input_list = replace_substrings(input_list, "\t", " ")

        # Collect all unique rows, rows with same entry in unique_entry_column assigned to same key
        unique_entries = defaultdict(list)

        for entry in input_list:
            unique_entries[entry[unique_entry_column]].append(entry)
    else:
        try:
            raise ValueError("Input list entries must be all strings or all lists.")
        except ValueError as e:
            logger.error(e)
            raise

    unique_entries = {key: unique_entries[key] for key in sorted(unique_entries)}
    processed_list = []

    for key, group in unique_entries.items():
        if len(group) == 1:
            # Only one entry with this key, keep it
            processed_list.append(group[0])
        else:
            # Check if all entries are identical
            first_entry = group[0]
            differing_entries = [entry for entry in group if entry != first_entry]

            if differing_entries:
                logger.warning(
                    f"Entries with the same unique column value '{key}' differ in other columns."
                )

                if combine_differing_entries:
                    # If there are differing entries, combine them into one entry
                    combined_entry = first_entry

                    for entry in differing_entries:
                        for index, item in enumerate(entry):
                            if item != combined_entry[index]:
                                combined_entry[index] = combine_info_strings(
                                    combined_entry[index], item
                                )

                    processed_list.append(combined_entry)
                    logger.info(f"Combining all unique entries for '{key}'.")
                else:
                    # If there are differing entries, keep all of them as separate entries
                    processed_list.append(first_entry)
                    processed_list.extend(differing_entries)
                    logger.info("Keeping all unique entries.")
            else:
                # logger.warning(
                #     f"{len(group)} entries with the same first column value '{key}' are identical. Keeping only one."
                # )
                processed_list.append(first_entry)

    return processed_list


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
    if deims_id in NON_DEIMS_LOCATIONS.keys():
        # Use non-DEIMS location coordinates if available
        location = NON_DEIMS_LOCATIONS[deims_id]
        logger.warning(
            f"Using non-DEIMS coordinates for ID '{deims_id}': Latitude: {location['lat']}, Longitude: {location['lon']}."
        )

        return location

    if deims_id != deims._normaliseDeimsID(deims_id):
        logger.error(
            f"Coordinates for DEIMS.iD '{deims_id}' not found (iD deviates from standard format)!"
        )
    else:
        try:
            deims_gdf = deims.getSiteCoordinates(deims_id, filename=None)
            # option: collect all coordinates from deims_gdf.boundary[0] ...
            # deims_gdf = deims.getSiteBoundaries(deims_id, file_name=None)

            lon = deims_gdf.geometry[0].x
            lat = deims_gdf.geometry[0].y
            name = deims_gdf.name[0]
            logger.info(
                f"Coordinates for DEIMS.iD '{deims_id}' found ({name}). "
                f"Latitude: {lat}, Longitude: {lon}"
            )
            return {
                "lat": lat,
                "lon": lon,
                "deims_id": deims_id,
                "found": True,
                "name": name,
            }
        except Exception as e:
            logger.error(f"Coordinates for DEIMS.iD '{deims_id}' not found ({e}).")

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
        try:
            raise FileNotFoundError(f"File '{xls_file}' not found.")
        except FileNotFoundError as e:
            logger.error(e)
            raise

    # Load Excel file into a DataFrame
    df = pd.read_excel(xls_file, header=header_row)

    # Filter by country code
    if not country == "ALL":
        df = df[df["Country"] == country]

        if df.empty:
            logger.warning(f"No entries found for country code '{country}'.")

    # Extract column containing list of DEIMS.iDs and return as list of dicts
    return df["DEIMS.ID"].tolist()


def get_plot_locations_from_csv(
    csv_file, *, header_row=0, sep=";", merge_same_locations=True
):
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
        try:
            raise FileNotFoundError(f"File '{csv_file}' not found.")
        except FileNotFoundError as e:
            logger.error(e)
            raise

    # Load CSV file into a DataFrame
    df = pd.read_csv(csv_file, header=header_row, encoding="ISO-8859-1", sep=sep)

    if df.empty:
        logger.warning(
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
                    logger.warning(
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

                if pd.isna(lat) or pd.isna(lon):
                    logger.warning(
                        f"Latitude and/or longitude 'nan' found for station code '{station_code}' "
                        f"and site code '{site_code}'. Skipping plot location row."
                    )
                    continue

                # deims_id check not reasonable, code in commits before 2025-07

                # Check if coordinates already exist in locations
                existing_location = find_existing_location(lat, lon)

                if merge_same_locations:
                    if existing_location:
                        if station_code not in existing_location["station_code"]:
                            existing_location["station_code"].append(station_code)
                        if site_code not in existing_location["site_code"]:
                            existing_location["site_code"].append(site_code)
                    else:
                        location = {
                            "lat": lat,
                            "lon": lon,
                            "station_code": [station_code],
                            "site_code": [site_code],
                        }

                        locations.append(location)
                else:
                    station_code = (
                        str(station_code).replace("/", "_").replace("?", "？")
                    )

                    if (
                        existing_location
                        and site_code != existing_location["site_code"]
                    ):
                        logger.error(
                            f"Site code '{site_code}' differs for equal coordinates "
                            f"({lat}, {lon}). Skipping entry."
                        )
                    elif (
                        existing_location is None
                        or station_code != existing_location["station_code"]
                    ):
                        # Add new location with just one (modified) station and site code
                        location = {
                            "lat": lat,
                            "lon": lon,
                            "station_code": station_code,
                            "site_code": site_code,
                        }
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
    logger.info("Parsing locations from input string ...")

    for item in locations_str.split(";"):
        if "," in item:
            try:
                lat, lon = map(float, item.split(","))
                locations.append({"lat": lat, "lon": lon})
                logger.info(f"Latitude: {lat}, Longitude: {lon}")

            except ValueError:
                try:
                    raise argparse.ArgumentTypeError(
                        f"Invalid coordinate input: {item}. Expected format is 'lat,lon'."
                    )
                except argparse.ArgumentTypeError as e:
                    logger.error(e)
                    raise
        else:
            location = get_deims_coordinates(item)

            if location["found"]:
                locations.append(location)
            else:
                try:
                    raise ValueError(f"Coordinates for DEIMS.id '{item}' not found.")
                except ValueError as e:
                    logger.error(e)
                    raise

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
        target_crs (crs or str): Target CRS (as CRS object or str).

    Returns:
        tuple (float): Reprojected coordinates (easting, northing).
    """
    # Define the source CRS (EPSG:4326 - WGS 84, commonly used for lat/lon)
    src_crs = "EPSG:4326"

    # Create a transformer to convert from the source CRS to the target CRS
    # (always_xy: use lon/lat for source CRS and east/north for target CRS)
    transformer = pyproj.Transformer.from_crs(src_crs, target_crs, always_xy=True)

    # Reproject the coordinates (order is lon, lat!)
    east, north = transformer.transform(lon, lat)

    return east, north


def set_no_data_value(tif_file, no_data_value):
    """
    Set the no_data value for a TIFF file, if it is provided and differs from the current value.
    Only modifies the file if needed.
    """
    if no_data_value is not None:
        no_data_value = float(no_data_value)

        with rasterio.open(tif_file, "r") as src:
            current_no_data = src.nodata

        if current_no_data is None or float(current_no_data) != no_data_value:
            with rasterio.open(tif_file, "r+") as src:
                src.nodata = no_data_value

            logger.info(
                f"Modified 'no data' value for raster file '{tif_file}' from {current_no_data} to {no_data_value}."
            )


def extract_raster_value(
    tif_file,
    location,
    *,
    band_number=1,
    attempts=5,
    delay=2,
    no_data_value=None,
    file_date_for_time_stamp=True,
):
    """
    Extract value from raster file at specified coordinates.

    Parameters:
        tif_file (str): TIF file path or URL.
        coordinates (dict): Dictionary with 'lat' and 'lon' keys ({'lat': float, 'lon': float}).
        band_number (int): Band number for which the value shall be extracted (default is 1).
        attempts (int): Number of attempts to open the TIF file in case of errors (default is 5).
        delay (int): Number of seconds to wait between attempts (default is 2).
        no_data_value (int or float): Value to set as no-data value in the raster file (default is None).
        file_date_for_time_stamp (bool): Use file date for the time stamp (default is True, if False file read time used).

    Returns:
        tuple: Extracted value (None if extraction failed), and time stamp.
    """
    is_url = str(tif_file).startswith("http") or str(tif_file).startswith("/vsicurl")

    if not is_url:
        set_no_data_value(tif_file, no_data_value)

    while attempts > 0:
        time_stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

        try:
            with rasterio.open(tif_file, "r") as src:
                # Check if band number exists in the raster file
                if band_number not in src.indexes:
                    try:
                        raise ValueError(
                            f"Band number {band_number} does not exist in the raster file {tif_file}."
                        )
                    except ValueError as e:
                        logger.error(e)
                        raise

                # Reproject coordinates to target CRS
                east, north = reproject_coordinates(
                    location["lat"],
                    location["lon"],
                    src.crs,  # TIF file CRS
                )

                # Extract value from specified band number at specified coordinates
                value = next(src.sample([(east, north)], indexes=band_number))[0]

                # # testing
                # print("Original coordinates:", location["lat"], location["lon"])
                # print("Projected coordinates:", east, north)
                # print("Raster bounds:", src.bounds)
                # row, col = src.index(east, north)
                # print("Pixel indices:", row, col)
                # print("Raster value via indices:", src.read(band_number)[row, col])
                # print("Raster value via sample:", value)

                if file_date_for_time_stamp:
                    if is_url:
                        logger.warning(
                            "Cannot access file modification time for URL. Using file reading time instead."
                        )
                    else:
                        time_stamp = datetime.fromtimestamp(
                            tif_file.stat().st_mtime,
                            tz=timezone.utc,
                        ).isoformat(timespec="seconds")

                    # Code for trying to use tifftag_datetime in commits before 2025-08-12 (but tag never found)

            return value, time_stamp
        except rasterio.errors.RasterioIOError as e:
            attempts -= 1
            logger.error(f"Reading TIF file failed ({e}).")

            if attempts > 0:
                logger.info(f"Retrying in {delay} seconds ...")
                time.sleep(delay)
            else:
                return None, time_stamp


def check_url(url, *, attempts=5, delay_exponential=2, delay_linear=2):
    """
    Check if a file exists at specified URL and retrieve its content type.

    Parameters:
        url (str): URL to check.
        attempts (int): Number of attempts in case of connection errors or specific status codes (default is 5).
        delay_exponential (int): Initial delay in seconds for request rate limit errors (default is 2).
        delay_linear (int): Delay in seconds for gateway errors and other failed requests (default is 2).

    Returns:
        str: URL if existing (original or redirected), None otherwise.
    """
    if not url:
        return None

    status_codes_rate = {429}  # codes for retry with exponentially increasing delay
    status_codes_gateway = {502, 503, 504}  # codes for retry with fixed time delay

    while attempts > 0:
        attempts -= 1

        try:
            response = requests.head(url, allow_redirects=True)

            if response.status_code == 200:
                return response.url
            elif response.status_code in status_codes_rate:
                logger.error(
                    f"Request rate limited (Status code {response.status_code})."
                )

                if attempts > 0:
                    logger.info(f"Retrying in {delay_exponential} seconds ...")
                    time.sleep(delay_exponential)
                    delay_exponential *= 2
            elif response.status_code in status_codes_gateway:
                logger.error(f"Request failed (Status code {response.status_code}).")

                if attempts > 0:
                    logger.info(f"Retrying in {delay_linear} seconds ...")
                    time.sleep(delay_linear)

            else:
                logger.error(
                    f"Invalid URL: {url} (Status code {response.status_code})."
                )
                return None
        except requests.ConnectionError as e:
            logger.error(f"Request failed ({e}).")

            if attempts > 0:
                logger.info(f"Retrying in {delay_linear} seconds ...")
                time.sleep(delay_linear)

    return None


def download_file_opendap(
    file_name,
    opendap_folder,
    target_folder,
    *,
    new_file_name=None,
    attempts=5,
    delay=2,
    warn_not_found=True,
):
    """
    Download a file from OPeNDAP server 'grasslands-pdt'.

    Parameters:
        file_name (str): Name of file to download.
        opendap_folder (str): Folder where file is expected on OPeNDAP server.
        target_folder (str): Local folder where file will be saved.
        new_file_name (str): New name for downloaded file (default is None, file_name will be used).
        attempts (int): Number of attempts to download the file (default is 5).
        delay (int): Number of seconds to wait between attempts (default is 2).
        warn_not_found (bool): Warn if file not found on OPeNDAP server (default is True).

    Returns:
        None
    """
    url = f"{OPENDAP_ROOT}{opendap_folder}/{file_name}"
    logger.info(f"Trying to download '{url}' ...")

    while attempts > 0:
        try:
            response = requests.get(url)

            # # Variant with authentication using OPeNDAP credentials from .env file.
            # dotenv_config = dotenv_values(".env")
            # session = requests.Session()
            # session.auth = (dotenv_config["opendap_user"], dotenv_config["opendap_pw"])
            # response = session.get(url)

            if response.status_code == 200:
                if not new_file_name:
                    new_file_name = file_name

                target_file = target_folder / new_file_name
                Path(target_file).parent.mkdir(parents=True, exist_ok=True)

                with open(target_file, "wb") as file:
                    file.write(response.content)

                logger.info(f"File downloaded successfully to '{target_file}'.")
                return
            elif response.status_code == 404:
                if warn_not_found:
                    logger.warning(f"File '{file_name}' not found on OPeNDAP server.")
                else:
                    logger.info(f"File '{file_name}' not found on OPeNDAP server.")
                return
            else:
                attempts -= 1

                if attempts > 0:
                    time.sleep(delay)
        except requests.ConnectionError:
            attempts -= 1

            if attempts > 0:
                time.sleep(delay)

    logger.warning(f"File '{file_name}' download failed repeatedly.")


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
    if (not leap_year_considered) and calendar.isleap(year) and (day_of_year > 59):
        delta_days = day_of_year
    else:
        delta_days = day_of_year - 1

    return datetime(year, 1, 1) + timedelta(days=delta_days)


def get_legend_from_file(map_specs, *, cache=None):
    """
    Get legend file for land cover map and create a mapping of category indices to category names.

    Parameters:
        map_specs (dict): Dictionary containing map specifications.
        cache (Path): Path for local map directory (default is None).

    Returns:
        dict: A mapping of category indices to category names.
    """
    file_name = f"{map_specs['file_stem']}{map_specs['leg_ext']}"

    # Try local file first
    if cache is not None:
        leg_file = Path(cache) / map_specs["subfolder"] / file_name

        if leg_file.is_file():
            logger.info(f"Land cover categories found. Using '{leg_file}'.")
            category_mapping = create_category_mapping(leg_file)

            return category_mapping
        else:
            logger.info(f"Land cover categories file '{leg_file}' not found.")

    # Try URL
    leg_file = (
        f"{OPENDAP_ROOT}{map_specs['folder']}/{map_specs['subfolder']}/{file_name}"
    )

    if check_url(leg_file):
        logger.info(f"Land cover categories found. Using '{leg_file}'.")
        category_mapping = create_category_mapping(leg_file)

        return category_mapping
    else:
        try:
            raise FileNotFoundError(
                f"Land cover categories file '{leg_file}' not found."
            )
        except FileNotFoundError as e:
            logger.error(e)
            raise


def create_category_mapping(leg_file):
    """
    Create a mapping of category indices to category names from legend file (XML or XLSX or ...).

    Parameters:
        leg_file (Path or URL): Path or URL to the leg file containing category names (in specific format).

    Returns:
        dict: A mapping of category indices to category names.
    """
    category_mapping = {}

    # Get file type (without dot)
    if isinstance(leg_file, Path):
        leg_file_suffix = leg_file.suffix[1:]
    elif isinstance(leg_file, str):
        leg_file_suffix = leg_file.split(".")[-1]

    if leg_file_suffix in ["xlsx", "xls"]:
        try:
            df = pd.read_excel(leg_file)

            # Assuming category elements are listed in the first two columns (index and name)
            category_mapping = {row[0]: row[1] for row in df.values}
            # # Alternative using the row names 'code' and 'class_name'
            # category_mapping = (df[["code", "class_name"]].set_index("code")["class_name"].to_dict())
        except Exception as e:
            logger.error(f"Reading XLSX file failed ({str(e)}).")
    elif leg_file_suffix == "xml":
        # Not implemented for URL, only local files
        try:
            tree = ET.parse(leg_file)
            root = tree.getroot()

            # Find CategoryNames (as in Preidl map legend)
            category_names = root.find(".//CategoryNames")

            if category_names is not None:
                for index, category in enumerate(category_names):
                    category_name = category.text
                    category_mapping[index] = category_name
            else:
                # Find GDALRasterAttributeTable (as in hda grassland data format)
                rat = root.find(".//GDALRasterAttributeTable")

                if rat is not None:
                    for row in rat.findall("Row"):
                        fields = row.findall("F")

                        if len(fields) >= 3:
                            value = int(fields[0].text)  # value in first row
                            class_name = fields[2].text  # class name in third row
                            category_mapping[value] = class_name
        except Exception as e:
            logger.error(f"Reading XML file failed ({str(e)}).")

    return category_mapping
