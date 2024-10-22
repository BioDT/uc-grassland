"""
Module Name: assign_pfts.py
Description: Assign PFTs to species with the following options:
    - based on TRY categorical traits table,
    - based on GBIF taxonomic backbone for family, and growth form table for woodiness,
    - based on combination of both methods.

    For any option, species names can (and should) be adjusted by GBIF taxonomic backbone.

Developed in the BioDT project by Thomas Banitz (UFZ) with contributions by Franziska Taubert (UFZ),
Tuomas Rossi (CSC) and Taimur Haider Khan (UFZ).

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

Data sources:
    TRY categorical traits table:
    - Kattge J., Bönisch G., Günther A., Wright I., Zanne A., Wirth C., Reich P.B. and the TRY Consortium (2012):
      TRY - Categorical Traits Dataset. Data from: TRY - a global database of plant traits.
      TRY File Archive https://www.try-db.org/TryWeb/Data.php#3.
    - Website: https://doi.org/10.17871/TRY.3
    - Publication:
      Kattge J., Díaz S., Lavorel S., Prentice I., Leadley P., et al. (2011):
      TRY - a global database of plant traits.
      Global Change Biology 17: 2905-2935. https://doi.org/10.1111/j.1365-2486.2011.02451.x
    - Table redistributed without changes at:
      http://opendap.biodt.eu/grasslands-pdt/speciesMappingLookupTables/

    GBIF taxonomic backbone:
    - GBIF Secretariat (2023):
      GBIF Backbone Taxonomy. Checklist dataset.
    - Website: https://doi.org/10.15468/39omei
    - Access via GBIF Application Program Interface (API):
        - URL: https://api.gbif.org/
        - Documentation: https://techdocs.gbif.org/en/openapi/
        - Python package 'pygbif': https://github.com/gbif/pygbif

    Growth form table:
    - Will Cornwell (2019).
      traitecoevo/growthform v0.2.3 (v0.2.3).
      Zenodo. https://doi.org/10.5281/zenodo.2543013
    - Supplement to: https://github.com/traitecoevo/growthform/tree/v0.2.3
    - Table redistributed without changes at:
      http://opendap.biodt.eu/grasslands-pdt/speciesMappingLookupTables/
    - Source of "woodiness" column (the information used in this script):
      Zanne A.E., Tank D.C., Cornwell W.K., Eastman J.M., Smith S.A., et al. (2014):
      Three keys to the radiation of angiosperms into freezing environments.
      Nature 506: 89-92. https://doi.org/10.1038/nature12872
"""

import shutil
import time
import warnings
from pathlib import Path

import pandas as pd
import utils as ut
from pygbif import species

# def combine_info_strings(info_1, info_2):
#     """
#     Combine infos for a species.

#     Parameters:
#         info_1 (str): First info entry.
#         info_2 (str): Second info entry.

#     Returns:
#         str: Combined info entry.
#     """
#     info_1_core = ut.replace_substrings(info_1, ["(", ")", "conflicting "], "")
#     info_2_core = ut.replace_substrings(info_2, ["(", ")", "conflicting "], "")

#     # Allow combination without conflict of infos that can be woody
#     woody_infos = [
#         "woody",
#         "tree",
#         "shrub",
#         "shrub/tree",
#         "legume?",
#         "legume?/tree",
#         "legume?/shrub",
#         "legume?/shrub/tree",
#     ]

#     # Return one info, if it already contains the other info
#     if info_1_core in info_2_core:
#         return info_2
#     elif info_2_core in info_1_core:
#         return info_1
#     else:
#         info_both = sorted((info_1_core, info_2_core))

#         # Combine without conflict, if both infos are woody (PFT or Woodiness)
#         if info_1_core in woody_infos and info_2_core in woody_infos:
#             return f"({info_both[0]}/{info_both[1]})"
#         # Combine as conflicting otherwise
#         else:
#             return f"conflicting ({info_both[0]} vs. {info_both[1]})"


def resolve_species_infos(
    spec, info_name, info_1, info_2, *, warn_duplicates=False, warn_conflict=True
):
    """
    Resolve conflicting infos for a species.

    Parameters:
        spec (str): Species for which infos are being resolved.
        info_name (str): Information name ('PFT' or 'Woodiness' or 'Family').
        info_1 (str): First info entry.
        info_2 (str): Second info entry.
        warn_duplicates (bool): Throw warnings for resolving duplicate entries (default is False).
        warn_conflict (bool): Throw warnings for conflicting entries (default is True).

    Returns:
        str: Resolved info entry.
    """
    # Warning for duplicate species
    if warn_duplicates:
        warnings.warn(f"Duplicate species entry found for species '{spec}'.")

    # Check if the infos are the same, no need to change the info
    if info_1 == info_2:
        info_resolved = info_1

        if warn_duplicates:
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
            info_resolved = ut.combine_info_strings(info_1, info_2)

            # Warn for two conflicting assigned infos
            if warn_conflict and info_resolved.startswith("conflicting "):
                warnings.warn(
                    f"Assigned {info_name} for species {spec} from duplicate entries is {info_resolved}."
                )
                warn_duplicates = False
        if warn_duplicates:
            print(
                f"{info_name} differs: '{info_1}' vs. '{info_2}'. Keeping the {info_name} '{info_resolved}'."
            )

    return info_resolved


def resolve_species_info_dicts(
    info_name,
    info_dict_1,
    info_dict_2,
    *,
    ask_user_input=False,
    info_source_1="source 1 not specied",
    info_source_2="source 2 not specied",
):
    """
    Resolve conflicting info entries for all species from two dictionaries.

    Parameters:
        info_name (str): Information name ('PFT' or 'Woodiness' of 'Family').
        info_dict_1 (dict): First dictionary mapping species to information entries.
        info_dict_2 (dict): Second dictionary mapping species to information entries.
        ask_user_input (bool): Ask user for manual input of unclear infos (default is False).

    Returns:
        dict: Dictionary with resolved information entries for each species.
    """
    print(
        f"Combining {info_name} information from '{info_source_1}' and '{info_source_2}' dictionaries ..."
    )
    resolved_dict = {}

    # Iterate over keys present in both dictionaries and resolve infos
    common_keys = set(info_dict_1.keys()) & set(info_dict_2.keys())

    for spec in common_keys:
        resolved_dict[spec] = resolve_species_infos(
            spec,
            info_name,
            info_dict_1[spec],
            info_dict_2[spec],
            warn_duplicates=False,
        )

    # Add entries present only in one of the dictionaries
    for spec in set(info_dict_1.keys()) - common_keys:
        resolved_dict[spec] = info_dict_1[spec]

    for spec in set(info_dict_2.keys()) - common_keys:
        resolved_dict[spec] = info_dict_2[spec]

    # Sort and check for unclear infos
    resolved_dict = dict(sorted(resolved_dict.items()))
    resolved_dict = check_unclear_infos(
        info_name, resolved_dict, ask_user_input=ask_user_input
    )
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
        return ["woody", "herbaceous", "(fern)", "(lichen)", "(moss)"]
    elif info_name == "Family":
        return ["any"]
    else:
        raise ValueError(
            "Unsupported species information type. Supported types are 'PFT' and 'Woodiness'."
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
            info, ["H", "herb", "graminoid", "non-woody"], "herbaceous", at_end=True
        )
        info = ut.replace_substrings(
            info, ["NA", "non-woody/woody", "variable"], "not assigned", at_end=True
        )
        info = ut.replace_substrings(info, "fern", "(fern)", at_end=True)
        info = ut.replace_substrings(info, "lichen", "(lichen)", at_end=True)
        info = ut.replace_substrings(info, "moss", "(moss)", at_end=True)

    if not info:
        info = "not assigned"

    return info


def read_species_info_dict(
    file_name,
    info_name,
    *,
    species_column=0,
    info_column=None,
    header_lines=1,
    new_file="",
):
    """
    Read a dictionary from a text file containing species and a corresponding information (PFT or Woodiness).

    Parameters:
        file_name (str): Path to the text file.
        info_name (str): Information name ('PFT' or 'Woodiness' or 'Family').
        species_column(str or int): Species column identifier (name as string or index)
        info_column (int): Information column identifier (name as string or index, default is None for using info_name).
        header_lines (int): Number of header lines to skip (default is 1).
        new_file (str): Path of new file to save the dictionary (default is "", to not save).
        lookup_source (str): Source of the lookup table for new file name (default is "Original").

    Returns:
        dict: Dictionary where species names are keys, and infos are values.

    Raises:
        ValueError: If unsupported species info_name is used.
    """
    valid_infos = get_valid_infos(info_name)
    print(f"Reading {info_name} lookup table from '{file_name}' ...")

    # Search for 'info_name' as column name if not specified otherwise
    if info_column is None:
        info_column = info_name

    # Open file for reading
    with open(file_name, "r") as file:
        species_info_dict = {}
        processed_lines = 0
        last_header_line = None

        # Skip header lines
        for _ in range(header_lines):
            last_header_line = next(file)

        # Get column names from last header line, find species and info columns
        column_names = [last_header_line.rstrip("\n").split("\t", -1)]
        species_column = ut.find_column_index(column_names, species_column)
        info_column = ut.find_column_index(column_names, info_column)

        # Split each line into columns (tab as delimiter), get species and info from columns
        for line_number, line in enumerate(file, start=header_lines + 1):
            columns = line.rstrip("\n").split("\t", -1)
            spec, info = (columns[species_column], columns[info_column])
            info = replace_info_strings(info, info_name)

            # Warning if info is not valid and not "not assigned"
            if (
                not (valid_infos == ["any"] and info != "")
                and info not in valid_infos
                and not info.startswith(("not assigned", "conflicting"))
            ):
                warnings.warn(
                    f"Invalid {info_name} found on line {line_number} for {spec}: '{info}'."
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

    # Sort dictionary by species keys
    species_info_dict = dict(sorted(species_info_dict.items()))
    print(f"Processed {processed_lines} lines.")
    print(f"Final {info_name} lookup table has {len(species_info_dict)} entries.")

    # Save created dictionary to new file if file is provided
    if new_file:
        ut.dict_to_file(species_info_dict, ["Species", info_name], new_file)

    return species_info_dict


def gbif_request(spec, *, kingdom="plants", attempts=5, delay=2):
    """
    Request species information from GBIF taxonomic backbone.

    Parameters:
        spec (str): Species name to look up in the GBIF taxonomic backbone.
        kingdom (str): Kingdom to search for (default is "plants").
        attempts (int): Number of attempts to make (default is 5).
        delay (int): Delay between attempts in seconds (default is 2).
    """
    while attempts > 0:
        attempts -= 1
        try:
            spec_gbif_dict = species.name_backbone(name=spec, kingdom=kingdom)
            return spec_gbif_dict
        except Exception as e:
            print(f"GBIF request failed {e}.")

            if attempts > 0:
                print(f"Retrying in {delay} seconds ...")
                time.sleep(delay)

    # After exhausting all attempts
    warnings.warn(
        f"GBIF request for species '{spec}' failed repeatedly. Returning 'not found'."
    )
    return "not found"


def get_gbif_species(spec, accepted_ranks=["GENUS"]):
    """
    Retrieve a species name or higher rank from the GBIF taxonomic backbone.

    Parameters:
        spec (str): Species name to look up in the GBIF taxonomic backbone.
        accepted_ranks (list): List of taxonomic ranks above SPECIES that can be used as new species entry (default is ["GENUS"]).

    Returns:
        str: Matched or suggested species name from GBIF, or the original species name if no match is found.
    """
    spec_gbif_dict = gbif_request(spec)

    if spec_gbif_dict == "not found":
        return spec
    elif spec_gbif_dict["matchType"] == "NONE":
        # No match, return input species
        warnings.warn(f"'{spec}' not found.")

        return spec
    elif spec_gbif_dict["rank"] == "SPECIES":
        if "species" in spec_gbif_dict:
            # Use 'species' entry
            spec_match = spec_gbif_dict["species"]

            if spec_match != spec:
                print(f"'{spec}' replaced with GBIF SPECIES '{spec_match}'.")
        else:
            # No 'species' entry, use 'canonicalName' entry (should not happen)
            spec_match = spec_gbif_dict["canonicalName"]
            warnings.warn(f"'{spec}' not exactly identified by GBIF.")
            print(
                f"SURPRISE: Result rank is SPECIES, but no species entry. Using CANONICALNAME '{spec_match}'."
            )
            if spec_match != spec:
                print(f"'{spec}' replaced with GBIF CANONICALNAME '{spec_match}'.")
    elif spec_gbif_dict["rank"] == "SUBSPECIES":
        # seperated for testing, could be merged with "SPECIES" case later
        if "species" in spec_gbif_dict:
            # Use 'species' entry
            spec_match = spec_gbif_dict["species"]

            if spec_match != spec:
                print(f"'{spec}' SUBSPECIES replaced with GBIF SPECIES '{spec_match}'.")
        else:
            # No 'species' entry, use 'canonicalName' entry (should not happen)
            spec_match = spec_gbif_dict["canonicalName"]
            warnings.warn(f"'{spec}' not exactly identified by GBIF.")
            print(
                f"SURPRISE: Result rank is SUBSPECIES, but no species entry. Using CANONICALNAME '{spec_match}'."
            )
            if spec_match != spec:
                print(f"'{spec}' replaced with GBIF CANONICALNAME '{spec_match}'.")
    elif "canonicalName" in spec_gbif_dict:
        # No exact match, use 'canonicalName' entry
        spec_match = spec_gbif_dict["canonicalName"]
        warnings.warn(f"'{spec}' not exactly identified by GBIF.")

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
        spec (str): Species name to find family.

    Returns:
        str: Family information or "not found."
    """
    spec_gbif_dict = gbif_request(spec)

    if "family" in spec_gbif_dict:
        return spec_gbif_dict["family"]
    else:
        warnings.warn(f"Family for '{spec}' not found by GBIF.")
        return "not found"


# def get_gbif_dict(species_info_dict, file_name="", info_name="PFT"):
#     """
#     Screen and correct species-info lookup table with GBIF taxonomic backbone.

#     Parameters:
#         species_info_dict (dict): Dictionary where species names are keys, and infos are values.
#         info_name (str): Information name ('PFT' or 'Woodiness', default is 'PFT').

#     Returns:
#         dict: Processed dictionary where species names are keys, and values are dictionaries with keys:
#             info_name('PFT' or 'Woodiness'): corresponding species info.
#             'originalNames': List of species names from input dictionary (that were replaced or not).
#     """
#     print("Searching for species in GBIF taxonomic backbone ...")
#     species_info_dict_gbif = {}
#     processed_lines = 0

#     for spec, info in species_info_dict.items():
#         spec_match = get_gbif_species(spec, accepted_ranks=["GENUS", "FAMILY"])

#         if (
#             spec_match != spec
#             and not info_name == "Family"  # Keep family infos
#             and spec_match.endswith(" species")
#             and "grass" not in info  # Keep all infos with "grass", also conflicts
#         ):
#             info = "not assigned"

#         # Check if (replaced) species name is already in lookup table
#         if spec_match in species_info_dict_gbif:
#             # Check info for existing species
#             species_info_dict_gbif[spec_match][info_name] = resolve_species_infos(
#                 spec_match,
#                 info_name,
#                 info,
#                 species_info_dict_gbif[spec_match][info_name],
#             )
#             species_info_dict_gbif[spec_match]["originalNames"].append(spec)
#         else:
#             # Add new species, info and replaced species name to lookup table
#             species_info_dict_gbif[spec_match] = {
#                 info_name: info,
#                 "originalNames": [spec],
#             }

#         processed_lines += 1

#     # Sort dictionary by species keys
#     species_info_dict_gbif = dict(sorted(species_info_dict_gbif.items()))
#     print(f"Processed {processed_lines} lines.")
#     print(f"Final {info_name} lookup table has {len(species_info_dict_gbif)} entries.")

#     # Save created dictionary to new file
#     if file_name:
#         ut.dict_to_file(
#             species_info_dict_gbif, ["Species", info_name, "Original names"], file_name
#         )

#     return species_info_dict_gbif


def get_pft_from_family_woodiness(spec, family_dict, woodiness_dict):
    """
    Determine PFT based on species family and woodiness.

    Parameters:
        spec (str): Species name to find PFT.
        family_dict (dict): Dictionary where species names are keys, and family infos are values.
        woodiness_dict (dict): Dictionary where species names are keys, and woodiness infos are values.

    Returns:
        str: PFT info or "not assigned."
    """
    # Get family or throw warning if not found
    if spec in family_dict:
        family = family_dict[spec]
    else:
        warnings.warn(f"Family for '{spec}' not found in lookup table.")
        family = "not found"

    # Get woodiness or throw warning if not found
    if spec in woodiness_dict:
        woodiness = woodiness_dict[spec]
    else:
        warnings.warn(f"Woodiness for '{spec}' not found in lookup table.")
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


def read_species_list(
    file_name,
    *,
    species_column=0,
    extra_columns=[],
    header_lines=1,
    check_gbif=True,
    save_new_file=True,
    new_suffix=None,
    add_species_column_copy=True,
    combine_differing_entries=False,
    csv_delimiter=";",
):
    """
    Read species names and, optionally, additional info from a file, and, optionally,
    check/correct species names with GBIF taxonomic backbone

    Parameters:
        file_name (str): Name of the file containing the species names.
        species_column (str or int): Species name column name or number (0-based index, default is 0).
        extra_columns (list of str or int): Additional columns to include in the list (default is empty list).
        header_lines (int): Number of header line, lines before will be skipped (default is 1).
        check_gbif (bool): Check/correct species names with GBIF taxonomic backbone (default is True).
        save_new_file (bool): Save species names (and info) retrieved to new file (default is True).
        new_suffix (str): Suffix for new file type (default is None for keeping the original file type).
        add_species_column_copy (bool): Add a copy of the original species column as a new first column to the output file (default is True).
        combine_differing_entries (bool): Combine differing entries (with same info in first column) into one (default is False).
        csv_delimiter (str): Delimiter for CSV files (default is ',').

    Returns:
        list: List of unique species names, and additional info if requested and found.
    """
    # Convert file_path to a Path object if it is not already
    file_name = Path(file_name)
    file_extension = file_name.suffix.lower()
    print(f"Reading species list from '{file_name}' ...")

    if file_extension == ".xlsx":
        try:
            df = pd.read_excel(file_name, header=header_lines - 1)
        except Exception as e:
            print(f"Error reading .xlsx file: {e}.")
            return []

        # Determine species name column index
        column_indexes = [ut.find_column_index(df, species_column)]

        for col_name in extra_columns:
            try:
                column_indexes.append(ut.find_column_index(df, col_name))
            except (KeyError, ValueError):
                warnings.warn(
                    f"Failed to find column '{col_name}'. Omitted in species list."
                )

        # Extract species names from specified columns
        species_list = df.iloc[:, column_indexes].values.tolist()
    elif file_extension == ".csv":
        try:
            df = pd.read_csv(
                file_name,
                header=header_lines - 1,
                encoding="ISO-8859-1",
                delimiter=csv_delimiter,
            )
        except Exception as e:
            print(f"Error reading .csv file: {e}.")
            return []

        # Determine species name column index
        column_indexes = [ut.find_column_index(df, species_column)]

        for col_name in extra_columns:
            try:
                column_indexes.append(ut.find_column_index(df, col_name))
            except (KeyError, ValueError):
                warnings.warn(
                    f"Failed to find column '{col_name}'. Omitted in species list."
                )

        # Extract species names from specified columns
        species_list = df.iloc[:, column_indexes].values.tolist()
    elif file_extension == ".txt":
        try:
            with open(file_name, "r") as file:
                species_data = [line.strip().split("\t") for line in file]
        except Exception as e:
            print(f"Error reading text file: {e}.")
            return []

        # Determine species name column index
        column_indexes = [ut.find_column_index(species_data, species_column)]

        for col_name in extra_columns:
            try:
                column_indexes.append(ut.find_column_index(species_data, col_name))
            except (KeyError, ValueError):
                warnings.warn(
                    f"Failed to find column '{col_name}'. Omitted in species list."
                )

        try:
            species_list = [
                [line[idx] for idx in column_indexes]
                for line in species_data[header_lines:]
            ]
        except IndexError as e:
            print(f"Error processing line: {e}. Returning empty list.")
            return []
    else:
        raise ValueError("Unsupported file format! Must be '.xlsx', '.txt', or '.csv'.")

    # Reduce list to unique entries only
    species_list = ut.sort_and_cleanup_list(
        species_list, combine_differing_entries=combine_differing_entries
    )

    # GBIF check and correction if selected
    if check_gbif:
        print("Searching for species in GBIF taxonomic backbone ...")
        species_list_renamed = []

        for entry in species_list:
            spec = entry if isinstance(entry, str) else entry[0]
            spec_renamed = get_gbif_species(spec, accepted_ranks=["GENUS", "FAMILY"])
            species_list_renamed.append(
                [spec_renamed] + (entry if isinstance(entry, list) else [entry])
            )

        # Save GBIF corrected species list to file
        if save_new_file:
            file_name = ut.add_string_to_file_name(
                file_name, "__Species__GBIF_corrected", new_suffix=new_suffix
            )
            ut.list_to_file(
                species_list_renamed,
                ["Species GBIF", "Species Original"] + extra_columns,
                file_name,
            )

        # Overwrite species_list with GBIF correction for empty/duplicate count below
        species_list = [entry[0] for entry in species_list_renamed]
    else:
        if add_species_column_copy:
            # No renaming, just add identical column
            species_list_renamed = [
                [entry[0]] + entry if isinstance(entry, list) else [entry, entry]
                for entry in species_list
            ]
            first_columns = ["Species (uncorrected)", "Species Original"]
        else:
            species_list_renamed = species_list
            first_columns = ["Species Original"]

        if save_new_file:
            file_name = ut.add_string_to_file_name(
                file_name, "__Species__Original", new_suffix=new_suffix
            )
            ut.list_to_file(
                species_list_renamed,
                first_columns + extra_columns,
                file_name,
            )

    # No removal of 'nan' or duplicate species entries in renamed list, assigned infos to be matched with original list later
    empty_strings = species_list.count("")
    print(
        f"Species list has {len(species_list)} entries, including {empty_strings} empty entries."
    )

    if not combine_differing_entries:
        duplicates = ut.count_duplicates(species_list)

        if len(duplicates) > 0:
            print("Duplicates: ", end="")
            print(
                ", ".join([f"'{spec}' ({count})" for spec, count in duplicates.items()])
            )

    return species_list_renamed


def user_input_info(info_dict, info_name, start_string):
    """
    Iterate through species without info assigned and prompt user to select a new info.

    Parameters:
        info_dict (dict): Dictionary with species names as keys and corresponding infos.
        info_name (str): Information name ('PFT' or 'Woodiness').
        start_string (string): Beginning of infos that get suggested for reassignment.

    Returns:
        dict: Modified dictionary with updated infos based on user input.
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

    for spec, info in info_dict.items():
        if bool(spec) and info.startswith(start_string):
            print(f"Species: {spec}. Current {info_name}: '{info}'.")
            user_choice = input(
                f"Enter your choice ({choice_string}{index + 1} Skip {index + 2} Exit): "
            )

            try:
                user_choice = int(user_choice)
            except ValueError:
                print(f"Invalid choice. Leaving {info_name} as is.")
            else:
                if 1 <= user_choice <= len(valid_choices):
                    user_info = f"{valid_choices[user_choice - 1]} (user input)"
                    info_dict[spec] = user_info
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

    return info_dict


def check_unclear_infos(info_name, info_dict, *, ask_user_input=True):
    """
    Check for species with unclear information entries in a dictionary.

    Parameters:
        info_name (str): Information name ('PFT' or 'Woodiness').
        info_dict (dict): Dictionary mapping species to information entries.
        ask_user_input (bool): Ask user for manual input of unclear infos (default is True).

    Returns:
        dict: Updated dictionary after resolving unclear information entries manually (if requested).
    """
    unclear_info_strings = ["not found", "not assigned", "variable"]

    for unclear_info in unclear_info_strings:
        count_unclear = sum(
            bool(spec) and info.startswith(unclear_info)
            for spec, info in info_dict.items()
        )

        if count_unclear:
            # Inform about unclear infos
            print(f"Species with {info_name} '{unclear_info}': {count_unclear}.")

            if ask_user_input:
                # Ask user if species with unclear info shall be modified manually
                manual_input = input(
                    "Do you want to make manual inputs for these species? (y/n): "
                ).lower()

                if manual_input == "y":
                    info_dict = user_input_info(info_dict, info_name, unclear_info)

    return info_dict


def return_as_list_or_dict(
    info_name, species_list, info_dict, *, return_as_list=False, file_name=None
):
    if return_as_list:
        # New list of species and infos, allowing for duplicates and preserving order
        species_info_list = ut.add_info_to_list(species_list, info_dict)

        if file_name:
            ut.list_to_file(species_info_list, ["Species", info_name], file_name)

        return species_info_list
    else:
        # Sort, save and return species info dictionary
        info_dict = dict(sorted(info_dict.items()))

        if file_name:
            ut.dict_to_file(info_dict, ["Species", info_name], file_name)

        return info_dict


def get_species_info(
    species_list,
    info_lookup,
    info_name,
    *,
    file_name="",
    lookup_source="source not specified",
    return_as_list=False,
    ask_user_input=False,
):
    """
    Create a dict or list with species and corresponding infos from a species-info lookup table,
    and save to file.

    Parameters:
        species_list (list): List of species names.
        info_lookup (dict): Dictionary with species names as keys and corresponding infos.
        info_name (str): Information name ('PFT' or 'Woodiness').
        file_name (str): File name to save the result (empty string to skip saving).
        return_as_list(bool): Return as a list, otherwise as a dict (default is False).
        ask_user_input (bool): Ask user for manual input of unclear infos (default is False).

    Returns:
        dict or list: Dict or list of pairs of the species names and corresponding infos.
    """
    print(
        f"Searching for species' {info_name} in '{lookup_source}' lookup table ..." f" "
    )

    # Convert info_lookup to dictionary of only infos if not already
    info_lookup = ut.reduce_dict_to_single_info(info_lookup, info_name)

    # Read info from lookup dict if available
    info_dict = {}

    for spec in species_list:
        if spec not in info_dict:
            info_dict[spec] = ut.lookup_info_in_dict(spec, info_lookup)

    # Check for unclear infos and get result (list or dict)
    info_dict = check_unclear_infos(info_name, info_dict, ask_user_input=ask_user_input)
    species_info_result = return_as_list_or_dict(
        info_name,
        species_list,
        info_dict,
        return_as_list=return_as_list,
        file_name=ut.add_string_to_file_name(
            file_name, f"__{info_name.lower()}_{lookup_source}"
        ),
    )
    return species_info_result


def get_species_family_gbif(species_list, *, file_name="", return_as_list=False):
    """
    Retrieve families for a list of species using GBIF taxonomic backbone.

    Parameters:
        species_list (list): List of species names.
        file_name (str): File name to save the result (empty string to skip saving).
        return_as_list(bool): Return as a list, otherwise as a dict (default is False).

    Returns:
        dict or list: Resulting dictionary or list with species and their Family information.
    """
    info_name = "Family"
    print("Searching for species' Family in GBIF taxonomic backbone ...")
    info_dict = {}

    for spec in species_list:
        if spec not in info_dict:
            info_dict[spec] = get_gbif_family(spec)

    # Get result (list or dict)
    species_info_result = return_as_list_or_dict(
        info_name,
        species_list,
        info_dict,
        return_as_list=return_as_list,
        file_name=ut.add_string_to_file_name(file_name, "__family_GBIF"),
    )
    return species_info_result


def get_species_pft_from_family_woodiness(
    species_list,
    family_dict,
    woodiness_dict,
    *,
    file_name="",
    lookup_source_family="family source not specified",
    lookup_source_woodiness="woodiness source not specified",
    return_as_list=False,
    ask_user_input=False,
):
    """
    Get PFT for a list of species based on family and woodiness.

    Parameters:
        species_list (list): List of species names.
        family_dict (dict): Dictionary mapping species to their families.
        woodiness_dict (dict): Dictionary mapping species to their woodiness.
        file_name (str): File name to save the result (empty string to skip saving).
        return_as_list(bool): Return as a list, otherwise as a dict (default is False).
        ask_user_input (bool): Ask user for manual input of unclear infos (default is False).

    Returns:
        dict or list: Resulting dictionary or list with species and their PFT information.
    """
    info_name = "PFT"
    print(
        f"Obtaining species' {info_name} from lookup tables, "
        f"Family: '{lookup_source_family}' and Woodiness: '{lookup_source_woodiness}' ..."
    )
    info_dict = {}

    for spec in species_list:
        if spec not in info_dict:
            info_dict[spec] = get_pft_from_family_woodiness(
                spec, family_dict, woodiness_dict
            )

    # Check for unclear infos and get result (list or dict)
    info_dict = check_unclear_infos(info_name, info_dict, ask_user_input=ask_user_input)
    species_info_result = return_as_list_or_dict(
        info_name,
        species_list,
        info_dict,
        return_as_list=return_as_list,
        file_name=ut.add_string_to_file_name(
            file_name,
            f"__{info_name}_family_{lookup_source_family}_woodiness_{lookup_source_woodiness}",
        ),
    )
    return species_info_result


def get_lookup_tables(lookup_folder_name, *, force_create=False, cache=None):
    """
    Get lookup tables from cache or opendap, create if not found.

    Parameters:
        lookup_folder_name (str): Name of subfolder containing and/or receiving lookup tables.
        force_create (bool): Force creation of new lookup tables (default is False).
        cache (str): Path to local folder containing and/or receiving lookup tables (default is None).
    """
    lookup_tables = {}
    lookup_table_specs = {
        "TRY_Family": {
            "file_name": "TRY_Categorical_traits__Family__GBIF_corrected.txt",
            "info_name": "Family",
            "found": False,
            "raw_file_opendap": "TRY_Categorical_Traits_Lookup_Table_2012_03_17_TestRelease.xlsx",
            "raw_file": "TRY_Categorical_traits.xlsx",
            "raw_species_column": "AccSpeciesName",
            "raw_info_columns": ["Family", "Woodiness"],
        },
        "TRY_Woodiness": {
            "file_name": "TRY_Categorical_traits__Woodiness__GBIF_corrected.txt",
            "info_name": "Woodiness",
            "found": False,
            "raw_file_opendap": "TRY_Categorical_Traits_Lookup_Table_2012_03_17_TestRelease.xlsx",
            "raw_file": "TRY_Categorical_traits.xlsx",
            "raw_species_column": "AccSpeciesName",
            "raw_info_columns": ["Family", "Woodiness"],
        },
        "Zanne_Woodiness": {
            "file_name": "Zanne_Growth_form__Woodiness__GBIF_corrected.txt",
            "info_name": "Woodiness",
            "found": False,
            "raw_file_opendap": "growth_form.csv",
            "raw_file": "Zanne_Growth_form.csv",
            "raw_species_column": "sp",
            "raw_info_columns": ["Woodiness"],
        },
    }

    # Define folder where lookup tables are expected, and will be stored
    lookup_folder = (
        ut.get_package_root() / lookup_folder_name if cache is None else Path(cache)
    )

    if not force_create:
        for table_name, table_info in lookup_table_specs.items():
            table_file = lookup_folder / table_info["file_name"]

            if not table_file.is_file():
                ut.download_file_opendap(
                    table_info["file_name"], lookup_folder_name, lookup_folder
                )

            if table_file.is_file():
                # Use local lookup tables, if found
                lookup_tables[table_name] = read_species_info_dict(
                    table_file, table_info["info_name"]
                )
                lookup_table_specs[table_name]["found"] = True

    # Create missing lookup tables (i.e. all in case of force_create) from raw tables
    for table_name, table_info in lookup_table_specs.items():
        if not table_info["found"]:
            # Create lookup table from raw file
            raw_file = lookup_folder / table_info["raw_file"]
            raw_list_file = ut.add_string_to_file_name(
                raw_file, "__Species__GBIF_corrected", new_suffix=".txt"
            )

            if not raw_list_file.is_file():
                if not raw_file.is_file():
                    # Download raw file from opendap, rename to standard name
                    ut.download_file_opendap(
                        table_info["raw_file_opendap"],
                        lookup_folder_name,
                        lookup_folder,
                        new_file_name=table_info["raw_file"],
                    )

                if raw_file.is_file():
                    print(
                        f"'{table_name}' source file found. Reading species infos from '{raw_file}' ..."
                    )
                else:
                    raise FileNotFoundError(
                        f"'{table_name}' source file '{table_info['raw_file']}' not found!"
                    )

                # Process raw source file with info column(s) to .txt file
                read_species_list(
                    raw_file,
                    species_column=table_info["raw_species_column"],
                    extra_columns=table_info["raw_info_columns"],
                    check_gbif=True,
                    save_new_file=True,
                    new_suffix=".txt",
                    add_species_column_copy=False,
                    combine_differing_entries=True,
                    csv_delimiter=",",
                )

            if raw_list_file.is_file():
                # Get lookup table from raw list in .txt file, and save to file
                lookup_tables[table_name] = read_species_info_dict(
                    raw_list_file,
                    table_info["info_name"],
                    species_column=0,
                    new_file=lookup_folder / table_info["file_name"],
                )
            else:
                raise FileNotFoundError(
                    f"File '{raw_list_file}' not found. Cannot retrieve '{table_name}'!"
                )

    return lookup_tables


def get_all_infos_and_pft(
    input_file,
    species_column,
    lookup_tables,
    *,
    extra_columns=[],
    save_single_files=True,
    csv_delimiter=";",
):
    """
    Get and combine Family and Woodiness information for a list of species, from various lookup tables and sources,
    and assign Plant Functional Types (PFT) based on family and woodiness.

    Parameters:
        input_file (str or Path): Path to the input file containing species list.
        species_column (str): The column name in the input file that contains species names.
        extra_columns (list, optional): Additional columns to include from the input file (default is empty list).
        lookup_folder (Path, optional): Path to the folder containing lookup tables (relative to package root, default is 'speciesMappingLookupTables').
        save_single_files (bool, optional): Whether to save intermediate results to separate files (default is False).

    Returns:
        list: List of processed species information, with family, woodiness, and derived PFT from various sources.
        dict: Dictionary of species PFT, as derived and combined from various sources.
    """
    # Read species list
    input_file = Path(input_file)
    species_list = read_species_list(
        input_file,
        species_column=species_column,
        extra_columns=extra_columns,
        save_new_file=save_single_files,
        csv_delimiter=csv_delimiter,
    )

    # Use first column of renamed list only for subsequent lookup of infos
    # (list can have original species names and more infos in additional columns)
    species_to_lookup = [entry[0] for entry in species_list]
    species_original = [entry[1] for entry in species_list]

    # Find Family infos based on sources, write to files if requested
    file_name = input_file if save_single_files else None
    family_try = get_species_info(
        species_to_lookup,
        lookup_tables["TRY_Family"],
        "Family",
        file_name=file_name,
        lookup_source="TRY",
    )
    family_gbif = get_species_family_gbif(species_to_lookup, file_name=file_name)
    family_extra_found = False

    # Scan extra columns if they contain family information
    for col_index, col_name in enumerate(extra_columns):
        if "family" in col_name.lower():
            # Family extra dict needs to work with original species names as keys (entry[1]),
            # because GBIF names can be the same for different original species, but
            # the extra column can contain different family information for them
            print(f"Extra column found with family information: '{col_name}'.")
            family_extra_found = True
            family_extra = {entry[1]: entry[col_index + 2] for entry in species_list}

            # Replace empty entries and entries of several terms separated by " / " with std format
            for key, value in family_extra.items():
                if value == "":
                    family_extra[key] = "not found"
                elif isinstance(value, str) and " / " in value:
                    family_extra[key] = "conflicting ("

                    for item in value.split(" / "):
                        family_extra[key] = (
                            family_extra[key] + f"{item.split(' / ')[0]} vs. "
                        )

                    family_extra[key] = ut.replace_substrings(
                        family_extra[key], " vs. ", ")", at_end=True
                    )

            ut.dict_to_file(
                family_extra,
                ["Species", "Family"],
                ut.add_string_to_file_name(file_name, "__Family_Extra"),
            )

    # Combine and resolve Family from both sources (TRY & GBIF)
    family_combined = resolve_species_info_dicts(
        "Family", family_try, family_gbif, info_source_1="TRY", info_source_2="GBIF"
    )

    # Find Woodiness infos based on sources, write to files if requested
    woodiness_try = get_species_info(
        species_to_lookup,
        lookup_tables["TRY_Woodiness"],
        "Woodiness",
        file_name=file_name,
        lookup_source="TRY",
    )
    woodiness_zanne = get_species_info(
        species_to_lookup,
        lookup_tables["Zanne_Woodiness"],
        "Woodiness",
        file_name=file_name,
        lookup_source="Zanne",
    )

    # Combine and resolve Woodiness from both sources (TRY & Zanne)
    woodiness_combined = resolve_species_info_dicts(
        "Woodiness",
        woodiness_try,
        woodiness_zanne,
        info_source_1="TRY",
        info_source_2="Zanne",
    )

    # Find PFT based on differnt combinations of Family and Woodiness sources
    pft_family_try_woodiness_try = get_species_pft_from_family_woodiness(
        species_to_lookup,
        family_try,
        woodiness_try,
        file_name=file_name,
        lookup_source_family="TRY",
        lookup_source_woodiness="TRY",
    )
    pft_family_gbif_woodiness_try = get_species_pft_from_family_woodiness(
        species_to_lookup,
        family_gbif,
        woodiness_try,
        file_name=file_name,
        lookup_source_family="GBIF",
        lookup_source_woodiness="TRY",
    )
    pft_family_gbif_woodiness_zanne = get_species_pft_from_family_woodiness(
        species_to_lookup,
        family_gbif,
        woodiness_zanne,
        file_name=file_name,
        lookup_source_family="GBIF",
        lookup_source_woodiness="Zanne",
    )
    pft_family_gbif_woodiness_combined = get_species_pft_from_family_woodiness(
        species_to_lookup,
        family_gbif,
        woodiness_combined,
        file_name=file_name,
        lookup_source_family="GBIF",
        lookup_source_woodiness="Combined",
    )

    # Combine and resolve PFT from multiple sources
    pft_combined = resolve_species_info_dicts(
        "PFT",
        pft_family_try_woodiness_try,
        pft_family_gbif_woodiness_try,
        info_source_1="family_TRY_woodiness_TRY",
        info_source_2="family_GBIF_woodiness_TRY",
    )
    pft_combined = resolve_species_info_dicts(
        "PFT",
        pft_combined,
        pft_family_gbif_woodiness_zanne,
        info_source_1="Combined",
        info_source_2="family_GBIF_woodiness_Zanne",
    )

    # Treat extra family infos as additional source if found
    if not family_extra_found:
        # Create empty dict family_extra if not found
        family_extra = {key: "not found" for key in species_original}

    woodiness_combined_original_keys = {
        species_original[i]: woodiness_combined[species_to_lookup[i]]
        for i in range(len(species_to_lookup))
    }
    pft_combined_original_keys = {
        species_original[i]: pft_combined[species_to_lookup[i]]
        for i in range(len(species_to_lookup))
    }
    pft_family_extra_woodiness_combined = get_species_pft_from_family_woodiness(
        species_original,
        family_extra,
        woodiness_combined_original_keys,
        file_name=file_name,
        lookup_source_family="Extra",
        lookup_source_woodiness="Combined",
    )
    pft_combined_extra = resolve_species_info_dicts(
        "PFT",
        pft_combined_original_keys,
        pft_family_extra_woodiness_combined,
        info_source_1="Combined",
        info_source_2="family_Extra_woodiness_Combined",
    )

    if file_name:
        ut.dict_to_file(
            family_combined,
            ["Species", "Family Combined"],
            ut.add_string_to_file_name(file_name, "__family_Combined"),
        )
        ut.dict_to_file(
            woodiness_combined,
            ["Species", "Woodiness Combined"],
            ut.add_string_to_file_name(file_name, "__woodiness_Combined"),
        )
        ut.dict_to_file(
            pft_combined,
            ["Species", "PFT Combined"],
            ut.add_string_to_file_name(file_name, "__PFT_Combined"),
        )
        ut.dict_to_file(
            pft_combined_extra,
            ["Species", "PFT Combined incl. Extra"],
            ut.add_string_to_file_name(file_name, "__PFT_Combined_Extra"),
        )

    # Combine all infos to one list, and write to file
    all_infos = ut.add_columns_to_list(species_list, family_extra.values())
    all_infos = ut.add_infos_to_list(
        all_infos,
        family_try,
        family_gbif,
        family_combined,
        woodiness_try,
        woodiness_zanne,
        woodiness_combined,
        pft_family_try_woodiness_try,
        pft_family_gbif_woodiness_try,
        pft_family_gbif_woodiness_zanne,
        pft_family_gbif_woodiness_combined,
        pft_combined,
    )
    all_infos = ut.add_columns_to_list(
        all_infos, pft_family_extra_woodiness_combined.values()
    )
    all_infos = ut.add_columns_to_list(all_infos, pft_combined_extra.values())
    file_name = ut.add_string_to_file_name(
        input_file, "__PFT_all_infos", new_suffix=".csv"
    )
    column_headers = (
        ["Species", "Species Original"]
        + extra_columns
        + [
            "Family Extra (data source)",
            "Family TRY",
            "Family GBIF",
            "Family Combined (excl. Extra)",
            "Woodiness TRY",
            "Woodiness Zanne",
            "Woodiness Combined",
            "PFT Family TRY Woodiness TRY",
            "PFT Family GBIF Woodiness TRY",
            "PFT Family GBIF Woodiness Zanne",
            "PFT Family GBIF Woodiness Combined",
            "PFT Combined (excl. Extra)",
            "PFT Family Extra Woodiness Combined",
            "PFT Combined incl. Extra",
        ]
    )
    ut.list_to_file(all_infos, column_headers, file_name)

    return all_infos, pft_combined


def get_species_data_specs():
    """
    Get species data specifications for different sites with grassland observation data.

    Returns:
        dict: Dictionary with site IDs as keys and corresponding species data specifications:
            'name' (str): Site name.
            'species_file_names' (list): Files containing species lists.
            'species_columns' (list): Column names for species list in each file.
            'extra_columns' (list of lists): Additional columns to retrieve from the files.
    """

    species_data_specs_per_site = {
        "11696de6-0ab9-4c94-a06b-7ce40f56c964": {
            "name": "IT25 - Val Mazia/Matschertal",
            "species_file_names": ["IT_Matschertal_data_abund.csv"],
            "species_columns": ["TAXA"],
            "extra_columns": [[]],
        },
        "31e67a47-5f15-40ad-9a72-f6f0ee4ecff6": {
            "name": "LTSER Zone Atelier Armorique",
            "species_file_names": ["FR_AtelierArmorique_reference.csv"],
            "species_columns": ["NAME"],
            "extra_columns": [["CODE", "FAMILY_NAME"]],
        },
        "324f92a3-5940-4790-9738-5aa21992511c": {
            "name": "Stubai (combination of Neustift meadows and Kaserstattalm)",
            "species_file_names": ["AT_Stubai_data_abund.csv"],
            "species_columns": ["TAXA"],
            "extra_columns": [[]],
        },
        "3de1057c-a364-44f2-8a2a-350d21b58ea0": {
            "name": "Obergurgl",
            "species_file_names": [
                "AT_Obergurgl_reference.csv",
                "AT_Obergurgl_data.csv",
            ],
            "species_columns": ["NAME", "TAXA"],
            "extra_columns": [[], []],
        },
        "4ac03ec3-39d9-4ca1-a925-b6c1ae80c90d": {
            "name": "Hochschwab (AT-HSW) GLORIA",
            "species_file_names": [
                "AT_Hochschwab_reference.csv",
                "AT_Hochschwab_data_cover.csv",
                "AT_Hochschwab_data_abund.csv",
            ],
            "species_columns": ["NAME", "TAXA", "TAXA"],
            "extra_columns": [["CODE"], [], []],
        },
        "6ae2f712-9924-4d9c-b7e1-3ddffb30b8f1": {
            "name": "GLORIA Master Site Schrankogel (AT-SCH), Stubaier Alpen",
            "species_file_names": [
                "AT_Schrankogel_reference.csv",
                "AT_Schrankogel_data_cover.csv",
            ],
            "species_columns": ["NAME", "TAXA"],
            "extra_columns": [["CODE"], []],
        },
        "9f9ba137-342d-4813-ae58-a60911c3abc1": {
            "name": "Rhine-Main-Observatory",
            "species_file_names": ["DE_RhineMainObservatory_abund_data.csv"],
            "species_columns": ["TAXA"],
            "extra_columns": [[]],
        },
        "c85fc568-df0c-4cbc-bd1e-02606a36c2bb": {
            "name": "Appennino centro-meridionale: Majella-Matese",
            "species_file_names": ["IT_AppenninoCentroMeridionale_data_cover.csv"],
            "species_columns": ["TAXA"],
            "extra_columns": [[]],
        },
    }

    return species_data_specs_per_site


def data_processing(
    location, species_data_specs, folder, lookup_tables, *, save_single_files=True
):
    """
    Process species data for a site based on the species data specifications.

    Parameters:
        location (dict): Dictionary with 'lat' and 'lon' keys.
        species_data_specs (dict): Dictionary with species data specifications for the site.
        folder (Path): Path to the folder containing species data files.
        save_single_files (bool): Save intermediate results to separate files (default is True).
    """
    if location["name"] == species_data_specs["name"]:
        # Create location subfolder
        location_folder = folder / location["deims_id"]
        Path(location_folder).mkdir(parents=True, exist_ok=True)
        all_species_infos = []
        all_species_pfts = {}

        for i, file_name in enumerate(species_data_specs["species_file_names"]):
            if Path(folder / file_name).exists():
                # Copy file with species list to location subfolder, allow overwriting
                shutil.copyfile(folder / file_name, location_folder / file_name)
                species_column = species_data_specs["species_columns"][i]
                extra_columns = species_data_specs["extra_columns"][i]
                species_infos, species_pfts = get_all_infos_and_pft(
                    location_folder / file_name,
                    species_column,
                    lookup_tables,
                    extra_columns=extra_columns,
                    save_single_files=save_single_files,
                )

                if all_species_pfts:
                    all_species_pfts = resolve_species_info_dicts(
                        "PFT",
                        all_species_pfts,
                        species_pfts,
                        info_source_1="previous files",
                        info_source_2=file_name,
                    )
                else:
                    all_species_pfts = species_pfts
            else:
                warnings.warn(
                    f"File '{file_name}' not found in '{folder}'. Skipping file."
                )
    else:
        raise ValueError(
            f"Site name mismatch for DEIMS ID '{location['deims_id']}': "
            f"'{location['name']}' vs. '{species_data_specs['name']}'."
        )


##########################################################################################################################
# Example usage:

lookup_tables = get_lookup_tables("speciesMappingLookupTables", force_create=True)
folder = Path(ut.get_package_root() / "grasslandSites")
species_data_specs = get_species_data_specs()
site_ids = list(species_data_specs.keys())
# Or directly specify selected site IDs here, but these need to be in species_data_specs
# site_ids = ["3de1057c-a364-44f2-8a2a-350d21b58ea0"]  # Obergurgl

for deims_id in site_ids:
    if deims_id in species_data_specs.keys():
        location = ut.get_deims_coordinates(deims_id)

        if location["found"]:
            data_processing(
                location, species_data_specs[deims_id], folder, lookup_tables
            )
        else:
            warnings.warn(
                f"Coordinates not found for DEIMS ID '{deims_id}'. Skipping site."
            )
    else:
        warnings.warn(
            f"DEIMS ID '{deims_id}' not found in species data specifications. Skipping site."
        )
