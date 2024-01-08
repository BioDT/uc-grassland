"""
Module Name: assign_pfts.py
Author: Thomas Banitz, Franziska Taubert, BioDT
Date: December 17, 2023
Description: Assign PFTs to species with the following options:
             - based on TRY categorical traits table
             - based on TRY categorical traits table with species names corrected or
               replaced by synonym names based on GBIF taxonomic backbone
             - based on GBIF taxonomic backbone for family and https://github.com/traitecoevo/growthform
               table (Zanne et al.) for Woodiness   
"""

from pathlib import Path
import utils as ut
import pandas as pd
import csv
from pygbif import species


def resolve_species_infos(spec, info_name, info_1, info_2):
    """
    Resolve conflicting info entries for a species.

    Parameters:
    - spec (str): Species for which infos are being resolved.
    - info_name (str): Information name ('PFT' or 'Woodiness')
    - info_1 (str): First info entry.
    - info_2 (str): Second info entry.

    Returns:
    - str: Resolved info entry.
    """

    # Warning for duplicate species
    print(f"Warning: Duplicate species entry found for species '{spec}'.")

    # Check if the infos are the same, no need to change the dictionary
    if info_1 == info_2:
        info_resolved = info_1
        print(f"{info_name} is equal. Keeping the {info_name} '{info_resolved}'.")
    # Check if infos start with "not assigned", keep other one in dictionary
    else:
        if info_1.startswith("not assigned") and not info_2.startswith("not assigned"):
            info_resolved = info_2
        elif not info_1.startswith("not assigned") and info_2.startswith(
            "not assigned"
        ):
            info_resolved = info_1
        elif info_1.startswith("not assigned") and info_2.startswith("not assigned"):
            info_resolved = "not assigned"
        # Raise an error for two different assigned infos
        else:
            print(f"ERROR: Different assigned {info_name} found for species {spec}!")
            info_resolved = "conflicting"
        print(
            f"{info_name} differs: '{info_1}' vs. '{info_2}'. Keeping the {info_name} '{info_resolved}'."
        )

    return info_resolved


def get_valid_infos(info_name):
    """
    Get valid information entries based on the specified information type.

    Args:
        info_name (str): The type of species information ('PFT' or 'Woodiness').

    Returns:
        list: A list of valid information entries for the specified type.

    Raises:
        ValueError: If an unsupported species information type is provided.
    """
    if info_name == "PFT":
        # Set valid grassland PFT entries
        return ["grass", "forb", "legume"]
    elif info_name == "Woodiness":
        # Set valid Woodiness entries
        return ["woody", "herbaceous", "variable"]
    else:
        raise ValueError(
            f"ERROR: Unsupported species information type. Supported types are 'PFT' and 'Woodiness'."
        )


def read_species_info_dict(
    file_name,
    species_column=0,
    info_name="PFT",
    info_column=1,
    header_lines=1,
    save_new_file=False,
):
    """
    Read a dictionary from a text file containing species and a corresponding information (PFT or Woodiness).

    Parameters:
    - file_name (str): Path to the text file.
    - species_column(int): Species column number (0-based index, default is 0).
    - info_name (str): Information name ('PFT' or 'Woodiness', default is 'PFT')
    - info_column (int): Information column number (0-based index, default is 1).
    - header_lines (int): Number of header lines to skip (default is 1).
    - save_new_file (bool): If true, save result dictionary to new file (default is False).

    Returns:
    - dict: Dictionary where species names are keys, and infos are values.

    Raises:
    - ValueError: If unsupported species info_name is used.
    """
    valid_infos = get_valid_infos(info_name)
    print(f"Reading species-{info_name} lookup table from '.\{file_name}' ...")

    # Open the file for reading
    with open(file_name, "r") as file:
        species_info_dict = {}
        processed_lines = 0

        # Skip header lines
        for _ in range(header_lines):
            next(file)

        # Split each line into columns (tab as delimiter), get species and info from columns
        for line_number, line in enumerate(file, start=header_lines + 1):
            columns = line.strip().split("\t")
            spec, info = (columns[species_column], columns[info_column])

            if info_name == "Woodiness":
                info = ut.replace_substrings(info, "W", "woody")
                info = ut.replace_substrings(info, "H", "herbaceous")
                info = ut.replace_substrings(info, "NA", "not assigned")

            # Warning if info is not valid or starts with "not assigned"
            if info not in valid_infos and not info.startswith("not assigned"):
                print(
                    f"Warning: Invalid {info_name} found on line {line_number} for {spec}: '{info}'."
                )

            # Check if (replaced) species name is already in lookup table
            if spec in species_info_dict:
                # Check info for existing species
                species_info_dict[spec] = resolve_species_infos(
                    spec, info_name, info, species_info_dict[spec]
                )
            else:
                # Add new species and info to lookup table
                species_info_dict[spec] = info

            processed_lines += 1

    print(f"Processed {processed_lines} lines.")
    print(
        f"Final species-{info_name} lookup table has {len(species_info_dict)} entries."
    )

    # Save created dictionary to new file
    if save_new_file:
        file_name = ut.add_string_to_file_name(file_name, "__UserDictionary")
        ut.dict_to_file(species_info_dict, ["Species", info_name], file_name)

    # Return resulting dictionary
    return species_info_dict


def get_gbif_species(spec, accepted_ranks=["GENUS"]):
    """
    Retrieve a species name or higher rank from the GBIF taxonomic backbone.

    Parameters:
    - spec (str): Species name to look up in the GBIF taxonomic backbone.
    - accepted_ranks (list): List of taxonomic ranks above SPECIES that can be used as new species entry (default is ["GENUS"]).

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

        if "species" in spec_gbif_dict:
            spec_match = spec_gbif_dict["species"]
            if spec_match != spec:
                print(f"'{spec}' replaced with GBIF NAME '{spec_match}'.")
        else:
            spec_match = spec_gbif_dict["canonicalName"]
            print(f"Warning: '{spec}' not exactly identified by GBIF.")
            print(
                f"SURPRISE: Result rank is SPECIES, but no species entry. Using CANONICALNAME '{spec_match}'."
            )
            if spec_match != spec:
                print(f"'{spec}' replaced with GBIF CANONICALNAME '{spec_match}'.")

    elif "canonicalName" in spec_gbif_dict:
        # No exact match, use 'canonicalName' entry
        spec_match = spec_gbif_dict["canonicalName"]
        print(f"Warning: '{spec}' not exactly identified by GBIF.")

        if spec_match == spec:
            # No better match, keep input species
            print(
                f"No replacement (GBIF match was {spec_gbif_dict['rank']} '{spec_match}')."
            )
        else:
            if spec_gbif_dict["rank"] in accepted_ranks:
                # GBIF result in accepted ranks, keep this result
                print(
                    f"'{spec}' replaced with {spec_gbif_dict['rank']} '{spec_match}'."
                )
            else:
                # GBIF result above accepted ranks, check for suggestions
                spec_gbif_suggest = species.name_suggest(q=spec, rank="species")

                if len(spec_gbif_suggest) > 0:
                    # Suggestions found, use first (i.e. most relevant) suggestion
                    spec_gbif_suggest = [sgs["species"] for sgs in spec_gbif_suggest]
                    spec_match = spec_gbif_suggest[0]
                    sgs_string = ", ".join([f"'{sgs}'" for sgs in spec_gbif_suggest])
                    print(f"Candidate species: {sgs_string}.")

                    # Check if suggestions include the input species name
                    if spec in spec_gbif_suggest and spec_gbif_suggest.index(spec) > 0:
                        print(
                            f"SURPRISE: '{spec}' included, but not the first GBIF suggestion!"
                        )

                    print(
                        f"'{spec}' replaced with first GBIF suggestion '{spec_match}'."
                    )

                else:
                    # No suggestions, return input species
                    print(
                        f"No replacement (GBIF match was {spec_gbif_dict['rank']} '{spec_match}')."
                    )
                    return spec
    else:
        print(
            f"SURPRISE: Neither 'species' nor 'canonicalName' in result, match type {spec_gbif_dict['matchType']}."
        )

    return spec_match


def get_gbif_family(spec):
    spec_gbif_dict = species.name_backbone(name=spec, kingdom="plants")

    if "family" in spec_gbif_dict:
        return spec_gbif_dict["family"]
    else:
        print(f"Warning: Family for '{spec}' not found by GBIF.")
        return "not found"


def get_gbif_dict(species_info_dict, file_name="", info_name="PFT"):
    """
    Screen and correct species-info lookup table with GBIF taxonomic backbone.

    Parameters:
    - species_info_dict (dict): Dictionary where species names are keys, and infos are values.

    - info_name (str): Information name ('PFT' or 'Woodiness', default is 'PFT').

    Returns:
    - dict: Processed dictionary where species names are keys, and values are dictionaries with keys:
        - info_name('PFT' or 'Woodiness'): corresponding species info.
        - 'originalNames': List of species names from input dictionary (that were replaced or not).
    """

    print(f"Searching for species in GBIF taxonomic backbone ...")
    species_info_dict_gbif = {}
    processed_lines = 0

    for spec, info in species_info_dict.items():
        spec_match = get_gbif_species(spec, accepted_ranks=["GENUS", "FAMILY"])

        # Check if (replaced) species name is already in lookup table
        if spec_match in species_info_dict_gbif:
            # Check info for existing species
            species_info_dict_gbif[spec_match][info_name] = resolve_species_infos(
                spec_match,
                info_name,
                info,
                species_info_dict_gbif[spec_match][info_name],
            )
        else:
            # Add new species, info and replaced species name to lookup table
            species_info_dict_gbif[spec_match] = {
                info_name: info,
                "originalNames": [],
            }

        if spec != spec_match:
            # Add replaced species name to list of original names
            species_info_dict_gbif[spec_match]["originalNames"].append(spec)

        processed_lines += 1

    # Sort dictionary by species keys
    species_info_dict_gbif = dict(sorted(species_info_dict_gbif.items()))
    print(f"Processed {processed_lines} lines.")
    print(
        f"Final species-{info_name} lookup table has {len(species_info_dict_gbif)} entries."
    )

    # Save created dictionary to new file
    if file_name != "":
        ut.dict_to_file(
            species_info_dict_gbif, ["Species", info_name, "Original names"], file_name
        )

    return species_info_dict_gbif


def get_pft_from_family_woodiness(spec, species_family_dict, species_woodiness_dict):
    grass_families = ["Poaceae", "Cyperaceae", "Juncaceae"]
    if spec not in species_family_dict:
        print(f"Warning: Family for '{spec}' not found in lookup table.")
        family = "not found"
    else:
        family = species_family_dict[spec]

    if spec not in species_woodiness_dict:
        print(f"Warning: Woodiness for '{spec}' not found in lookup table.")
        woodiness = "not found"
        if family == "not found":
            return "not found"
    else:
        woodiness = species_woodiness_dict[spec]

    if family in grass_families:
        return "grass"
    elif woodiness == "herbaceous":
        if family == "Fabaceae":
            return "legume"
        else:
            return "forb"
    else:
        return "not assigned"


def read_species_list(file_name, species_column=0, header_lines=1, check_gbif=True):
    """
    Read species names from a file.

    Parameters:
    - file_name (str): Name of the file.
    - species_column (str or int): Species column name or number (0-based index, default is 0).
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
            print(f"ERROR reading Excel file: {e}")
            return []

        # Determine column index
        if isinstance(species_column, str):
            try:
                column_index = df.columns.get_loc(species_column)
            except KeyError:
                print(f"ERROR: Column '{species_column}' not found in the Excel file.")
                return []
        elif isinstance(species_column, int):
            column_index = species_column
        else:
            print(
                "ERROR: Invalid column identifier. Please provide a column name (str) or column number (int)."
            )
            return []

        # Extract species names from the specified column, convert to string and replace 'nan' by empty string
        species_list = df.iloc[:, column_index].tolist()
        species_list = [str(spec) for spec in species_list]
        species_list = ut.replace_substrings(species_list, "nan", "", at_end=True)

    elif file_extension == ".txt":
        # Read from tab-separated text file
        try:
            with open(file_name, "r") as file:
                species_data = [line.strip().split("\t") for line in file]

        except Exception as e:
            print(f"ERROR reading text file: {e}")
            return []

        # Determine column index
        if isinstance(species_column, str):
            if species_column in species_data[header_lines - 1]:
                column_index = species_data[header_lines - 1].index(species_column)
            else:
                print(
                    f"ERROR: Column '{species_column}' not found in the specified header line of the text file."
                )
                return []
        elif isinstance(species_column, int):
            column_index = species_column
        else:
            print(
                "ERROR: Invalid column identifier. Please provide a column name (str) or column number (int)."
            )
            return []

        species_list = [line[column_index] for line in species_data[header_lines:]]

    else:
        print(
            f"ERROR: Unsupported file format. Supported formats are 'xlsx' and 'txt'."
        )
        return []

    # GBIF check and correction if selected
    if check_gbif:
        print(f"Searching for species from species list in GBIF taxonomic backbone ...")
        species_list_renamed = []
        for spec in species_list:
            species_list_renamed.append(
                (get_gbif_species(spec, accepted_ranks=["GENUS", "FAMILY"]), spec)
            )

        # Save GBIF corrected species list to file
        file_name = ut.add_string_to_file_name(file_name, "__GBIFList")
        ut.list_to_file(
            species_list_renamed, ["Species GBIF", "Species Original"], file_name
        )

        # Overwrite species_list with GBIF correction for empty/duplicate count below
        species_list = [entry[0] for entry in species_list_renamed]
    else:
        # No renaming, just add identical column
        species_list_renamed = list(zip(species_list, species_list))

    # No removal of 'nan' or duplicate species entries, assigned infos to be matched with original list later
    empty_strings = species_list.count("")
    print(
        f"Species list has {len(species_list)} entries, including {empty_strings} empty entries."
    )
    duplicates = ut.count_duplicates(species_list)
    if len(duplicates) > 0:
        print("Duplicates: ", end="")
        print(", ".join([f"'{spec}' ({count})" for spec, count in duplicates.items()]))

    return species_list_renamed


def user_input_info(species_info_dict, info_name, start_string):
    """
    Iterate through species without info assigned and prompt user to select a new info.

    Parameters:
    - species_info_dict (dict): Dictionary with species names as keys and corresponding infos.
    - info_name (str): Information name ('PFT' or 'Woodiness').
    - start_string (string): Beginning of infos that get suggested for reassignment.

    Returns:
    - dict: Modified dictionary with updated infos based on user input.
    """

    valid_choices = get_valid_infos(info_name)
    valid_choices.append("not assigned")
    choice_string = ""
    print(f"Going through species with {info_name} '{start_string}' ...")
    print(f"You can select the new {info_name} from the following options:")

    for index, info in enumerate(valid_choices, start=1):
        print(f"{index}. '{info}'")
        choice_string += f"{index} '{info}' "

    print(f"{index + 1}. Skip (leave {info_name} as is). ")
    print(f"{index + 2}. Exit {info_name} assignment.")

    for spec, info in species_info_dict.items():
        if bool(spec) and info.startswith(start_string):
            print(f"Species: {spec}. Current {info_name}: '{info}'.")
            user_choice = input(
                f"Enter your choice ({choice_string}{index + 1} Skip {index + 2} Exit): "
            )

            try:
                user_choice = int(user_choice)
            except:
                print(f"Invalid choice. Leaving {info_name} as is.")
            else:
                if 1 <= user_choice <= len(valid_choices):
                    user_info = f"{valid_choices[user_choice - 1]} (user input)"
                    species_info_dict[spec] = user_info
                    print(f"Changing {info_name} to '{user_info}'.")
                elif user_choice == len(valid_choices) + 1:
                    pass  # Leave as is, no change needed
                elif user_choice == len(valid_choices) + 2:
                    print(
                        f"Exiting the manual {info_name} assignment for species with {info_name} '{start_string}'."
                    )
                    break  # Exit the loop
                else:
                    print(f"Invalid choice. Leaving {info_name} as is.")

    return species_info_dict


def get_species_info(
    species_list,
    species_info_lookup,
    info_name,
    file_name,
    return_as_list=False,
    ask_user_input=True,
):
    """
    Create a dict or list with species and corresponding infos from a species-info lookup table,
    and save to file.

    Parameters:
    - species_list (list): List of species names.
    - species_info_lookup (dict): Dictionary with species names as keys and corresponding infos.
    - info_name (str): Information name ('PFT' or 'Woodiness').
    - file_name (str): Name of the file for saving the new list.
    - return_as_list(bool): If True, return argument is a list, otherwise a dict (default is False)
    - ask_user_input (bool): If True, ask user for manual input of unclear infos (default is True).

    Returns:
    - dict or list: Dict or list of pairs of the species names and corresponding infos.
    """
    print(f"Searching for species from species list in species-info lookup table ...")

    # Convert species_info_lookup to dictionary of only infos if not already
    species_info_lookup = ut.reduce_dict_to_single_info(species_info_lookup, info_name)

    # Read info from lookup dict if available
    species_info_dict = {}
    for spec in species_list:
        species_info_dict[spec] = ut.lookup_info_in_dict(spec, species_info_lookup)

    # Check for unclear infos
    for unclear_info_string in ["not found", "not assigned", "variable"]:
        count_unclear = sum(
            bool(spec) and info.startswith(unclear_info_string)
            for spec, info in species_info_dict.items()
        )
        if count_unclear:
            print(f"Species with {info_name} '{unclear_info_string}': {count_unclear}.")
            if ask_user_input:
                # Ask user if species with unclear info shall be modified manually
                manual_input = input(
                    f"Do you want to make manual inputs for these species? (y/n): "
                ).lower()

                if manual_input == "y":
                    species_info_dict = user_input_info(
                        species_info_dict, info_name, unclear_info_string
                    )

    if return_as_list:
        # New list of species and infos, allowing for duplicates and preserving order
        species_info_list = ut.add_info_to_list(species_list, species_info_dict)
        if file_name != "":
            ut.list_to_file(species_info_list, ["Species", info_name], file_name)

        return species_info_list
    else:
        # Sort, save and return created dict
        species_info_dict = dict(sorted(species_info_dict.items()))
        if file_name != "":
            ut.dict_to_file(species_info_dict, ["Species", info_name], file_name)

        return species_info_dict


def get_species_family(species_list, file_name, return_as_list=False):
    info_name = "Family GBIF"
    print(f"Searching for species' families in GBIF taxonomic backbone ...")
    species_info_dict = {}
    for spec in species_list:
        if spec not in species_info_dict:
            species_info_dict[spec] = get_gbif_family(spec)

    # species_family_list = []
    # for spec in species_list:
    #     species_family_list.append((spec, get_gbif_family(spec)))

    if return_as_list:
        # New list of species and infos, allowing for duplicates and preserving order
        species_info_list = ut.add_info_to_list(species_list, species_info_dict)
        if file_name != "":
            ut.list_to_file(species_info_list, ["Species", info_name], file_name)

        return species_info_list
    else:
        # Sort, save and return created dict
        species_info_dict = dict(sorted(species_info_dict.items()))
        if file_name != "":
            ut.dict_to_file(species_info_dict, ["Species", info_name], file_name)

        return species_info_dict


def get_species_pft(
    species_list,
    species_family_dict,
    species_woodiness_dict,
    file_name,
    return_as_list=False,
    ask_user_input=True,
):
    info_name = "PFT Family_Woodiness"
    species_info_dict = {}
    for spec in species_list:
        if spec not in species_info_dict:
            species_info_dict[spec] = get_pft_from_family_woodiness(
                spec, species_family_dict, species_woodiness_dict
            )

    # Check for unclear infos
    for unclear_info_string in ["not found", "not assigned"]:
        count_unclear = sum(
            bool(spec) and info.startswith(unclear_info_string)
            for spec, info in species_info_dict.items()
        )
        if count_unclear:
            print(f"Species with {info_name} '{unclear_info_string}': {count_unclear}.")
            if ask_user_input:
                # Ask user if species with unclear info shall be modified manually
                manual_input = input(
                    f"Do you want to make manual inputs for these species? (y/n): "
                ).lower()

                if manual_input == "y":
                    species_info_dict = user_input_info(
                        species_info_dict, "PFT", unclear_info_string
                    )

    if return_as_list:
        # New list of species and infos, allowing for duplicates and preserving order
        species_info_list = ut.add_info_to_list(species_list, species_info_dict)
        if file_name != "":
            ut.list_to_file(species_info_list, ["Species", info_name], file_name)

        return species_info_list
    else:
        # Sort, save and return created dict
        species_info_dict = dict(sorted(species_info_dict.items()))
        if file_name != "":
            ut.dict_to_file(species_info_dict, ["Species", info_name], file_name)

        return species_info_dict


# Example usage:

# Get PFT dictionary from lookup table, and store to file (once created, this file can also be used to get the dictionary)
folder = Path("speciesMappingLookupTables")
# file_name = folder / "TRY_Categorical_Traits__Grassmind_PFTs.txt"
file_name = folder / "TRY_Categorical_Traits__Grassmind_PFTs__GBIFDictionary.txt"
species_pft_dict = read_species_info_dict(file_name, save_new_file=True)

# # Check dictionary against GBIF taxonomic backbone, and store to file (once created, this file can also be used to get the dictionary)
# file_name = ut.add_string_to_file_name(file_name, "__GBIFDictionary")
# species_pft_dict_gbif = get_gbif_dict(species_pft_dict, file_name, info_name="PFT")

# Get Woodiness dictionary from lookup table, and store to file (once created, this file can also be used to get the dictionary)
# file_name = folder / "traitecoevo__growth_form.txt"
# species_woodiness_dict = read_species_info_dict(
#     file_name, info_name="Woodiness", info_column=2, save_new_file=True
# )
file_name = folder / "traitecoevo__growth_form__GBIFDictionary.txt"
species_woodiness_dict = read_species_info_dict(
    file_name, info_name="Woodiness", info_column=1, save_new_file=True
)

# # Check dictionary against GBIF taxonomic backbone, and store to file (once created, this file can also be used to get the dictionary)
# file_name = ut.add_string_to_file_name(file_name, "__GBIFDictionary")
# species_woodiness_dict_gbif = get_gbif_dict(
#     species_woodiness_dict, file_name, info_name="Woodiness"
# )

# Get example list, here from GCEF site
folder = Path("speciesMappingExampleLists")
# file_name = folder / "102ae489-04e3-481d-97df-45905837dc1a_Species.xlsx"
# file_name = folder / "102ae489-04e3-481d-97df-45905837dc1a_Species.txt"
# species_list_renamed = read_species_list(
#     file_name, species_column="Name", check_gbif=True
# )
file_name = folder / "102ae489-04e3-481d-97df-45905837dc1a_Species__GBIFList.xlsx"
species_list_renamed = read_species_list(file_name, check_gbif=False)

# Use first column only for subsequent lookup of infos
species_list = [entry[0] for entry in species_list_renamed]

# Find PFT (optional user modifications) and write to file
info_name = "PFT"
file_name_pft = ut.add_string_to_file_name(file_name, f"__{info_name}")
species_pft_assigned = get_species_info(
    species_list,
    species_pft_dict,
    info_name,
    file_name_pft,
    return_as_list=False,
    ask_user_input=False,
)

# Find Woodiness (optional user modifications) and write to file
info_name = "Woodiness"
file_name_woodiness = ut.add_string_to_file_name(file_name, f"__{info_name}")
species_woodiness_assigned = get_species_info(
    species_list,
    species_woodiness_dict,
    info_name,
    file_name_woodiness,
    return_as_list=False,
    ask_user_input=False,
)

# Find GBIF Family and write to file
## TODO: perhaps combine with get_species_info?
info_name = "FamilyGBIF"
file_name_family = ut.add_string_to_file_name(file_name, f"__{info_name}")
species_family_assigned = get_species_family(
    species_list, file_name_family, return_as_list=False
)

info_name = "PFTFamilyWoodiness"
file_name_pft_from_family_woodiness = ut.add_string_to_file_name(
    file_name, f"__{info_name}"
)
species_pft_from_family_woodiness_assigned = get_species_pft(
    species_list,
    species_family_assigned,
    species_woodiness_assigned,
    file_name_pft_from_family_woodiness,
    return_as_list=False,
    ask_user_input=True,
)

# Combine all infos to one list, and write to file
species_infos_assigned = ut.add_to_list(
    species_list_renamed, ut.add_info_to_list(species_list, species_pft_assigned)
)
species_infos_assigned = ut.add_to_list(
    species_infos_assigned,
    ut.add_info_to_list(species_list, species_woodiness_assigned),
)
species_infos_assigned = ut.add_to_list(
    species_infos_assigned, ut.add_info_to_list(species_list, species_family_assigned)
)
species_infos_assigned = ut.add_to_list(
    species_infos_assigned,
    ut.add_info_to_list(species_list, species_pft_from_family_woodiness_assigned),
)

file_name_combined = ut.add_string_to_file_name(file_name, f"__combined_infos")
ut.list_to_file(
    species_infos_assigned,
    [
        "Species",
        "Species Original",
        "PFT TRY",
        "Woodiness",
        "Family GBIF",
        "PFT Family_Woodiness",
    ],
    file_name_combined,
)
