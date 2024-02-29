"""
Module Name: assign_pfts.py
Author: Thomas Banitz, Franziska Taubert, BioDT
Date: January, 2024
Description: Assign PFTs to species with the following options:
             - based on TRY categorical traits table (with prepared PFT column in this table)
             - based on GBIF taxonomic backbone for family and https://github.com/traitecoevo/growthform
               table (Zanne et al.) for Woodiness 
             - based on combination of both methods

Species names can (and should) be adjusted by GBIF taxonomic backbone  
"""

from pathlib import Path
import utils as ut
import pandas as pd
import csv
from pygbif import species


def combine_info_strings(info_name, info_1, info_2):
    """
    Combine infos for a species.

    Parameters:
    - info_name (str): Information name ('PFT' or 'Woodiness' or 'Family').
    - info_1 (str): First info entry.
    - info_2 (str): Second info entry.

    Returns:
    - str: Combined info entry.
    """
    info_1_core = ut.replace_substrings(info_1, ["(", ")", "conflicting "], "")
    info_2_core = ut.replace_substrings(info_2, ["(", ")", "conflicting "], "")

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


def resolve_species_infos(spec, info_name, info_1, info_2, warning_duplicates=True):
    """
    Resolve conflicting infos for a species.

    Parameters:
    - spec (str): Species for which infos are being resolved.
    - info_name (str): Information name ('PFT' or 'Woodiness' or 'Family').
    - info_1 (str): First info entry.
    - info_2 (str): Second info entry.
    - warning_duplicates (bool): Throw warnings for resolving duplicate entries (default is True).

    Returns:
    - str: Resolved info entry.
    """
    # Warning for duplicate species
    if warning_duplicates:
        print(f"Warning: Duplicate species entry found for species '{spec}'.")

    # Check if the infos are the same, no need to change the info
    if info_1 == info_2:
        info_resolved = info_1

        if warning_duplicates:
            print(f"{info_name} is equal. Keeping the {info_name} '{info_resolved}'.")
    # Check if infos start with "not ", keep other one
    else:
        if info_1.startswith("not ") and not info_2.startswith("not "):
            info_resolved = info_2
        elif not info_1.startswith("not ") and info_2.startswith("not "):
            info_resolved = info_1
        elif info_1.startswith("not ") and info_2.startswith("not "):
            info_resolved = "not assigned"
        elif f"({info_1}?)" == info_2:
            info_resolved = info_1
        elif f"({info_2}?)" == info_1:
            info_resolved = info_2
        else:
            info_resolved = combine_info_strings(info_name, info_1, info_2)

            # Raise an error for two conflicting assigned infos
            if info_resolved.startswith("conflicting "):
                print(
                    f"CONFLICT: Different assigned {info_name} found for species {spec}!"
                )
        if warning_duplicates:
            print(
                f"{info_name} differs: '{info_1}' vs. '{info_2}'. Keeping the {info_name} '{info_resolved}'."
            )

    return info_resolved


def resolve_species_info_dicts(
    info_name, info_dict_1, info_dict_2, ask_user_input=False
):
    """
    Resolve conflicting info entries for all species from two dictionaries.

    Parameters:
    - info_name (str): Information name ('PFT' or 'Woodiness' of 'Family').
    - info_dict_1 (dict): First dictionary mapping species to information entries.
    - info_dict_2 (dict): Second dictionary mapping species to information entries.
    - ask_user_input (bool): Ask user for manual input of unclear infos (default is False).

    Returns:
    - dict: Dictionary with resolved information entries for each species.
    """
    print(f"Combining {info_name} information from two dictionaries ...")
    resolved_dict = {}

    # Iterate over keys present in both dictionaries and resolve infos
    common_keys = set(info_dict_1.keys()) & set(info_dict_2.keys())

    for spec in common_keys:
        resolved_dict[spec] = resolve_species_infos(
            spec,
            info_name,
            info_dict_1[spec],
            info_dict_2[spec],
            warning_duplicates=False,
        )

    # Add entries present only in one of the dictionaries
    for spec in set(info_dict_1.keys()) - common_keys:
        resolved_dict[spec] = info_dict_1[spec]

    for spec in set(info_dict_2.keys()) - common_keys:
        resolved_dict[spec] = info_dict_2[spec]

    # Sort and check for unclear infos
    resolved_dict = dict(sorted(resolved_dict.items()))
    resolved_dict = check_unclear_infos(info_name, resolved_dict, ask_user_input)

    return resolved_dict


def get_valid_infos(info_name):
    """
    Get valid information entries based on the specified information type.

    Parameters:
        info_name (str): Type of species information ('PFT' or 'Woodiness').

    Returns:
        list: List of valid information entries for the specified type.

    Raises:
        ValueError: If an unsupported species information type is provided.
    """
    if info_name == "PFT":
        # Set valid grassland PFT entries
        return [
            "grass",
            "forb",
            "legume",
            "(tree)",
            "(shrub)",
            "(shrub/tree)",
            "(fern)",
            "(moss)",
            "(lichen)",
            "(legume?)",
        ]
    elif info_name == "Woodiness":
        # Set valid Woodiness entries
        return ["woody", "herbaceous", "variable", "(fern)", "(lichen)", "(moss)"]
    elif info_name == "Family":
        return ["any"]
    else:
        raise ValueError(
            f"ERROR: Unsupported species information type. Supported types are 'PFT' and 'Woodiness'."
        )


def replace_info_strings(info, info_name):
    """
    Revise information entries based on the specified information type for consistency.

    Parameters:
        info (str): Original information entry.
        info_name (str): Type of species information ('PFT' or 'Woodiness').

    Returns:
        str: Revised information entry.
    """
    if info_name == "PFT":
        info = ut.replace_substrings(info, "not assigned ()", "not assigned")
        info = ut.replace_substrings(info, "not assigned (", "(")
        info = ut.replace_substrings(
            info, "(herb/shrub)", "conflicting (forb vs. shrub)"
        )
        info = ut.replace_substrings(
            info, "(herb/shrub/tree)", "conflicting (forb vs. shrub/tree)"
        )
    elif info_name == "Woodiness":
        info = ut.replace_substrings(
            info,
            ["conflicting", "herb/shrub", "herb/shrub/tree"],
            "conflicting (herbaceous vs. woody)",
            at_end=True,
        )
        info = ut.replace_substrings(
            info, ["W", "shrub", "shrub/tree", "tree"], "woody", at_end=True
        )
        info = ut.replace_substrings(
            info, ["H", "herb", "graminoid"], "herbaceous", at_end=True
        )
        info = ut.replace_substrings(info, "NA", "not assigned", at_end=True)
        info = ut.replace_substrings(info, "fern", "(fern)", at_end=True)
        info = ut.replace_substrings(info, "lichen", "(lichen)", at_end=True)
        info = ut.replace_substrings(info, "moss", "(moss)", at_end=True)

    if not info:
        info = "not assigned"

    return info


def read_species_info_dict(
    file_name,
    info_name,
    species_column=0,
    info_column=1,
    header_lines=1,
    save_new_file=False,
):
    """
    Read a dictionary from a text file containing species and a corresponding information (PFT or Woodiness).

    Parameters:
    - file_name (str): Path to the text file.
    - info_name (str): Information name ('PFT' or 'Woodiness', default is 'PFT').
    - species_column(int): Species column number (0-based index, default is 0).
    - info_column (int): Information column number (0-based index, default is 1).
    - header_lines (int): Number of header lines to skip (default is 1).
    - save_new_file (bool): Save result dictionary to new file (default is False).

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
            info = replace_info_strings(info, info_name)

            # Warning if info is not valid and not "not assigned"
            if (
                not (valid_infos == ["any"] and info != "")
                and info not in valid_infos
                and not info.startswith("not assigned")
            ):
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
        file_name = ut.add_string_to_file_name(
            file_name, f"__{info_name}__UserDictionary"
        )
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

    if spec_gbif_dict["matchType"] == "NONE":
        # No match, return input species
        print(f"Warning: '{spec}' not found.")

        return spec
    elif spec_gbif_dict["rank"] == "SPECIES":
        if "species" in spec_gbif_dict:
            # Use 'species' entry
            spec_match = spec_gbif_dict["species"]

            if spec_match != spec:
                print(f"'{spec}' replaced with GBIF NAME '{spec_match}'.")
        else:
            # No 'species' entry, use 'canonicalName' entry (should not happen)
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
                spec_match = f"{spec_match} species"
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

                    # Check if suggestions include the input species name but not at first position
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
    """
    Get family information for a given species from GBIF.

    Parameters:
    - spec (str): Species name to find family.

    Returns:
    - str: Family information or "not found."
    """
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

        if (
            spec_match != spec
            and not info_name == "Family"  # Keep family infos
            and spec_match.endswith(" species")
            and not "grass" in info  # Keep all infos with "grass", also conflicts
        ):
            info = "not assigned"

        # Check if (replaced) species name is already in lookup table
        if spec_match in species_info_dict_gbif:
            # Check info for existing species
            species_info_dict_gbif[spec_match][info_name] = resolve_species_infos(
                spec_match,
                info_name,
                info,
                species_info_dict_gbif[spec_match][info_name],
            )
            species_info_dict_gbif[spec_match]["originalNames"].append(spec)
        else:
            # Add new species, info and replaced species name to lookup table
            species_info_dict_gbif[spec_match] = {
                info_name: info,
                "originalNames": [spec],
            }

        # if spec != spec_match:
        # Add (replaced) species name to list of original names
        # species_info_dict_gbif[spec_match]["originalNames"].append(spec)

        processed_lines += 1

    # Sort dictionary by species keys
    species_info_dict_gbif = dict(sorted(species_info_dict_gbif.items()))
    print(f"Processed {processed_lines} lines.")
    print(
        f"Final species-{info_name} lookup table has {len(species_info_dict_gbif)} entries."
    )

    # Save created dictionary to new file
    if file_name:
        ut.dict_to_file(
            species_info_dict_gbif, ["Species", info_name, "Original names"], file_name
        )

    return species_info_dict_gbif


def get_pft_from_family_woodiness(spec, species_family_dict, species_woodiness_dict):
    """
    Determine PFT based on species family and woodiness.

    Parameters:
    - spec (str): Species name to find PFT.
    - species_family_dict (dict): Dictionary where species names are keys, and family infos are values.
    - species_woodiness_dict (dict): Dictionary where species names are keys, and woodiness infos are values.

    Returns:
    - str: PFT info or "not assigned."
    """
    # Get family or throw warning if not found
    if spec in species_family_dict:
        family = species_family_dict[spec]
    else:
        print(f"Warning: Family for '{spec}' not found in lookup table.")
        family = "not found"

    # Get woodiness or throw warning if not found
    if spec in species_woodiness_dict:
        woodiness = species_woodiness_dict[spec]
    else:
        print(f"Warning: Woodiness for '{spec}' not found in lookup table.")
        woodiness = "not found"

    # Return "not found" as PFT if no info was found
    if family == "not found" and woodiness == "not found":
        return "not found"

    # Assign PFT according to heuristics
    grass_families = ["Poaceae", "Cyperaceae", "Juncaceae"]

    if family in grass_families:
        return "grass"
    elif woodiness == "herbaceous":
        if family == "Fabaceae":
            return "legume"
        else:
            return "forb"
    elif woodiness == "woody":
        return "(woody)"
    else:
        return "not assigned"


def read_species_list(file_name, species_column=0, header_lines=1, check_gbif=True):
    """
    Read species names from a file.

    Parameters:
    - file_name (str): Name of the species list file.
    - species_column (str or int): Species column name or number (0-based index, default is 0).
    - header_lines (int): Number of header line, lines before will be skipped (default is 1).
    - check_gbif (bool): Check/correct species name with GBIF taxonomic backbone (default is True).

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
        print(f"Searching for species in GBIF taxonomic backbone ...")
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


def check_unclear_infos(info_name, species_info_dict, ask_user_input=True):
    """
    Check for species with unclear information entries in a dictionary.

    Parameters:
    - info_name (str): Information name ('PFT' or 'Woodiness').
    - species_info_dict (dict): Dictionary mapping species to information entries.
    - ask_user_input (bool): Ask user for manual input of unclear infos (default is True).

    Returns:
    - dict: Updated dictionary after resolving unclear information entries manually (if requested).
    """
    unclear_info_strings = ["not found", "not assigned", "variable"]

    for unclear_info in unclear_info_strings:
        count_unclear = sum(
            bool(spec) and info.startswith(unclear_info)
            for spec, info in species_info_dict.items()
        )

        if count_unclear:
            # Inform about unclear infos
            print(f"Species with {info_name} '{unclear_info}': {count_unclear}.")

            if ask_user_input:
                # Ask user if species with unclear info shall be modified manually
                manual_input = input(
                    f"Do you want to make manual inputs for these species? (y/n): "
                ).lower()

                if manual_input == "y":
                    species_info_dict = user_input_info(
                        species_info_dict, info_name, unclear_info
                    )

    return species_info_dict


def return_as_list_or_dict(
    return_as_list, info_name, species_list, species_info_dict, file_name
):
    if return_as_list:
        # New list of species and infos, allowing for duplicates and preserving order
        species_info_list = ut.add_info_to_list(species_list, species_info_dict)

        if file_name:
            ut.list_to_file(species_info_list, ["Species", info_name], file_name)

        return species_info_list
    else:
        # Sort, save and return species info dictionary
        species_info_dict = dict(sorted(species_info_dict.items()))

        if file_name:
            ut.dict_to_file(species_info_dict, ["Species", info_name], file_name)

        return species_info_dict


def get_species_info(
    species_list,
    species_info_lookup,
    info_name,
    file_name,
    return_as_list=False,
    ask_user_input=False,
):
    """
    Create a dict or list with species and corresponding infos from a species-info lookup table,
    and save to file.

    Parameters:
    - species_list (list): List of species names.
    - species_info_lookup (dict): Dictionary with species names as keys and corresponding infos.
    - info_name (str): Information name ('PFT' or 'Woodiness').
    - file_name (str): File name to save the result (empty string to skip saving).
    - return_as_list(bool): Return as a list, otherwise as a dict (default is False).
    - ask_user_input (bool): Ask user for manual input of unclear infos (default is False).

    Returns:
    - dict or list: Dict or list of pairs of the species names and corresponding infos.
    """
    print(f"Searching for species' {info_name} in species-{info_name} lookup table ...")

    # Convert species_info_lookup to dictionary of only infos if not already
    species_info_lookup = ut.reduce_dict_to_single_info(species_info_lookup, info_name)

    # Read info from lookup dict if available
    species_info_dict = {}

    for spec in species_list:
        if spec not in species_info_dict:
            species_info_dict[spec] = ut.lookup_info_in_dict(spec, species_info_lookup)

    # Check for unclear infos and get result (list or dict)
    species_info_dict = check_unclear_infos(
        info_name, species_info_dict, ask_user_input
    )
    species_info_result = return_as_list_or_dict(
        return_as_list, info_name, species_list, species_info_dict, file_name
    )

    return species_info_result


def get_species_family(species_list, file_name, return_as_list=False):
    """
    Retrieve families for a list of species using GBIF taxonomic backbone.

    Parameters:
    - species_list (list): List of species names.
    - file_name (str): File name to save the result (empty string to skip saving).
    - return_as_list(bool): Return as a list, otherwise as a dict (default is False).

    Returns:
    - dict or list: Resulting dictionary or list with species and their Family information.
    """
    info_name = "Family"
    print("Searching for species' Family in GBIF taxonomic backbone ...")
    species_info_dict = {}

    for spec in species_list:
        if spec not in species_info_dict:
            species_info_dict[spec] = get_gbif_family(spec)

    # Get result (list or dict)
    species_info_result = return_as_list_or_dict(
        return_as_list, info_name, species_list, species_info_dict, file_name
    )

    return species_info_result


def get_species_pft_from_family_woodiness(
    species_list,
    species_family_dict,
    species_woodiness_dict,
    file_name,
    return_as_list=False,
    ask_user_input=False,
):
    """
    Get PFT for a list of species based on family and woodiness.

    Parameters:
    - species_list (list): List of species names.
    - species_family_dict (dict): Dictionary mapping species to their families.
    - species_woodiness_dict (dict): Dictionary mapping species to their woodiness.
    - file_name (str): File name to save the result (empty string to skip saving).
    - return_as_list(bool): Return as a list, otherwise as a dict (default is False).
    - ask_user_input (bool): Ask user for manual input of unclear infos (default is False).

    Returns:
    - dict or list: Resulting dictionary or list with species and their PFT information.
    """
    info_name = "PFT"
    print(
        f"Searching for species' {info_name} in species-Family and species-Woodiness lookup tables ..."
    )
    species_info_dict = {}

    for spec in species_list:
        if spec not in species_info_dict:
            species_info_dict[spec] = get_pft_from_family_woodiness(
                spec, species_family_dict, species_woodiness_dict
            )

    # Check for unclear infos and get result (list or dict)
    species_info_dict = check_unclear_infos(
        info_name, species_info_dict, ask_user_input
    )
    species_info_result = return_as_list_or_dict(
        return_as_list, info_name, species_list, species_info_dict, file_name
    )

    return species_info_result


##########################################################################################################################
# Example usage:

folder = Path("speciesMappingLookupTables")

# # Get PFT dictionary from lookup table, and store to file (once created, this file can also be used to get the dictionary)
# info_name = "PFT"
# # file_name = folder / "TRY_Categorical_Traits.txt"
# # species_pft_try_lookup = read_species_info_dict(
# #     file_name, info_name, info_column=5, save_new_file=True
# # )
# file_name = folder / "TRY_Categorical_Traits__PFT__GBIFDictionary.txt"
# species_pft_try_lookup = read_species_info_dict(
#     file_name, info_name, info_column=1, save_new_file=False
# )
# # # Check dictionary against GBIF taxonomic backbone, and store to file (once created, this file can also be used to get the dictionary)
# # file_name = ut.add_string_to_file_name(file_name, f"__{info_name}__GBIFDictionary")
# # species_pft_try_lookup = get_gbif_dict(species_pft_try_lookup, file_name, info_name)

# Get Family dictionary from lookup table, and store to file (once created, this file can also be used to get the dictionary)
info_name = "Family"
# file_name = folder / "TRY_Categorical_Traits.txt"
# species_family_try_lookup = read_species_info_dict(
#     file_name, info_name, info_column=3, save_new_file=True
# )
file_name = folder / "TRY_Categorical_Traits__Family__GBIFDictionary.txt"
species_family_try_lookup = read_species_info_dict(
    file_name, info_name, info_column=1, save_new_file=False
)
# # Check dictionary against GBIF taxonomic backbone, and store to file (once created, this file can also be used to get the dictionary)
# file_name = ut.add_string_to_file_name(file_name, f"__{info_name}__GBIFDictionary")
# species_family_try_lookup = get_gbif_dict(
#     species_family_try_lookup, file_name, info_name
# )

# Get Woodiness dictionary from lookup table, and store to file (once created, this file can also be used to get the dictionary)
info_name = "Woodiness"
# file_name = folder / "TRY_Categorical_Traits.txt"
# file_name = folder / "TRY_Categorical_Traits__test.txt"
# species_woodiness_try_lookup = read_species_info_dict(
#     file_name, info_name, info_column=4, save_new_file=True
# )
file_name = folder / "TRY_Categorical_Traits__Woodiness__GBIFDictionary.txt"
species_woodiness_try_lookup = read_species_info_dict(
    file_name, info_name, info_column=1, save_new_file=False
)
# # Check dictionary against GBIF taxonomic backbone, and store to file (once created, this file can also be used to get the dictionary)
# file_name = ut.add_string_to_file_name(file_name, f"__{info_name}__GBIFDictionary")
# species_woodiness_try_lookup = get_gbif_dict(
#     species_woodiness_try_lookup, file_name, info_name
# )

# Get Woodiness dictionary from lookup table, and store to file (once created, this file can also be used to get the dictionary)
info_name = "Woodiness"
# file_name = folder / "traitecoevo__growth_form.txt"
# species_woodiness_zanne_lookup = read_species_info_dict(
#     file_name, info_name, info_column=2, save_new_file=True
# )
file_name = folder / "traitecoevo__growth_form__Woodiness__GBIFDictionary.txt"
info_name = "Woodiness"
species_woodiness_zanne_lookup = read_species_info_dict(
    file_name, info_name, info_column=1, save_new_file=False
)
# # Check dictionary against GBIF taxonomic backbone, and store to file (once created, this file can also be used to get the dictionary)
# file_name = ut.add_string_to_file_name(file_name, f"__{info_name}__GBIFDictionary")
# species_woodiness_lookup = get_gbif_dict(
#     species_woodiness_zanne_lookup, file_name, info_name="Woodiness"
# )

# Get example list, here from GCEF site
folder = Path("speciesMappingExampleLists")
file_name_species_list = folder / "102ae489-04e3-481d-97df-45905837dc1a_Species.xlsx"
species_list_renamed = read_species_list(
    file_name_species_list, species_column="Name", check_gbif=True
)
# file_name_species_list = (
#     folder / "102ae489-04e3-481d-97df-45905837dc1a_Species__GBIFList.xlsx"
# )
# species_list_renamed = read_species_list(file_name_species_list, check_gbif=False)

# Use first column of renamed list only for subsequent lookup of infos
# (list can have original species names in additional column)
species_list = [entry[0] for entry in species_list_renamed]

# Find Family (optional user modifications) based on TRY and write to file
file_name = ut.add_string_to_file_name(file_name_species_list, "__FamilyTRY")
species_family_try = get_species_info(
    species_list,
    species_family_try_lookup,
    "Family",
    file_name,
)

# Find Family based on GBIF and write to file
file_name = ut.add_string_to_file_name(file_name_species_list, "__FamilyGBIF")
species_family_gbif = get_species_family(species_list, file_name)

# Combine and resolve Family from both sources (TRY & GBIF, optional user modifications)
file_name = ut.add_string_to_file_name(file_name_species_list, "__FamilyCombined")
species_family_combined = resolve_species_info_dicts(
    "Family",
    species_family_try,
    species_family_gbif,
)
ut.dict_to_file(species_family_combined, ["Species", "Family Combined"], file_name)

# Find Woodiness (optional user modifications) based on TRY and write to file
file_name = ut.add_string_to_file_name(file_name_species_list, "__WoodinessTRY")
species_woodiness_try = get_species_info(
    species_list,
    species_woodiness_try_lookup,
    "Woodiness",
    file_name,
)

# Find Woodiness (optional user modifications) based on Zanne and write to file
file_name = ut.add_string_to_file_name(file_name_species_list, "__WoodinessZanne")
species_woodiness_zanne = get_species_info(
    species_list,
    species_woodiness_zanne_lookup,
    "Woodiness",
    file_name,
)

# Combine and resolve Woodiness from both sources (TRY & Zanne, optional user modifications)
file_name = ut.add_string_to_file_name(file_name_species_list, "__WoodinessCombined")
species_woodiness_combined = resolve_species_info_dicts(
    "Woodiness",
    species_woodiness_try,
    species_woodiness_zanne,
)
ut.dict_to_file(
    species_woodiness_combined, ["Species", "Woodiness Combined"], file_name
)

# Find PFT (optional user modifications) based on TRY Family and Woodiness
file_name = ut.add_string_to_file_name(
    file_name_species_list, "__PFTFamilyWoodinessTRY"
)
species_pft_family_woodiness_try = get_species_pft_from_family_woodiness(
    species_list,
    species_family_try,
    species_woodiness_try,
    file_name,
)

# Find PFT (optional user modifications) based on GBIF Family and TRY Woodiness
file_name = ut.add_string_to_file_name(
    file_name_species_list, "__PFTFamilyWoodinessGBIF_TRY"
)
species_pft_family_woodiness_gbif_try = get_species_pft_from_family_woodiness(
    species_list,
    species_family_gbif,
    species_woodiness_try,
    file_name,
)

# Find PFT (optional user modifications) based on GBIF Family and Zanne Woodiness
file_name = ut.add_string_to_file_name(
    file_name_species_list, "__PFTFamilyWoodinessGBIF_Zanne"
)
species_pft_family_woodiness_gbif_zanne = get_species_pft_from_family_woodiness(
    species_list,
    species_family_gbif,
    species_woodiness_zanne,
    file_name,
)

# Find PFT (optional user modifications) based on GBIF Family and Combined Woodiness
file_name = ut.add_string_to_file_name(
    file_name_species_list, "__PFTFamilyWoodinessGBIF_Combined"
)
species_pft_family_woodiness_gbif_combined = get_species_pft_from_family_woodiness(
    species_list,
    species_family_gbif,
    species_woodiness_combined,
    file_name,
)

# Combine and resolve PFT from multiple sources (optional user modifications)
file_name = ut.add_string_to_file_name(file_name_species_list, "__PFTCombined")
species_pft_combined = species_pft_family_woodiness_try

species_pft_combined = resolve_species_info_dicts(
    "PFT",
    species_pft_combined,
    species_pft_family_woodiness_gbif_try,
)
species_pft_combined = resolve_species_info_dicts(
    "PFT",
    species_pft_combined,
    species_pft_family_woodiness_gbif_zanne,
)


# Combine all infos to one list, and write to file
all_species_infos = ut.add_infos_to_list(
    species_list_renamed,
    species_family_try,
    species_family_gbif,
    species_family_combined,
    species_woodiness_try,
    species_woodiness_zanne,
    species_woodiness_combined,
    species_pft_family_woodiness_try,
    species_pft_family_woodiness_gbif_try,
    species_pft_family_woodiness_gbif_zanne,
    species_pft_family_woodiness_gbif_combined,
    species_pft_combined,
)
file_name = ut.add_string_to_file_name(file_name_species_list, "__combined_infos")
ut.list_to_file(
    all_species_infos,
    [
        "Species",
        "Species Original",
        "Family TRY",
        "Family GBIF",
        "Family Combined",
        "Woodiness TRY",
        "Woodiness Zanne",
        "Woodiness Combined",
        "PFT Family_Woodiness TRY",
        "PFT Family_Woodiness GBIF_TRY",
        "PFT Family_Woodiness GBIF_Zanne",
        "PFT Family_Woodiness GBIF_Combined",
        "PFT Combined",
    ],
    file_name,
)
