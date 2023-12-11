"""
Module Name: utils.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: December 11, 2023
Description: Utility functions for uc-grassland building block. 
"""

from pathlib import Path


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


def replace_substring(input_data, substring_to_replace, replacement_string):
    """
    Replace a substring with another string in a single string or a list of strings.

    Parameters:
    - input_data (str or list): String or list of strings.
    - substring_to_replace (str): Substring to be replaced.
    - replacement_string (str): New string to replace the specified substring.

    Returns:
    - str or list: Modified string or list of strings (same as format input_data
    """
    if isinstance(input_data, str):
        return input_data.replace(substring_to_replace, replacement_string)
    elif isinstance(input_data, list):
        return [
            original_string.replace(substring_to_replace, replacement_string)
            if isinstance(original_string, str)
            else original_string
            for original_string in input_data
        ]
    else:
        raise ValueError("Input data must be a string or a list of strings.")


def replace_substrings(
    input_data, substrings_to_replace, replacement_string, at_end=False
):
    """
    Replace specified substrings with another string in a single string or a list of strings.

    Parameters:
    - input_data (str or list): String or list of strings.
    - substrings_to_replace (str or list): Substring or list of substrings to be replaced.
    - replacement_string (str): New string to replace the specified substring(s).
    - at_end (bool): Replace the substring(s) only if appearing at the end of each string (default is False).

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
            else:
                # Warning for non string element in list.
                print(
                    f"Warning: {modified_string} is not a string. No replacements performed."
                )
            modified_list.append(modified_string)
    else:
        raise ValueError("Input data must be a string or a list of strings.")

    # Return only string if input data was just a string, list of strings otherwise.
    return modified_list[0] if len(modified_list) == 1 else modified_list
