"""
Module Name: assign_pfts.py
Author: Thomas Banitz, Franziska Taubert, BioDT
Date: December 17, 2023
Description: Assign PFTs to species with the following options:
             - based on TRY categorical traits table
             - based on TRY categorical traits table with species names corrected or
               replaced by synonym names based on GBIF taxonomic backbone
             - based on GBIF taxonomic backbone for family and https://github.com/traitecoevo/growthform
               table (Zanne et al.) for woodiness   
"""

from pathlib import Path
import utils as ut
import pandas as pd
import csv
from pygbif import species


def resolve_pfts(spec, pft_1, pft_2):
    """
    Resolve conflicting PFT entries for a species.

    Parameters:
    - spec (str): Species for which PFTs are being resolved.
    - pft_1 (str): First PFT entry.
    - pft_2 (str): Second PFT entry.

    Returns:
    - str: Resolved PFT entry.

    Raises:
    - ValueError: If different assigned grassland PFTs were found for the same species.
    """

    # Warning for duplicate species
    print(f"Warning: Duplicate species entry found for species: {spec}")

    # Check if the PFTs are the same, no need to change the dictionary
    if pft_1 == pft_2:
        pft_resolved = pft_1
        print(f"         PFTs are equal. Keeping the PFT '{pft_resolved}'.")
    # Check if PFTs start with "not assigned", keep other one in dictionary
    else:
        if pft_1.startswith("not assigned") and not pft_2.startswith("not assigned"):
            pft_resolved = pft_2
        elif not pft_1.startswith("not assigned") and pft_2.startswith("not assigned"):
            pft_resolved = pft_1
        elif pft_1.startswith("not assigned") and pft_2.startswith("not assigned"):
            pft_resolved = "not assigned (varying)"
        # Raise an error for two different assigned PFTs
        else:
            raise ValueError(
                f"Different assigned PFTs found for species {spec}: '{pft_1}' vs. '{pft_2}'."
            )
        print(
            f"         PFTs differ: '{pft_1}' vs. '{pft_2}'. Keeping the PFT '{pft_resolved}'."
        )

    return pft_resolved


def read_species_pft_dict(
    file_name, species_column=0, pft_column=1, header_lines=1, save_new_file=False
):
    """
    Read a dictionary from a text file containing species and plant functional types (PFTs).

    Parameters:
    - file_name (str): Path to the text file.
    - species_column(int): Species column number (0-based index, default is 0).
    - pft_column (int): PFT column number (0-based index, default is 1).
    - header_lines (int): Number of header lines to skip (default is 1).
    - save_new_file (bool): If true, save result dictionary to new file (default is False).

    Returns:
    - dict: Dictionary where species names are keys, and PFTs are values.
    """
    # TODO: optional: read also from xlsx files

    # Set valid PFT entries for error checking.
    valid_pfts = ["forb", "grass", "legume"]

    print(f"Reading species-PFT lookup table from '.\{file_name}' ...")

    # Open the file for reading
    with open(file_name, "r") as file:
        species_pft_dict = {}
        processed_lines = 0

        # Skip header lines
        for _ in range(header_lines):
            next(file)

        # Split each line into columns (tab as delimiter), get species and PFT from columns
        for line_number, line in enumerate(file, start=header_lines + 1):
            columns = line.strip().split("\t")
            spec, pft = (columns[species_column], columns[pft_column])

            # Warning if PFT is not valid or starts with "not assigned"
            if pft not in valid_pfts and not pft.startswith("not assigned"):
                print(
                    f"Warning: Invalid PFT found on line {line_number} for {spec}: '{pft}'."
                )

            # Check if (replaced) species name is already in lookup table
            if spec in species_pft_dict:
                # Check PFT for existing species
                species_pft_dict[spec] = resolve_pfts(spec, pft, species_pft_dict[spec])
            else:
                # Add new species and PFT to lookup table
                species_pft_dict[spec] = pft

            processed_lines += 1

    print(f"Processed {processed_lines} lines.")
    print(f"Final species-PFT lookup table has {len(species_pft_dict)} entries.")

    # Save created dictionary to new file
    if save_new_file:
        file_name = ut.add_string_to_file_name(file_name, "__UserDictionary")
        ut.species_dict_to_file(species_pft_dict, ["Species", "PFT"], file_name)

    # Return resulting dictionary
    return species_pft_dict


def get_gbif_species(spec):
    """
    Retrieve a species name from the GBIF taxonomic backbone.

    Parameters:
    - spec (str): Species name to look up in the GBIF taxonomic backbone.

    Returns:
    - str: Matched or suggested species name from GBIF, or the original species name if no match is found.
    """

    spec_gbif_dict = species.name_backbone(name=spec, kingdom="plants")
    # Option: try with strict first?: If true it (fuzzy) matches only the given name, but never a taxon in the upper classification

    if spec_gbif_dict["matchType"] == "NONE":
        # No match, return input species
        print(f"Warning: '{spec}' not found.")
        return spec
    elif spec_gbif_dict["rank"] == "SPECIES":
        # Use 'species' entry
        spec_match = spec_gbif_dict["species"]
        if spec_match != spec:
            print(f"Hint: '{spec}' replaced with GBIF NAME '{spec_match}'.")
    elif "canonicalName" in spec_gbif_dict:
        # No exact match, use 'canonicalName' entry
        spec_match = spec_gbif_dict["canonicalName"]

        if spec_match != spec:
            print(f"Warning: '{spec}' not exactly identified by GBIF.")

            if spec_gbif_dict["rank"] == "GENUS":
                # GBIF result is only GENUS, keep this result
                print(f"         '{spec}' replaced with GBIF GENUS '{spec_match}'.")
            else:
                # Check for GBIF suggestions
                spec_gbif_suggest = species.name_suggest(q=spec, rank="species")

                if len(spec_gbif_suggest) > 0:
                    # Suggestions found, use first suggestion
                    spec_gbif_suggest = [sgs["species"] for sgs in spec_gbif_suggest]
                    print(f"         Candidate species: {spec_gbif_suggest}")
                    spec_match = spec_gbif_suggest[0]
                    print(
                        f"         '{spec}' replaced with GBIF suggestion '{spec_match}'."
                    )
                else:
                    # No suggestions, return input species (matches above rank GENUS do not help for PFT mapping)
                    print(
                        f"         No replacement (GBIF match was {spec_gbif_dict['rank']} '{spec_match}')."
                    )
                    return spec
    else:
        print(
            f"surprise: neither 'species' nor 'canonicalName' in result, match type {spec_gbif_dict['matchType']}"
        )

    return spec_match


def get_gbif_dict(species_pft_dict, save_new_file=False):
    """
    Screen and correct species-PFT lookup table with GBIF taxonomic backbone.

    Parameters:
    - species_pft_dict (dict): Dictionary where species names are keys, and PFTs are values.
    - save_new_file (bool): If true, save result dictionary to new file (default is False).

    Returns:
    - dict: Processed dictionary where species names are keys, and values are dictionaries with keys:
        - 'pft': PFT.
        - 'originalNames': List of species names from input dictionary (that were replaced or not).
    """

    print(f"Searching for species in GBIF taxonomic backbone ...")
    species_pft_dict_gbif = {}
    processed_lines = 0

    for spec, pft in species_pft_dict.items():
        spec_match = get_gbif_species(spec)

        # Check if (replaced) species name is already in lookup table
        if spec_match in species_pft_dict_gbif:
            # Check PFT for existing species
            species_pft_dict_gbif[spec_match]["pft"] = resolve_pfts(
                spec_match, pft, species_pft_dict_gbif[spec_match]["pft"]
            )
            # Add replaced species name to list of original names
            species_pft_dict_gbif[spec_match]["originalNames"].append(spec)
        else:
            # Add new species, PFT and replaced species name to lookup table
            species_pft_dict_gbif[spec_match] = {"pft": pft, "originalNames": [spec]}

        processed_lines += 1

    print(f"Processed {processed_lines} lines.")
    print(f"Final species-PFT lookup table has {len(species_pft_dict_gbif)} entries.")

    # Save created dictionary to new file
    if save_new_file:
        file_name = ut.add_string_to_file_name(file_name, "__GBIFDictionary")
        ut.species_dict_to_file(
            species_pft_dict, ["Species", "PFT", "Original names"], file_name
        )

    # Return resulting dictionary
    return species_pft_dict_gbif


def read_species_list(file_name, species_column, header_lines=1, check_gbif=True):
    """
    Read species names from a file.

    Parameters:
    - file_name (str): Name of the file.
    - species_column (str or int): Species column name or number (0-based index).
    - header_lines (int): Number of header line, lines before will be skipped (default is 1).
    - check_gbif (bool): If True, check/correct species name with GBIF taxonomic backbone (default is True).

    Returns:
    - species_list (list): List of species names.
    """
    # Convert file_path to a Path object if it is not already
    file_name = Path(file_name)
    file_extension = file_name.suffix.lower()
    print(f"Reading species list from '{file_name}' ...")

    if file_extension == ".xlsx":
        # Read from Excel file
        try:
            df = pd.read_excel(file_name, header=header_lines - 1)
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return []

        # Determine column index
        if isinstance(species_column, str):
            try:
                column_index = df.columns.get_loc(species_column)
            except KeyError:
                print(f"Error: Column '{species_column}' not found in the Excel file.")
                return []
        elif isinstance(species_column, int):
            column_index = species_column
        else:
            print(
                "Error: Invalid column identifier. Please provide a column name (str) or column number (int)."
            )
            return []

        # Extract species names from the specified column, convert to string and replace 'nan' by empty string
        species_list = df.iloc[:, column_index].tolist()
        species_list = [str(spec) for spec in species_list]
        species_list = ut.replace_substrings(species_list, "nan", "")

    elif file_extension == ".txt":
        # Read from tab-separated text file
        try:
            with open(file_name, "r") as file:
                species_data = [line.strip().split("\t") for line in file]

        except Exception as e:
            print(f"Error reading text file: {e}")
            return []

        # Determine column index
        if isinstance(species_column, str):
            if species_column in species_data[header_lines - 1]:
                column_index = species_data[header_lines - 1].index(species_column)
            else:
                print(
                    f"Error: Column '{species_column}' not found in the specified header line of the text file."
                )
                return []
        elif isinstance(species_column, int):
            column_index = species_column
        else:
            print(
                "Error: Invalid column identifier. Please provide a column name (str) or column number (int)."
            )
            return []

        species_list = [line[column_index] for line in species_data[header_lines:]]

    else:
        print(
            f"Error: Unsupported file format. Supported formats are 'xlsx' and 'txt'."
        )
        return []

    # GBIF check and correction if selected
    if check_gbif:
        for index, spec in enumerate(species_list):
            species_list[index] = get_gbif_species(spec)

    # No removal of 'nan' or double species, so that assigned PFTs can be matched with original list later
    empty_strings = species_list.count("")
    print(
        f"Species list has {len(species_list)} entries, including {empty_strings} empty entries."
    )
    duplicates = ut.count_duplicates(species_list)
    if len(duplicates) > 0:
        print("Duplicates: ", end="")
        print(", ".join([f"'{spec}' ({count})" for spec, count in duplicates.items()]))

    return species_list


def user_input_pfts(species_pft_dict, start_string):
    """
    Iterate through species without PFT assigned and prompt user to select a new PFT.

    Parameters:
    - species_pft_dict (dict): Dictionary with species names as keys and corresponding PFTs.
    - start_string (string): Beginning of PFTs that get suggested for reassignment.

    Returns:
    - dict: Modified dictionary with updated PFTs based on user input.
    """

    print(f"Going through species {start_string} ...")
    print("You can select the new PFT from the following options:")
    print("1. 'grass'")
    print("2. 'forb'")
    print("3. 'legume'")
    print("4. 'not assigned'")
    print("5. Skip (leave PFT as is). ")
    print("6. Exit PFT assignment.")

    for spec, pft in species_pft_dict.items():
        if pft.startswith(start_string) and isinstance(spec, str):
            print(f"Species: {spec}. Current PFT: '{pft}'.")
            user_choice = input(
                "Enter your choice (1 'grass' 2 'forb' 3 'legume' 4 'not assigned' 5 Skip 6 Exit): "
            )

            if user_choice == "1":
                species_pft_dict[spec] = "grass (user input)"
            elif user_choice == "2":
                species_pft_dict[spec] = "forb (user input)"
            elif user_choice == "3":
                species_pft_dict[spec] = "legume (user input)"
            elif user_choice == "4":
                species_pft_dict[spec] = "not assigned (user input)"
            elif user_choice == "5":
                pass  # Leave as is, no change needed
            elif user_choice == "6":
                print(f"Exiting the manual PFT assignment for species {start_string}.")
                break  # Exit the loop
            else:
                print("Invalid choice. Leaving PFT as is.")

    return species_pft_dict


def get_species_pfts(species_list, species_pft_dict, file_name):
    """
    Create a dictionary with species and corresponding PFTs from a species-PFT lookup table,
    and save to file.

    Parameters:
    - species_list (list): List of species names.
    - species_pft_dict (dict): Dictionary with species names as keys and corresponding PFTs.
    - file_name (str): Name of the file for saving the new dictionary.

    Returns:
    - dict: Dictionary with species names as keys and corresponding PFTs.
    """
    print(f"Searching for species from species list in species-PFT lookup table ...")
    species_pfts_assigned = {}

    for spec in species_list:
        if spec in species_pft_dict:
            pft = species_pft_dict[spec]
        else:
            pft = "not found"

        species_pfts_assigned[spec] = pft

    # Ask user if species not found or not assigned shall be modified manually?
    for unclear_pft_string in ["not found", "not assigned"]:
        count_unclear = sum(
            isinstance(spec, str) and pft.startswith(unclear_pft_string)
            for spec, pft in species_pfts_assigned.items()
        )
        if count_unclear:
            print(f"Species {unclear_pft_string}: {count_unclear}.")
            manual_input = input(
                f"Do you want to make manual inputs for these species? (y/n): "
            ).lower()

            if manual_input == "y":
                species_pfts_assigned = user_input_pfts(
                    species_pfts_assigned, unclear_pft_string
                )

    # Save created dictionary to specified file
    ut.species_dict_to_file(species_pfts_assigned, ["Species name", "PFT"], file_name)

    return species_pfts_assigned


# Example usage:

# Get dictionary from lookup table, and store to file (once created, this file can also be used to get the dictionary)
folder = Path("speciesMappingLookupTable")
file_name = folder / "TRY_Categorical_Traits__Grassmind_PFTs.txt"
species_pft_dict = read_species_pft_dict(file_name, save_new_file=True)

# # Check dictionary against GBIF taxonomic backbone, and store to file (once created, this file can also be used to get the dictionary)
# species_pft_dict_gbif = get_gbif_dict(species_pft_dict, save_new_file=True)

# Get example list, here from GCEF site
folder = Path("speciesMappingExampleLists")
file_name = folder / "102ae489-04e3-481d-97df-45905837dc1a_Species.xlsx"
# file_name = folder / "102ae489-04e3-481d-97df-45905837dc1a_Species.txt"
species_column = "Name"  # 1
species_list = read_species_list(file_name, species_column)

# Find PFTs (optional user modifications) and write to file
file_name = ut.add_string_to_file_name(file_name, "__TRYmapping")
species_pfts_assigned = get_species_pfts(species_list, species_pft_dict, file_name)
# species_pfts_assigned = get_species_pfts(species_list, species_pft_dict_gbif)
