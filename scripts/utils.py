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
