"""
Module Name: utils.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: December 11, 2023
Description: Utility functions for uc-grassland building block. 
"""

from pathlib import Path
import pandas as pd
import csv
from collections import Counter


def add_string_to_file_name(file_name, string_to_add):
    """
    Add a string before the suffix of a file name.

    Parameters:
    - file_name (Path): The path of the file.
    - string_to_add (str): The string to add before the suffix.

    Returns:
    - new_file_name (Path): The new file path with the added string.
    """
    # Convert the WindowsPath object to a string
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

    # Nested functions for either replacing substring at the end or everywhere.
    def replace_substring_at_end(original_string, substring_to_replace):
        return (
            original_string[: -len(substring_to_replace)] + replacement_string
            if original_string.endswith(substring_to_replace)
            else original_string
        )

    def replace_substring(original_string, substring_to_replace):
        return original_string.replace(substring_to_replace, replacement_string)

    # Convert single strings to lists for unified handling.
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

    # Return only string if input data was just a string, list of strings otherwise.
    return modified_list[0] if len(modified_list) == 1 else modified_list


def count_duplicates(lst):
    """
    Count occurrences of duplicate items in a list.

    Parameters:
    - lst (list): The list to analyze.

    Returns:
    - dict: A dictionary where keys are duplicate items and values are their counts.
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
        # row_values = [key] + list(values.values())
        row_values = [key, f"'{values}'"]
    else:
        row_values = [key, values]

    return row_values


def species_dict_to_file(species_dict, column_names, file_name):
    """
    Write a dictionary to a text file (tab-separated) or an Excel file.

    Parameters:
    - species_dict (dict): Dictionary to be written to the file.
    - column_names (list): List of all column names (strings, includes first column for species_dict keys).
    - file_name (str or Path): The path of the output file.
    """
    file_path = Path(file_name)
    file_suffix = file_path.suffix.lower()

    if file_suffix == ".txt":
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter="\t")
            header = column_names
            writer.writerow(header)  # Header row

            for spec, values in species_dict.items():
                writer.writerow(get_row_values(spec, values))

    elif file_suffix == ".xlsx":
        df = pd.DataFrame(columns=column_names)
        for spec, values in species_dict.items():
            df = pd.concat(
                [
                    df,
                    pd.DataFrame([get_row_values(spec, values)], columns=column_names),
                ],
                ignore_index=True,
            )

        df.to_excel(file_path, index=False)
    else:
        print(
            f"Error: Unsupported file format. Supported formats are '.txt' and '.xlsx'."
        )

    print(f"Species dictionary written to file '{file_name}'.")
