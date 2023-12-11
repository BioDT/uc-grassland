"""
Module Name: assign_pfts.py
Author: Thomas Banitz, Franziska Taubert, BioDT
Date: December 8, 2023
Description: Assign PFTs to species based on TRY categorical traits table. 
"""

from pathlib import Path
import utils as ut
import pandas as pd
import csv


# Set undetermined epithet entries for replacing.
undetermined_epithets = [
    "sp.",
    "x",
    "varia",
    "varium",
    "varius",
    "variana",
    "varians",
    "variabile",
    "variabilis",
]


def create_species_pft_dict(
    file_name, pft_column=2, genus_column=3, epithet_column=4, header_lines=1
):
    """
    Create a dictionary from a text file containing species and plant functional types (PFTs).

    Parameters:
    - file_name (str): Path to the text file.
    - pft_column (int): PFT column number (default is 2).
    - genus_column (int): Species column number (default is 3).
    - epithet_column (int): Epithet column number (default is 4).
    - header_lines (int): Number of header lines to skip (default is 1).

    Returns:
    - dict: Dictionary where species names are keys, and PFTs are values.
    """
    # Set valid PFT entries for error checking.
    valid_pfts = ["forb", "grass", "legume"]

    # Open the file for reading
    with open(file_name, "r") as file:
        # Initialize an empty dictionary
        species_pft_dict = {}
        processed_lines = 0

        # Skip header lines
        for _ in range(header_lines):
            next(file)

        # Iterate over each line in the file
        for line_number, line in enumerate(file, start=header_lines + 1):
            # Split the line into columns using tab as delimiter
            columns = line.strip().split("\t")
            # Use species and PFT columns as key and value
            value, genus, epithet = (
                columns[pft_column - 1],
                columns[genus_column - 1],
                columns[epithet_column - 1],
            )

            # Replace undetermined epithets
            if epithet in undetermined_epithets:
                print(f"Hint: '{genus} {epithet}' replaced with '{genus} species'.")
                epithet = "species"

            # Compose species name
            key = f"{genus} {epithet}"

            # Warning if PFT is not valid or starts with "not assigned"
            if value not in valid_pfts and not value.startswith("not assigned"):
                print(
                    f"Warning: Invalid PFT found on line {line_number} for {key}: '{value}'."
                )

            if key in species_pft_dict:
                # Warning for duplicate species key
                print(
                    f"Warning: Duplicate species entry found on line {line_number}: {key}"
                )

                # Check if the values are the same, no need to change the dictionary
                if species_pft_dict[key] == value:
                    print(f"         PFTs are equal. Keeping the PFT: '{value}'.")
                else:
                    # Check if one but not both values start with "not assigned"
                    if species_pft_dict[key].startswith(
                        "not assigned"
                    ) and not value.startswith("not assigned"):
                        # Keep the new value in the dictionary
                        species_pft_dict[key] = value
                        print(
                            f"         PFTs differ: '{species_pft_dict[key]}' vs. '{value}'. Keeping the PFT: '{value}'."
                        )
                    elif not species_pft_dict[key].startswith(
                        "not assigned"
                    ) and value.startswith("not assigned"):
                        # Keep the existing value in the dictionary
                        print(
                            f"         PFTs differ: '{species_pft_dict[key]}' vs. '{value}'. Keeping the PFT: '{species_pft_dict[key]}'."
                        )
                    elif species_pft_dict[key].startswith(
                        "not assigned"
                    ) and value.startswith("not assigned"):
                        # Both start with "not assigned", use "not assigned (varying)" in the dictionary
                        print(
                            f"         PFTs differ: '{species_pft_dict[key]}' vs. '{value}'. Keeping the PFT: 'not assigned (varying)'."
                        )
                        species_pft_dict[key] = "not assigned (varying)"
                    else:
                        # Raise an error for other cases of different values
                        raise ValueError(
                            f"Error: Different PFTs found for species {key}: '{species_pft_dict[key]}' vs. '{value}'."
                        )
            else:
                # Add new species and PFT to the dict
                species_pft_dict[key] = value

            processed_lines += 1

    print(f"Processed {processed_lines} lines.")
    print(f"Final species dictionary has {len(species_pft_dict)} entries.")

    # Return the resulting dictionary
    return species_pft_dict


def read_species_list(file_name, column_identifier, header_lines=1):
    """
    Read species names from a file.

    Parameters:
    - file_name (str): The name of the file.
    - column_identifier (str or int): Column name or column number (0-based index).
    - header_lines (int): Number of header line, lines before will be skipped (default is 1).

    Returns:
    - species_list (list): List of species names.
    """
    # Convert file_path to a Path object if it is not already
    file_name = Path(file_name)
    file_extension = file_name.suffix.lower()

    if file_extension == ".xlsx":
        # Read from Excel file
        try:
            df = pd.read_excel(file_name, header=header_lines - 1)
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return []

        # Determine column index
        if isinstance(column_identifier, str):
            try:
                column_index = df.columns.get_loc(column_identifier)
            except KeyError:
                print(
                    f"Error: Column '{column_identifier}' not found in the Excel file."
                )
                return []
        elif isinstance(column_identifier, int):
            column_index = column_identifier
        else:
            print(
                "Error: Invalid column identifier. Please provide a column name (str) or column number (int)."
            )
            return []

        # Extract species names from the specified column
        species_list = df.iloc[:, column_index].tolist()

    elif file_extension == ".txt":
        # Read from tab-separated text file
        try:
            with open(file_name, "r") as file:
                # # Skip header lines
                # for _ in range(header_lines):
                #     next(file)

                # Read data into species_data
                species_data = [line.strip().split("\t") for line in file]

        except Exception as e:
            print(f"Error reading text file: {e}")
            return []

        # Continue with the specific case handling
        if isinstance(column_identifier, str):
            # Case where column_identifier is a string
            if column_identifier in species_data[header_lines - 1]:
                column_index = species_data[header_lines - 1].index(column_identifier)
                # species_list = [line[column_index] for line in species_data[1:]]
            else:
                print(
                    f"Error: Column '{column_identifier}' not found in the specified header line of the text file."
                )
                return []
        elif isinstance(column_identifier, int):
            # Case where column_identifier is an integer
            column_index = column_identifier
            # species_list = [line[column_index] for line in species_data]
        else:
            print(
                "Error: In the case of a tab-separated text file, column_identifier must be a string or an integer."
            )
            return []

        species_list = [line[column_index] for line in species_data[header_lines:]]

    else:
        print(
            f"Error: Unsupported file format. Supported formats are 'xlsx' and 'txt'."
        )
        return []

    # Remove middle 'x' in species name
    species_list = ut.replace_substrings(species_list, " x ", " ")

    # Replace substrings for unspecified SpeciesEpiphet (strings to be replaced need to be at end of species name)
    substrings_to_replace = [" " + s for s in undetermined_epithets]
    species_list = ut.replace_substrings(
        species_list, substrings_to_replace, " species", True
    )

    return species_list


def get_species_pfts(species_list, species_pft_dict):
    """
    Create a list with species and corresponding PFTs from a dictionary.

    Parameters:
    - species_list (list): List of species names.
    - species_pft_dict (dict): Dictionary with species names as keys and corresponding PFTs.

    Returns:
    - species_pft_list (list of tuples): List of tuples with species and corresponding PFTs.
    """
    species_pft_list = []

    for species in species_list:
        if species in species_pft_dict:
            value = species_pft_dict[species]
        else:
            value = "not found"

        species_pft_list.append((species, value))

    return species_pft_list


def species_pfts_to_file(species_pft_list, file_name):
    """
    Write a list of tuples with species and PFTs to a text file (tab-separated) or an Excel file.

    Parameters:
    - species_pft_list (list of tuples): List of tuples with species and corresponding PFTs.
    - file_name (str or Path): The path of the output file.
    """
    file_path = Path(file_name)
    file_suffix = file_path.suffix.lower()

    if file_suffix == ".txt":
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow(["Species name", "PFT"])  # Header row
            writer.writerows(species_pft_list)

    elif file_suffix == ".xlsx":
        df = pd.DataFrame(species_pft_list, columns=["Species name", "PFT"])
        df.to_excel(file_path, index=False)

    else:
        print(
            f"Error: Unsupported file format. Supported formats are '.txt' and '.xlsx'."
        )


# Example usage:

# Get dictionary
folder = "speciesMappingLookupTable"
folder = Path(folder)
file_name = "TRY_Categorical_Traits_Lookup_Table_2012_03_17__Grassmind_PFTs.txt"
file_name = folder / file_name

species_pft_dict = create_species_pft_dict(file_name)

# Get example list, here from GCEF site
folder = "D:/home/BioDT/_data/GCEF/Vegetation/"
folder = Path(folder)
file_name = "102ae489-04e3-481d-97df-45905837dc1a_Species.xlsx"
# file_name = "102ae489-04e3-481d-97df-45905837dc1a_Species.txt"
file_name = folder / file_name
column_identifier = "Name"  # 1

species_list = read_species_list(file_name, column_identifier)


# Find PFTs and write to file
species_pft_list = get_species_pfts(species_list, species_pft_dict)

file_name = ut.add_string_to_file_name(file_name, "__TRYmapping")
species_pfts_to_file(species_pft_list, file_name)
