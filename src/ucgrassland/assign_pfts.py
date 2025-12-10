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
    - Kattge, J., Bönisch, G., Günther, A., Wright, I., Zanne, A.E., Wirth, C., Reich, P.B. and the TRY Consortium (2012):
      TRY - Categorical Traits Dataset. Data from: TRY - a global database of plant traits.
      TRY File Archive https://www.try-db.org/TryWeb/Data.php#3.
    - Website: https://doi.org/10.17871/TRY.3
    - Licence: Creative Commons Attribution 3.0 (CC BY 3.0)
    - Publications:
      - Kattge, J., Díaz, S., Lavorel, S., Prentice, I., Leadley, P., et al. (2011):
        TRY - a global database of plant traits.
        Global Change Biology, https://doi.org/10.1111/j.1365-2486.2011.02451.x.
      - Kattge, J., Bönisch, G., Díaz S., et al. (2020):
        TRY plant trait database - enhanced coverage and open access.
        Global Change Biology, https://doi.org/10.1111/gcb.14904.

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
    - Cornwell, W. (2019):
      traitecoevo/growthform v0.2.3 (v0.2.3).
      Zenodo. https://doi.org/10.5281/zenodo.2543013
    - Supplement to: https://github.com/traitecoevo/growthform/tree/v0.2.3
    - Table redistributed without changes at:
      http://opendap.biodt.eu/grasslands-pdt/speciesMappingLookupTables/
    - Source of "woodiness" column (the information used in this script):
      Zanne A.E., Tank D.C., Cornwell W.K., Eastman J.M., Smith S.A., et al. (2014):
      Three keys to the radiation of angiosperms into freezing environments.
      Nature 506, https://doi.org/10.1038/nature12872.
"""

import argparse
import shutil
import time
import warnings
from collections import defaultdict
from pathlib import Path
from types import MappingProxyType

import pandas as pd
from dotenv import dotenv_values
from pygbif import species

from ucgrassland import elter_site_specs as essp
from ucgrassland import utils as ut
from ucgrassland.logger_config import logger

GRASS_FAMILIES = ("Poaceae", "Cyperaceae", "Juncaceae")
LEGUME_FAMILIES = (
    "Fabaceae",  # legume family,
    "Leguminosae",  # legume family, old name
)
VALID_INFO_ENTRIES = MappingProxyType(
    {
        "PFT": [
            "grass",
            "forb",
            "legume",
            "(tree)",
            "(shrub)",
            "(shrub/tree)",
            "(fern)",
            "(fern/non-woody)",
            "(fern/woody)",
            "(moss)",
            "(lichen)",
            "(legume?)",
            "(woody)",
        ],
        "Woodiness": ["woody", "non-woody"],  # "non-woody/woody"
        "PlantGrowthForm": ["woody", "non-woody", "(fern)", "(lichen)", "(moss)"],
    }
)

LOOKUP_TABLE_SPECS = MappingProxyType(
    {
        "TRY_Family": {
            "file_name": "TRY_Categorical_traits__Family__GBIF_corrected.txt",
            "info_name": "Family",
            "found": False,
            "raw_file_opendap": "TRY_Categorical_Traits_Lookup_Table_2012_03_17_TestRelease.xlsx",
            "raw_file": "TRY_Categorical_traits.xlsx",
            "raw_species_column": "AccSpeciesName",
            "raw_info_columns": ["Family", "PlantGrowthForm", "Woodiness"],
        },
        "TRY_PlantGrowthForm": {
            "file_name": "TRY_Categorical_traits__PlantGrowthForm__GBIF_corrected.txt",
            "info_name": "PlantGrowthForm",
            "found": False,
            "raw_file_opendap": "TRY_Categorical_Traits_Lookup_Table_2012_03_17_TestRelease.xlsx",
            "raw_file": "TRY_Categorical_traits.xlsx",
            "raw_species_column": "AccSpeciesName",
            "raw_info_columns": ["Family", "PlantGrowthForm", "Woodiness"],
        },
        "TRY_Woodiness": {
            "file_name": "TRY_Categorical_traits__Woodiness__GBIF_corrected.txt",
            "info_name": "Woodiness",
            "found": False,
            "raw_file_opendap": "TRY_Categorical_Traits_Lookup_Table_2012_03_17_TestRelease.xlsx",
            "raw_file": "TRY_Categorical_traits.xlsx",
            "raw_species_column": "AccSpeciesName",
            "raw_info_columns": ["Family", "PlantGrowthForm", "Woodiness"],
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
)

# NOTE: Family classifications based on global botanical references
# (WFO, POWO, Judd et al.) and general botanical knowledge, with the
# assumption that families with rare woody/herbaceous exceptions globally
# likely have no such exceptions in Europe, unless European-specific
# exceptions are documented in accessible literature.
#
# These classifications represent educated assessments rather than systematic
# quantitative analyses. "Exclusively" classifications indicate literature
# consensus that families contain only one growth form in Europe.
# "Predominantly" classifications indicate "rare" exceptions are possible
# but comprehensive quantitative verification against European species inventories
# has not been performed.
#
# Thus, we always trust species-level woodiness data over family-level inference.

# NOTE: Family classifications based on global botanical references
# (WFO, POWO, Judd et al.) and general botanical knowledge, with the
# assumption that families with rare woody/herbaceous exceptions globally
# likely have no such exceptions in Europe, unless European-specific
# exceptions are documented in accessible literature.
#
# Family growth form descriptions from World Flora Online (WFO) and
# Plants of the World Online (POWO) have been consulted and documented
# in the project wiki to support these classifications.
#
# These classifications represent educated assessments rather than systematic
# quantitative analyses. "Exclusively" classifications indicate literature
# consensus that families contain only one growth form in Europe.
# "Predominantly" classifications indicate rare exceptions are possible,
# but comprehensive quantitative verification against European species inventories
# has not been performed.
#
# Thus, we trust species-level woodiness data over family-level inference
# in the assignment heuristics.

EXCLUSIVELY_WOODY_FAMILIES = (
    "Aceraceae",  # maple family (should be Sapindaceae, but here if listed separately)
    "Betulaceae",  # birch family
    "Cupressaceae",  # cypress family
    "Fagaceae",  # beech and oak family
    "Juglandaceae",  # walnut family
    "Pinaceae",  # pine family
    "Platanaceae",  # plane tree family
    "Taxaceae",  # yew family
    "Tiliaceae",  # linden family (could be Malvaceae, but then not assignable)
    "Ulmaceae",  # elm family
)

PREDOMINANTLY_WOODY_FAMILIES = (
    "Anacardiaceae",  # cashew and sumac family
    "Caprifoliaceae",  # honeysuckle family
    "Cornaceae",  # dogwood family
    "Oleaceae",  # olive family,
    "Salicaceae",  # willow and poplar family
    "Sapindaceae",  # soapberry family
    "Vitaceae",  # grape family
)

EXCLUSIVELY_HERBACEOUS_FAMILIES = (
    "Droseraceae",  # sundew family
    "Eriocaulaceae",  # pipewort family
    "Lentibulariaceae",  # bladderwort family
    "Primulaceae",  # primrose family
)

PREDOMINANTLY_HERBACEOUS_FAMILIES = (
    "Amaranthaceae",  # amaranth family
    "Boraginaceae",  # borage family
    "Brassicaceae",  # mustard family
    "Campanulaceae",  # bellflower family
    "Caryophyllaceae",  # pink/carnation family
    "Orobanchaceae",  # broomrape family
    "Papaveraceae",  # poppy family
    "Ranunculaceae",  # buttercup family
    "Violaceae",  # violet family
)


def resolve_infos(
    key, info_name, info_1, info_2, *, warn_duplicates=False, warn_conflict=True
):
    """
    Resolve conflicting infos for a key.

    Parameters:
        key (str): Key for which infos are being resolved (e.g. a species name).
        info_name (str): Information name (e.g. 'PFT' or 'Woodiness' or 'Family').
        info_1 (str): First info entry.
        info_2 (str): Second info entry.
        warn_duplicates (bool): Throw warnings for resolving duplicate entries (default is False).
        warn_conflict (bool): Throw warnings for conflicting entries (default is True).

    Returns:
        str: Resolved info entry.
    """
    # Warning for duplicate keys
    if warn_duplicates:
        logger.warning(f"Duplicate entry found for key '{key}'.")

    # Check if the infos are the same, no need to change the info
    if info_1 == info_2:
        info_resolved = info_1

        if warn_duplicates:
            logger.warning(
                f"{info_name} is equal. Keeping the {info_name} '{info_resolved}'."
            )
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
                logger.warning(
                    f"Assigned {info_name} for key '{key}' from duplicate entries is {info_resolved}."
                )
                warn_duplicates = False
        if warn_duplicates:
            logger.warning(
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
        info_source_1 (str): Name of the first source of information (default is "source 1 not specied").
        info_source_2 (str): Name of the second source of information (default is "source 2 not specied").

    Returns:
        dict: Dictionary with resolved information entries for each species.
    """
    logger.info(
        f"Combining {info_name} information from '{info_source_1}' and '{info_source_2}' dictionaries ..."
    )
    resolved_dict = {}

    # Iterate over keys present in both dictionaries and resolve infos
    common_keys = set(info_dict_1.keys()) & set(info_dict_2.keys())

    for spec in common_keys:
        resolved_dict[spec] = resolve_infos(
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


def reduce_pft_info(info, *, separate_woody=False):
    """
    Map PFT information to coarse category.

    Parameters:
        info (str): PFT information entry.

    Returns:
        str: Reduced PFT information entry.
    """
    if info in ["not assigned", "not found"]:  # or info.startswith("conflicting"):
        return "not_assigned"

    # for debugging remaining conflicting cases
    if info.startswith("conflicting"):
        return "not_assigned"

    if info in ["(tree)", "(shrub)", "(shrub/tree)", "(woody)", "(fern/woody)"]:
        return "woody" if separate_woody else "other"

    if info in ["(fern)", "(moss)", "(lichen)", "(legume?)", "(fern/non-woody)"]:
        return "other"

    return info


def replace_info_strings(info, info_name):
    """
    Revise information entries based on the specified information type for consistency.

    Parameters:
        info (str): Original information entry.
        info_name (str): Type of species information ('PFT' or 'Woodiness' or 'PlantGrowthForm').

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
            info, "non-woody/woody", "conflicting (non-woody vs. woody)", at_end=True
        )
        info = ut.replace_substrings(info, "W", "woody", at_end=True)
        info = ut.replace_substrings(info, "H", "non-woody", at_end=True)
        info = ut.replace_substrings(
            info, ["NA", "variable"], "not assigned", at_end=True
        )
    elif info_name == "PlantGrowthForm":
        info = ut.replace_substrings(
            info,
            ["herb/shrub", "herb/shrub/tree"],
            "conflicting (non-woody vs. woody)",
            at_end=True,
        )
        info = ut.replace_substrings(
            info, ["W", "shrub", "shrub/tree", "tree"], "woody", at_end=True
        )
        info = ut.replace_substrings(
            info, ["H", "herb", "graminoid"], "non-woody", at_end=True
        )
        info = ut.replace_substrings(
            info, ["NA", "variable"], "not assigned", at_end=True
        )
        info = ut.replace_substrings(info, "fern", "(fern)", at_end=True)
        info = ut.replace_substrings(info, "lichen", "(lichen)", at_end=True)
        info = ut.replace_substrings(info, "moss", "(moss)", at_end=True)

    if not info:
        info = "not assigned"

    return info


def read_info_dict(
    file_name,
    info_name,
    *,
    key_column=0,
    key_name="Species",
    info_column=None,
    header_lines=1,
    new_file="",
):
    """
    Read a dictionary from a text file containing keys and a corresponding information.

    Parameters:
        file_name (str): Path to the text file.
        info_name (str): Information name (e.g. 'PFT' or 'Woodiness' or 'Family').
        key_column (str or int): Key column identifier (name as string or index).
        key_name (str): Key name for the dictionary (default is 'Species').
        info_column (int): Information column identifier (name as string or index, default is None for using info_name).
        header_lines (int): Number of header lines to skip (default is 1).
        new_file (str): Path of new file to save the dictionary (default is "", to not save).

    Returns:
        dict: Dictionary where key_column entries are keys, and infos are values.
    """
    if file_name.is_file():
        valid_infos = VALID_INFO_ENTRIES.get(info_name, ["any"])
        logger.info(f"Reading {info_name} lookup table from '{file_name}' ...")

        # Search for 'info_name' as column name if not specified otherwise
        if info_column is None:
            info_column = info_name

        # Open file for reading
        with open(file_name, "r", encoding="utf-8", errors="replace") as file:
            info_dict = {}
            processed_lines = 0
            last_header_line = None

            # Skip header lines
            for _ in range(header_lines):
                last_header_line = next(file)

            # Get column names from last header line, find key and info columns
            column_names = [last_header_line.rstrip("\n").split("\t", -1)]
            key_column = ut.find_column_index(column_names, key_column)
            info_column = ut.find_column_index(column_names, info_column)

            # Split each line into columns (tab as delimiter), get key and info from columns
            for line_number, line in enumerate(file, start=header_lines + 1):
                columns = line.rstrip("\n").split("\t", -1)
                key, info = (columns[key_column], columns[info_column])
                info = replace_info_strings(info, info_name)

                # Warning if info is not valid and not "not assigned"
                if info == "" or (
                    valid_infos != ["any"]
                    and info not in valid_infos
                    and not info.startswith(
                        ("not assigned", "conflicting", "not found")
                    )
                ):
                    logger.warning(
                        f"Invalid {info_name} found on line {line_number} for {key}: '{info}'."
                    )

                # Check if (replaced) key name is already in lookup table
                if key in info_dict:
                    # Resolve infos for existing key
                    info_dict[key] = resolve_infos(key, info_name, info, info_dict[key])
                else:
                    # Add new key and info to lookup table
                    info_dict[key] = info

                processed_lines += 1

        # Sort dictionary by keys
        info_dict = dict(sorted(info_dict.items()))
        logger.info(
            f"Processed {processed_lines} lines. "
            f"Final {info_name} lookup table has {len(info_dict)} entries."
        )

        # Save created dictionary to new file if file is provided
        if new_file:
            ut.dict_to_file(info_dict, new_file, column_names=[key_name, info_name])

        return info_dict
    else:
        try:
            raise FileNotFoundError(
                f"File '{file_name}' not found. Cannot read {info_name} lookup table."
            )
        except FileNotFoundError as e:
            logger.error(e)
            raise


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
            logger.error(f"GBIF request failed ({e}).")

            if attempts > 0:
                logger.info(f"Retrying in {delay} seconds ...")
                time.sleep(delay)

    # After exhausting all attempts
    logger.error(
        f"GBIF request for species '{spec}' failed repeatedly. Returning 'not found'."
    )
    return "not found"


def get_gbif_species(spec, *, accepted_ranks=["GENUS", "FAMILY"]):
    """
    Retrieve a species name or higher rank from the GBIF taxonomic backbone.

    Parameters:
        spec (str): Species name to look up in the GBIF taxonomic backbone.
        accepted_ranks (list): List of taxonomic ranks above SPECIES that can be used as new species entry (default is ["GENUS", "FAMILY"]).

    Returns:
        str: Matched or suggested species name from GBIF, or the original species name if no match is found.
    """
    spec_gbif_dict = gbif_request(spec)

    if spec_gbif_dict == "not found":
        return spec
    elif spec_gbif_dict["matchType"] == "NONE":
        # No match, return input species
        logger.warning(f"'{spec}' not found.")
        return spec
    elif spec_gbif_dict["rank"] == "SPECIES":
        if "species" in spec_gbif_dict:
            # Use 'species' entry
            spec_match = spec_gbif_dict["species"]

            if spec_match != spec:
                logger.info(f"'{spec}' replaced with GBIF SPECIES '{spec_match}'.")
        else:
            # No 'species' entry, use 'canonicalName' entry (should not happen)
            spec_match = spec_gbif_dict["canonicalName"]
            logger.warning(
                f"'{spec}' not exactly identified by GBIF. "
                f"Result rank is SPECIES, but no species entry. Using CANONICALNAME '{spec_match}'."
            )
            if spec_match != spec:
                logger.warning(
                    f"'{spec}' replaced with GBIF CANONICALNAME '{spec_match}'."
                )
    elif spec_gbif_dict["rank"] == "SUBSPECIES":
        # seperated for testing, could be merged with "SPECIES" case later
        if "species" in spec_gbif_dict:
            # Use 'species' entry
            spec_match = spec_gbif_dict["species"]

            if spec_match != spec:
                logger.warning(
                    f"'{spec}' SUBSPECIES replaced with GBIF SPECIES '{spec_match}'."
                )
        else:
            # No 'species' entry, use 'canonicalName' entry (should not happen)
            spec_match = spec_gbif_dict["canonicalName"]
            logger.warning(
                f"'{spec}' not exactly identified by GBIF. "
                f"Result rank is SUBSPECIES, but no species entry. Using CANONICALNAME '{spec_match}'."
            )
            if spec_match != spec:
                logger.warning(
                    f"'{spec}' replaced with GBIF CANONICALNAME '{spec_match}'."
                )
    elif "canonicalName" in spec_gbif_dict:
        # No exact match, use 'canonicalName' entry
        spec_match = spec_gbif_dict["canonicalName"]
        logger.warning(f"'{spec}' not exactly identified by GBIF.")

        if spec_match == spec:
            # No better match, keep input species
            logger.info(
                f"No replacement (GBIF match was {spec_gbif_dict['rank']} '{spec_match}')."
            )
        else:
            if spec_gbif_dict["rank"] in accepted_ranks:
                # GBIF result in accepted ranks, keep this result
                spec_match = f"{spec_match} species"
                logger.warning(
                    f"'{spec}' replaced with {spec_gbif_dict['rank']} '{spec_match}'."
                )

            else:
                # GBIF result above accepted ranks, check for suggestions
                spec_gbif_suggest = species.name_suggest(q=spec, rank="species")

                if len(spec_gbif_suggest) > 0:
                    # Suggestions found, use first (i.e. most relevant) suggestion
                    spec_gbif_suggest = [
                        sgs.get("species") for sgs in spec_gbif_suggest
                    ]
                    spec_match = next(
                        (sgs for sgs in spec_gbif_suggest if sgs is not None), None
                    )

                    if spec_match is None:
                        logger.info(
                            f"No replacement (all GBIF suggestions for '{spec}' are None)."
                        )
                    else:
                        sgs_string = ", ".join(
                            [f"'{sgs}'" for sgs in spec_gbif_suggest]
                        )
                        logger.info(f"Candidate species: {sgs_string}.")

                        # Check if suggestions include the input species name but not at first position
                        if (
                            spec in spec_gbif_suggest
                            and spec_gbif_suggest.index(spec) > 0
                        ):
                            logger.warning(
                                f"No replacement ('{spec}' included in GBIF suggestions, though not at the first position)."
                            )
                            return spec

                        logger.info(
                            f"'{spec}' replaced with first GBIF suggestion '{spec_match}'."
                        )
                else:
                    # No suggestions, return input species
                    logger.info(
                        f"No replacement (GBIF match was {spec_gbif_dict['rank']} '{spec_match}')."
                    )
                    return spec
    else:
        logger.warning(
            f"Neither 'species' nor 'canonicalName' in result, match type {spec_gbif_dict['matchType']}."
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
        logger.error(f"Family for '{spec}' not found by GBIF. Returning 'not found'.")
        return "not found"


def get_pft_from_family_woodiness(
    spec,
    family_dict,
    woodiness_dict,
    *,
    accept_predominantly_woody_families=True,
    accept_predominantly_herbaceous_families=True,
    pft_from_family_counts=None,
):
    """
    Determine PFT based on species family and woodiness.

    Parameters:
        spec (str): Species name to find PFT.
        family_dict (dict): Dictionary where species names are keys, and family infos are values.
        woodiness_dict (dict): Dictionary where species names are keys, and woodiness infos are values.
        accept_predominantly_woody_families (bool): Accept predominantly woody families as PFT 'woody' if
          species woodiness is unclear (default is True).
        accept_predominantly_herbaceous_families (bool): Accept predominantly herbaceous families as PFT 'forb' if
          species woodiness is unclear (default is False).
        pft_from_family_counts (defaultdict): Dictionary to add counts of PFT assignments, conflicts or non-assignments
          from family info (default is None, new defaultdict(int) will be created).

    Returns:
        str: PFT info or "not assigned."
        defaultdict: Updated counts of PFT assignments, conflicts or non-assignments from family info.
    """
    family = family_dict.get(spec, "not found")
    woodiness = woodiness_dict.get(spec, "not found")

    # Initialize PFT from family counts dictionary if not provided
    if pft_from_family_counts is None:
        pft_from_family_counts = defaultdict(int)

    if family == "not found" and woodiness == "not found":
        return "not found", pft_from_family_counts

    # NOTE: assigning woodiness based on family is not implemented to keep the (missing) woodiness info
    woodiness_info = get_woodiness_info_from_family(family)

    def _throw_log_message(
        woodiness, spec, family, woodiness_info, pft_assigned, *, log_level="warning"
    ):
        """Helper function to throw log messages for PFT assignment based on woodiness and family."""
        message = (
            f"Woodiness is '{woodiness}' for '{spec}'. Family '{family}' is {woodiness_info}. "
            f"Assigning PFT '{pft_assigned}'."
        )
        if log_level == "error":
            logger.error(message)
        elif log_level == "warning":
            logger.warning(message)

    # Assign PFT according to heuristics
    # Check for conflicts between family and woodiness, assign PFT accordingly if suitable
    if family in GRASS_FAMILIES:
        pft_assigned = "grass"

        # error message, but overrule any conflicting woodiness for grass families
        if woodiness in [
            "woody",
            "fern",
            "moss",
            "lichen",
            "(woody)",
            "(fern)",
            "(moss)",
            "(lichen)",
        ] or woodiness.startswith("conflicting"):
            _throw_log_message(
                woodiness, spec, family, woodiness_info, pft_assigned, log_level="error"
            )
            pft_from_family_counts[family + "_conflict"] += 1
    elif woodiness == "non-woody":
        if family in LEGUME_FAMILIES:
            pft_assigned = "legume"
        elif family in EXCLUSIVELY_WOODY_FAMILIES:
            pft_assigned = "conflicting (forb vs. woody)"
            _throw_log_message(
                woodiness, spec, family, woodiness_info, pft_assigned, log_level="error"
            )
            pft_from_family_counts[family + "_conflict"] += 1
        else:
            pft_assigned = "forb"

            if family in PREDOMINANTLY_WOODY_FAMILIES:
                _throw_log_message(
                    woodiness, spec, family, woodiness_info, pft_assigned
                )
                pft_from_family_counts[family + "_conflict"] += 1
    elif woodiness in ["woody", "(woody)"]:
        if family in EXCLUSIVELY_HERBACEOUS_FAMILIES:
            pft_assigned = "conflicting (forb vs. woody)"
            _throw_log_message(
                woodiness, spec, family, woodiness_info, pft_assigned, log_level="error"
            )
            pft_from_family_counts[family + "_conflict"] += 1
        else:
            pft_assigned = "(woody)"

            if family in PREDOMINANTLY_HERBACEOUS_FAMILIES:
                _throw_log_message(
                    woodiness, spec, family, woodiness_info, pft_assigned
                )
                pft_from_family_counts[family + "_conflict"] += 1
    elif woodiness == "(fern/woody)":
        if family in EXCLUSIVELY_HERBACEOUS_FAMILIES:
            pft_assigned = "conflicting (fern/woody vs. forb)"
            _throw_log_message(
                woodiness, spec, family, woodiness_info, pft_assigned, log_level="error"
            )
            pft_from_family_counts[family + "_conflict"] += 1
        else:
            pft_assigned = "(fern/woody)"

            if family in PREDOMINANTLY_HERBACEOUS_FAMILIES:
                _throw_log_message(
                    woodiness, spec, family, woodiness_info, pft_assigned
                )
                pft_from_family_counts[family + "_conflict"] += 1
    elif woodiness in [
        "fern",
        "moss",
        "lichen",
        "(fern)",
        "(moss)",
        "(lichen)",
        "(fern/non-woody)",
    ]:
        if family in LEGUME_FAMILIES:
            pft_assigned = ut.combine_info_strings("legume", woodiness)
        elif family in EXCLUSIVELY_WOODY_FAMILIES:
            pft_assigned = ut.combine_info_strings("woody", woodiness)
        elif family in EXCLUSIVELY_HERBACEOUS_FAMILIES:
            pft_assigned = ut.combine_info_strings("forb", woodiness)
        else:
            pft_assigned = woodiness if woodiness.startswith("(") else f"({woodiness})"

        if pft_assigned.startswith("conflicting"):
            if woodiness in ["fern", "(fern)"]:
                _throw_log_message(
                    woodiness,
                    spec,
                    family,
                    woodiness_info + ", but contains no fern species",
                    pft_assigned,
                    log_level="error",
                )
            else:
                _throw_log_message(
                    woodiness,
                    spec,
                    family,
                    woodiness_info,
                    pft_assigned,
                    log_level="error",
                )

            pft_from_family_counts[family + "_conflict"] += 1
    elif woodiness == "conflicting (non-woody vs. woody)":
        # Assignment for conflict herbaceous vs. woody is possible here
        if family in LEGUME_FAMILIES:
            # Legumes can be herbaceous or woody, keep conflict but specify
            pft_assigned = "conflicting (legume vs. woody)"
        else:
            pft_assigned = "conflicting (forb vs. woody)"
            # NOTE: we keep the conflict even if family suggests exclusively herbaceous or woody,
            #       because we have higher trust in the species-level woodiness info

        # Error if family is strictly herbaceous or strictly woody, warning otherwise
        if woodiness_info.startswith("exclusively"):
            _throw_log_message(
                woodiness, spec, family, woodiness_info, pft_assigned, log_level="error"
            )
        else:
            _throw_log_message(woodiness, spec, family, woodiness_info, pft_assigned)

        pft_from_family_counts[family + "_conflict"] += 1
    elif family in EXCLUSIVELY_WOODY_FAMILIES:
        pft_assigned = "(woody)"
        pft_from_family_counts[family + "_assigned"] += 1
    elif accept_predominantly_woody_families and family in PREDOMINANTLY_WOODY_FAMILIES:
        pft_assigned = "(woody)"
        _throw_log_message(woodiness, spec, family, woodiness_info, pft_assigned)
        pft_from_family_counts[family + "_assigned"] += 1
    elif family in EXCLUSIVELY_HERBACEOUS_FAMILIES:
        pft_assigned = "forb"
        pft_from_family_counts[family + "_assigned"] += 1
    elif (
        accept_predominantly_herbaceous_families
        and family in PREDOMINANTLY_HERBACEOUS_FAMILIES
    ):
        pft_assigned = "forb"
        _throw_log_message(woodiness, spec, family, woodiness_info, pft_assigned)
        pft_from_family_counts[family + "_assigned"] += 1
    else:
        pft_assigned = "not assigned"
        _throw_log_message(woodiness, spec, family, woodiness_info, pft_assigned)
        pft_from_family_counts[family + "_not_assignable"] += 1
        # NOTE: conflicting woodiness cannot be resolved here
        # NOTE: legume families could be legume or woody, cannot be resolved here

    return pft_assigned, pft_from_family_counts


def read_species_list(
    file_name,
    *,
    species_column=0,
    extra_columns=[],
    header_lines=1,
    check_gbif=True,
    accepted_ranks=["GENUS", "FAMILY"],
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
        file_name (Path): Path to the file containing the species.
        species_column (str or int): Species name column name or number (0-based index, default is 0).
        extra_columns (list of str or int): Additional columns to include in the list (default is empty list).
        header_lines (int): Number of header line, lines before will be skipped (default is 1).
        check_gbif (bool): Check/correct species names with GBIF taxonomic backbone (default is True).
        accepted_ranks (list): List of taxonomic ranks above SPECIES that can be used as new species entry (default is ["GENUS", "FAMILY"]).
        save_new_file (bool): Save species names (and info) retrieved to new file (default is True).
        new_suffix (str): Suffix for new file type (default is None for keeping the original file type).
        add_species_column_copy (bool): Add a copy of the original species column as a new first column to the output file (default is True).
        combine_differing_entries (bool): Combine differing entries (with same info in first column) into one (default is False).
        csv_delimiter (str): Delimiter for CSV files (default is ',').

    Returns:
        list: List of unique species names, and additional info if requested and found.
    """
    file_extension = file_name.suffix.lower()
    logger.info(f"Reading species list from '{file_name}' ...")

    if file_extension == ".xlsx":
        try:
            df = pd.read_excel(file_name, header=header_lines - 1)
        except Exception as e:
            logger.error(f"Reading .xlsx file failed ({e}).")
            return []

        # Determine species name column index
        column_indexes = [ut.find_column_index(df, species_column)]

        for col_name in extra_columns:
            try:
                column_indexes.append(ut.find_column_index(df, col_name))
            except (KeyError, ValueError):
                logger.error(
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
            logger.error(f"Reading .csv file failed ({e}).")
            return []

        # Determine species name column index
        column_indexes = [ut.find_column_index(df, species_column)]

        for col_name in extra_columns:
            try:
                column_indexes.append(ut.find_column_index(df, col_name))
            except (KeyError, ValueError):
                logger.error(
                    f"Failed to find column '{col_name}'. Omitted in species list."
                )

        # Extract species names from specified columns
        species_list = df.iloc[:, column_indexes].values.tolist()
    elif file_extension == ".txt":
        try:
            with open(file_name, "r", encoding="utf-8", errors="replace") as file:
                species_data = [line.strip().split("\t") for line in file]
        except Exception as e:
            logger.error(f"Reading text file failed ({e}).")
            return []

        # Determine species name column index
        column_indexes = [ut.find_column_index(species_data, species_column)]

        for col_name in extra_columns:
            try:
                column_indexes.append(ut.find_column_index(species_data, col_name))
            except (KeyError, ValueError):
                logger.error(
                    f"Failed to find column '{col_name}'. Omitted in species list."
                )

        try:
            species_list = [
                [line[index] for index in column_indexes]
                for line in species_data[header_lines:]
            ]
        except IndexError as e:
            logger.error(f"Processing line failed ({e}). Returning empty list.")
            return []
    else:
        try:
            raise ValueError(
                "Unsupported file format. Must be '.xlsx', '.txt', or '.csv'."
            )
        except ValueError as e:
            logger.error(e)
            raise

    # Reduce list to unique entries only
    species_list = ut.sort_and_cleanup_list(
        species_list, combine_differing_entries=combine_differing_entries
    )

    # GBIF check and correction if selected
    if check_gbif:
        logger.info("Searching for species in GBIF taxonomic backbone ...")
        species_list_renamed = []

        for entry in species_list:
            spec = entry if isinstance(entry, str) else entry[0]
            spec_renamed = get_gbif_species(spec, accepted_ranks=accepted_ranks)
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
                file_name,
                column_names=["Species GBIF", "Species Original"] + extra_columns,
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
                file_name,
                column_names=first_columns + extra_columns,
            )

    # No removal of 'nan' or duplicate species entries in renamed list, assigned infos to be matched with original list later
    empty_strings = species_list.count("")
    logger.info(
        f"Species list has {len(species_list)} entries, including {empty_strings} empty entries."
    )

    if not combine_differing_entries:
        duplicates = ut.count_duplicates(species_list)

        if len(duplicates) > 0:
            duplicates_string = ", ".join(
                [f"'{spec}' ({count})" for spec, count in duplicates.items()]
            )
            logger.info(f"Duplicates: {duplicates_string}.")

    return species_list_renamed


def user_input_info(info_dict, info_name, *, start_string="not "):
    """
    Iterate through species without info assigned and prompt user to select a new info.

    Parameters:
        info_dict (dict): Dictionary with species names as keys and corresponding infos.
        info_name (str): Information name ('PFT' or 'Woodiness').
        start_string (string): Beginning of infos that get suggested for reassignment (default is "not ").

    Returns:
        dict: Modified dictionary with updated infos based on user input.
    """
    valid_choices = VALID_INFO_ENTRIES.get(info_name)
    valid_choices.append("not assigned")
    choice_string = ""
    logger.info(f"Going through species with {info_name} '{start_string}' ...")
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
                warnings.warn(
                    f"Invalid choice. Leaving {info_name} as is.", UserWarning
                )
            else:
                if 1 <= user_choice <= len(valid_choices):
                    user_info = f"{valid_choices[user_choice - 1]} (user input)"
                    info_dict[spec] = user_info
                    logger.info(f"Changing {info_name} to '{user_info}'.")
                elif user_choice == len(valid_choices) + 1:
                    pass  # Leave as is, no change needed
                elif user_choice == len(valid_choices) + 2:
                    print(
                        f"Exiting the manual {info_name} assignment for species with {info_name} '{start_string}'."
                    )
                    break  # Exit the loop
                else:
                    warnings.warn(
                        f"Invalid choice. Leaving {info_name} as is.", UserWarning
                    )

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
            logger.warning(
                f"Species with {info_name} '{unclear_info}': {count_unclear}."
            )

            if ask_user_input:
                # Ask user if species with unclear info shall be modified manually
                manual_input = input(
                    "Do you want to make manual inputs for these species? (y/n): "
                ).lower()

                if manual_input == "y":
                    info_dict = user_input_info(
                        info_dict, info_name, start_string=unclear_info
                    )

    return info_dict


def get_species_info(
    species_list,
    info_lookup,
    info_name,
    *,
    file_name="",
    lookup_source="source not specified",
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
        lookup_source (str): Name of the source of information (default is "source not specified").
        ask_user_input (bool): Ask user for manual input of unclear infos (default is False).

    Returns:
        dict or list: Dict or list of pairs of the species names and corresponding infos.
    """
    logger.info(
        f"Searching for species' {info_name} in '{lookup_source}' lookup table ... "
    )

    # Convert info_lookup to dictionary of only infos if not already
    info_lookup = ut.reduce_dict_to_single_info(info_lookup, info_name)

    # Read info from lookup dict if available
    info_dict = {}

    for spec in species_list:
        if spec not in info_dict:
            info_dict[spec] = info_lookup.get(spec, "not found")

    # Check for unclear infos, sort, and save dictionary to file if specified
    info_dict = check_unclear_infos(info_name, info_dict, ask_user_input=ask_user_input)
    info_dict = dict(sorted(info_dict.items()))

    if file_name:
        file_name = ut.add_string_to_file_name(
            file_name, f"__{info_name}__{lookup_source}"
        )
        ut.dict_to_file(info_dict, file_name, column_names=["Species", info_name])

    return info_dict


def get_species_family_gbif(species_list, *, file_name=""):
    """
    Retrieve families for a list of species using GBIF taxonomic backbone.

    Parameters:
        species_list (list): List of species names.
        file_name (str): File name to save the result (empty string to skip saving).

    Returns:
        dict or list: Resulting dictionary or list with species and their Family information.
    """
    info_name = "Family"
    logger.info("Searching for species' Family in GBIF taxonomic backbone ...")
    info_dict = {}

    for spec in species_list:
        if spec not in info_dict:
            info_dict[spec] = get_gbif_family(spec)

    # Sort, and save dictionary to file if specified
    info_dict = dict(sorted(info_dict.items()))

    if file_name:
        file_name = ut.add_string_to_file_name(file_name, "__Family__GBIF")
        ut.dict_to_file(info_dict, file_name, column_names=["Species", info_name])

    return info_dict


def get_species_pft_from_family_woodiness(
    species_list,
    family_dict,
    woodiness_dict,
    *,
    file_name="",
    lookup_source_family="family source not specified",
    lookup_source_woodiness="woodiness source not specified",
    ask_user_input=False,
):
    """
    Get PFT for a list of species based on family and woodiness.

    Parameters:
        species_list (list): List of species names.
        family_dict (dict): Dictionary mapping species to their families.
        woodiness_dict (dict): Dictionary mapping species to their woodiness.
        file_name (str): File name to save the result (empty string to skip saving).
        ask_user_input (bool): Ask user for manual input of unclear infos (default is False).

    Returns:
        dict or list: Resulting dictionary or list with species and their PFT information.
    """
    info_name = "PFT"
    logger.info(
        f"Obtaining species' {info_name} from lookup tables, "
        f"Family: '{lookup_source_family}' and Woodiness: '{lookup_source_woodiness}' ..."
    )
    info_dict = {}
    pft_from_family_counts = defaultdict(int)

    for spec in species_list:
        if spec not in info_dict:
            info_dict[spec], pft_from_family_counts = get_pft_from_family_woodiness(
                spec,
                family_dict,
                woodiness_dict,
                pft_from_family_counts=pft_from_family_counts,
            )

    logger.info("PFT assignment summary based on family heuristics:")
    pft_from_family_counts = dict(sorted(pft_from_family_counts.items()))

    for key, count in pft_from_family_counts.items():
        logger.info(f"{key}: {count}")

    # Check for unclear infos, sort, and save dictionary to file if specified
    info_dict = check_unclear_infos(info_name, info_dict, ask_user_input=ask_user_input)
    info_dict = dict(sorted(info_dict.items()))

    if file_name:
        file_name = ut.add_string_to_file_name(
            file_name,
            f"__{info_name}__family_{lookup_source_family}_woodiness_{lookup_source_woodiness}",
        )
        ut.dict_to_file(info_dict, file_name, column_names=["Species", info_name])

    return info_dict, pft_from_family_counts


def get_woodiness_info_from_family(family):
    """
    Get woodiness information for a given family.

    Parameters:
        family (str): Family name to find woodiness.

    Returns:
        str: Woodiness information or "not allowing clear assignment of woodiness."
    """
    if family in EXCLUSIVELY_WOODY_FAMILIES:
        return "exclusively woody"
    elif family in PREDOMINANTLY_WOODY_FAMILIES:
        return "mostly woody, but some herbaceous exceptions exist"
    elif family in EXCLUSIVELY_HERBACEOUS_FAMILIES:
        return "exclusively herbaceous"
    elif family in PREDOMINANTLY_HERBACEOUS_FAMILIES:
        return "mostly herbaceous, but some woody exceptions exist"
    elif family in GRASS_FAMILIES:
        return "grass family (exclusively herbaceous)"
    elif family in LEGUME_FAMILIES:
        return "legume family (herbaceous or woody)"
    else:
        return "not allowing clear assignment of woodiness"


def get_lookup_tables(
    *, lookup_folder_name="speciesMappingLookupTables", force_create=False, cache=None
):
    """
    Get lookup tables from cache or opendap, create if not found.

    Parameters:
        lookup_folder_name (str): Name of subfolder containing and/or receiving lookup tables (default is 'speciesMappingLookupTables').
        force_create (bool): Force creation of new lookup tables (default is False).
        cache (str): Path to local folder containing and/or receiving lookup tables and/or raw source files (default is None).
    """
    # Define folder where lookup tables are expected, and will be stored
    lookup_folder = Path(cache) if cache else Path.cwd() / lookup_folder_name
    lookup_tables = {}

    if not force_create:
        for table_name, table_info in LOOKUP_TABLE_SPECS.items():
            table_file = lookup_folder / table_info["file_name"]

            if not table_file.is_file():
                ut.download_file_opendap(
                    table_info["file_name"], lookup_folder_name, lookup_folder
                )

            if table_file.is_file():
                # Use local lookup tables, if found
                lookup_tables[table_name] = read_info_dict(
                    table_file, table_info["info_name"]
                )
                LOOKUP_TABLE_SPECS[table_name]["found"] = True

    # Create missing lookup tables (i.e. all in case of force_create) from raw tables
    for table_name, table_info in LOOKUP_TABLE_SPECS.items():
        if not table_info["found"]:
            # Create lookup table from raw files
            # raw file: the source data file (xlsx or csv) containing species and info columns
            # raw list file: the processed txt file with species and selected info(s) extracted from raw file
            raw_file = lookup_folder / table_info["raw_file"]
            raw_list_file = ut.add_string_to_file_name(
                raw_file, "__Species__GBIF_corrected", new_suffix=".txt"
            )

            if not raw_list_file.is_file():
                ut.download_file_opendap(
                    raw_list_file.name, lookup_folder_name, lookup_folder
                )

            if not raw_list_file.is_file():
                # Processed raw list file not available, create it from raw file
                if not raw_file.is_file():
                    # Download raw file from opendap, rename to standard name
                    ut.download_file_opendap(
                        table_info["raw_file_opendap"],
                        lookup_folder_name,
                        lookup_folder,
                        new_file_name=table_info["raw_file"],
                    )

                if raw_file.is_file():
                    logger.info(
                        f"'{table_name}' source file found. Reading species infos from '{raw_file}' ..."
                    )
                else:
                    try:
                        raise FileNotFoundError(
                            f"'{table_name}' source file '{table_info['raw_file']}' not found."
                        )
                    except FileNotFoundError as e:
                        logger.error(e)
                        raise

                # Process raw source file with info column(s) to .txt file
                read_species_list(
                    raw_file,
                    species_column=table_info["raw_species_column"],
                    extra_columns=table_info["raw_info_columns"],
                    check_gbif=True,
                    accepted_ranks=[],  # cannot accept higher ranks for trait lookup tables
                    save_new_file=True,
                    new_suffix=".txt",
                    add_species_column_copy=False,
                    combine_differing_entries=True,
                    csv_delimiter=",",
                )

            if raw_list_file.is_file():
                # Get lookup table from raw list in .txt file, and save to file
                lookup_tables[table_name] = read_info_dict(
                    raw_list_file,
                    table_info["info_name"],
                    new_file=lookup_folder / table_info["file_name"],
                    info_column=table_info["info_name"],
                )
            else:
                try:
                    raise FileNotFoundError(
                        f"File '{raw_list_file}' not found. Cannot retrieve '{table_name}'."
                    )
                except FileNotFoundError as e:
                    logger.error(e)
                    raise

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
            logger.info(f"Extra column found with family information: '{col_name}'.")
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
                ut.add_string_to_file_name(file_name, "__Family__Extra"),
                column_names=["Species", "Family"],
            )

    # Combine and resolve Family from both sources (TRY & GBIF)
    family_combined = resolve_species_info_dicts(
        "Family", family_try, family_gbif, info_source_1="TRY", info_source_2="GBIF"
    )

    # Find Woodiness infos based on sources, write to files if requested
    plantgrowthform_try = get_species_info(
        species_to_lookup,
        lookup_tables["TRY_PlantGrowthForm"],
        "PlantGrowthForm",
        file_name=file_name,
        lookup_source="TRY",
    )
    woodiness_column_try = get_species_info(
        species_to_lookup,
        lookup_tables["TRY_Woodiness"],
        "Woodiness",
        file_name=file_name,
        lookup_source="TRY",
    )
    woodiness_try = resolve_species_info_dicts(
        "Woodiness",
        plantgrowthform_try,
        woodiness_column_try,
        info_source_1="TRY PlantGrowthForm",
        info_source_2="TRY Woodiness",
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

    # Find PFT based on different combinations of Family and Woodiness sources
    pft_family_try_woodiness_try, pft_from_family_summary = (
        get_species_pft_from_family_woodiness(
            species_to_lookup,
            family_try,
            woodiness_try,
            file_name=file_name,
            lookup_source_family="TRY",
            lookup_source_woodiness="TRY",
        )
    )
    pft_family_gbif_woodiness_try, pft_from_family_counts = (
        get_species_pft_from_family_woodiness(
            species_to_lookup,
            family_gbif,
            woodiness_try,
            file_name=file_name,
            lookup_source_family="GBIF",
            lookup_source_woodiness="TRY",
        )
    )
    pft_from_family_summary = ut.add_to_dict(
        pft_from_family_summary,
        pft_from_family_counts,
        value_prev="family_try_woodiness_try",
        value_add="family_gbif_woodiness_try",
    )
    pft_family_gbif_woodiness_zanne, pft_from_family_counts = (
        get_species_pft_from_family_woodiness(
            species_to_lookup,
            family_gbif,
            woodiness_zanne,
            file_name=file_name,
            lookup_source_family="GBIF",
            lookup_source_woodiness="Zanne",
        )
    )
    pft_from_family_summary = ut.add_to_dict(
        pft_from_family_summary,
        pft_from_family_counts,
        value_add="family_gbif_woodiness_zanne",
    )
    pft_family_gbif_woodiness_combined, pft_from_family_counts = (
        get_species_pft_from_family_woodiness(
            species_to_lookup,
            family_gbif,
            woodiness_combined,
            file_name=file_name,
            lookup_source_family="GBIF",
            lookup_source_woodiness="combined",
        )
    )
    pft_from_family_summary = ut.add_to_dict(
        pft_from_family_summary,
        pft_from_family_counts,
        value_add="family_gbif_woodiness_combined",
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
        info_source_1="combined",
        info_source_2="family_GBIF_woodiness_Zanne",
    )

    # Treat extra family infos as additional source if found
    if not family_extra_found:
        # Create empty dict family_extra if not found
        family_extra = dict.fromkeys(species_original, "not found")

    woodiness_combined_original_keys = {
        species_original[index]: woodiness_combined[species_to_lookup[index]]
        for index in range(len(species_to_lookup))
    }
    pft_combined_original_keys = {
        species_original[index]: pft_combined[species_to_lookup[index]]
        for index in range(len(species_to_lookup))
    }
    pft_family_extra_woodiness_combined, pft_from_family_counts = (
        get_species_pft_from_family_woodiness(
            species_original,
            family_extra,
            woodiness_combined_original_keys,
            file_name=file_name,
            lookup_source_family="Extra",
            lookup_source_woodiness="combined",
        )
    )
    pft_from_family_summary = ut.add_to_dict(
        pft_from_family_summary,
        pft_from_family_counts,
        value_add="family_extra_woodiness_combined",
    )
    pft_combined_extra = resolve_species_info_dicts(
        "PFT",
        pft_combined_original_keys,
        pft_family_extra_woodiness_combined,
        info_source_1="combined",
        info_source_2="family_Extra_woodiness_combined",
    )

    if file_name:
        ut.dict_to_file(
            family_combined,
            ut.add_string_to_file_name(file_name, "__Family__combined"),
            column_names=["Species", "Family Combined"],
        )
        ut.dict_to_file(
            woodiness_combined,
            ut.add_string_to_file_name(file_name, "__Woodiness__combined"),
            column_names=["Species", "Woodiness Combined"],
        )
        ut.dict_to_file(
            pft_combined,
            ut.add_string_to_file_name(file_name, "__PFT__combined"),
            column_names=["Species", "PFT Combined"],
        )
        ut.dict_to_file(
            pft_combined_extra,
            ut.add_string_to_file_name(file_name, "__PFT__combined_Extra"),
            column_names=["Species", "PFT Combined incl. Extra"],
        )
        sample_entry = next(iter(pft_from_family_summary.values()))
        ut.dict_to_file(
            pft_from_family_summary,
            ut.add_string_to_file_name(file_name, "__PFT__from_Family__counts"),
            column_names=["Family assignment"] + list(sample_entry.keys()),
        )

    # Add PFT combined column to species list
    pft_infos = ut.add_infos_to_list(species_list, pft_combined)

    # Combine all infos to one list, and write to file
    all_infos = ut.add_columns_to_list(species_list, family_extra.values())
    all_infos = ut.add_infos_to_list(
        all_infos,
        family_try,
        family_gbif,
        family_combined,
        plantgrowthform_try,
        woodiness_column_try,
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
    file_name = ut.add_string_to_file_name(input_file, "__AllInfos", new_suffix=".csv")
    column_headers = (
        ["Species", "Species Original"]
        + extra_columns
        + [
            "Family Extra (data source)",
            "Family TRY",
            "Family GBIF",
            "Family Combined (excl. Extra)",
            "PlantGrowthForm TRY",
            "Woodiness Column TRY",
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
    ut.list_to_file(all_infos, file_name, column_names=column_headers)

    return pft_infos, pft_combined


def get_species_data_specs(site_id):
    """
    Get species data specifications for a specific site with grassland observation data.

    Parameters:
        site_id (str): DEIMS ID of the site.

    Returns:
        dict: Dictionary with species data specifications for the site:
            'name' (str): Site name.
            'file_names' (list): Files containing species lists.
            'species_columns' (list): Column names for species list in each file.
            'extra_columns' (list of lists): Additional columns to retrieve from the files.
    """
    # Check if site_id is found in predefined species data specifications
    if site_id in essp.SPECIES_DATA_SPECS_PER_SITE.keys():
        return essp.SPECIES_DATA_SPECS_PER_SITE[site_id]
    else:
        try:
            raise ValueError(
                f"Site ID '{site_id}' not found in species data specifications."
            )
        except ValueError as e:
            logger.error(e)
            raise


def get_pft_from_files(
    location,
    species_data_specs,
    source_folder,
    lookup_tables,
    *,
    save_single_files=True,
    target_folder=None,
):
    """
    Process species data for a site based on species data specifications (data can come from multiple files).

    Parameters:
        location (dict): Dictionary with 'name', 'deims_id', 'lat' and 'lon' keys.
        species_data_specs (dict): Dictionary with species data specifications for the site.
        source_folder (Path): Path to the folder containing species data files.
        save_single_files (bool): Save intermediate results to separate files (default is True).
    """
    if location["name"] == species_data_specs["name"]:
        if target_folder is None:
            target_folder = source_folder

        # Create location subfolder
        target_subfolder = target_folder / "PFT_Mapping"
        target_subfolder.mkdir(parents=True, exist_ok=True)
        formatted_lat = f"lat{location['lat']:.6f}"
        formatted_lon = f"lon{location['lon']:.6f}"
        collect_species_pfts = {}

        for index, file_name in enumerate(species_data_specs["file_names"]):
            if (source_folder / file_name).exists():
                # Copy file with species list to location subfolder, allow overwriting
                shutil.copyfile(source_folder / file_name, target_subfolder / file_name)
                species_column = species_data_specs["species_columns"][index]
                extra_columns = species_data_specs["extra_columns"][index]
                infos_pft, pft_lookup = get_all_infos_and_pft(
                    target_subfolder / file_name,
                    species_column,
                    lookup_tables,
                    extra_columns=extra_columns,
                    save_single_files=save_single_files,
                )

                # Save species infos to location specific files
                species_source = ut.get_source_from_elter_data_file_name(file_name)
                target_file = (
                    target_subfolder
                    / f"{formatted_lat}_{formatted_lon}__PFT__{species_source}.txt"
                )
                ut.list_to_file(
                    infos_pft,
                    target_file,
                    column_names=["Species", "Species Original"]
                    + extra_columns
                    + ["PFT combined"],
                )

                # Combine PFT lookup dictionaries retrieved from different source files
                if collect_species_pfts:
                    collect_species_pfts = resolve_species_info_dicts(
                        "PFT",
                        collect_species_pfts,
                        pft_lookup,
                        info_source_1="previous files",
                        info_source_2=file_name,
                    )
                else:
                    collect_species_pfts = pft_lookup
            else:
                logger.error(
                    f"File '{file_name}' not found in '{source_folder}'. Skipping file."
                )

        # Save combined PFTs to file
        file_name = (
            target_subfolder / f"{formatted_lat}_{formatted_lon}__PFT__allSources.txt"
        )
        ut.dict_to_file(
            collect_species_pfts, file_name, column_names=["Species", "PFT combined"]
        )
    else:
        try:
            raise ValueError(
                f"Site name mismatch for DEIMS ID '{location['deims_id']}': "
                f"'{location['name']}' vs. '{species_data_specs['name']}'."
            )
        except ValueError as e:
            logger.error(e)
            raise


def assign_pfts(deims_id, source_folder, *, target_folder=None, lookup_tables=None):
    """
    Find and process species data for a site based on DEIMS ID.

    Parameters:
        deims_id (str): DEIMS ID of the site.
        source_folder (Path): Path to the folder containing species data files.
        target_folder (Path): Path to the folder to save processed species data.
        lookup_tables (dict): Dictionary with lookup tables for species data (default is None, lookup tables will be created).
    """
    try:
        species_data_specs = get_species_data_specs(deims_id)
    except ValueError:
        logger.error(
            f"DEIMS ID '{deims_id}' not found in species data specifications. Skipping site."
        )
        return

    if target_folder is None:
        target_folder = source_folder

    location = ut.get_deims_coordinates(deims_id)

    if location["found"]:
        if not lookup_tables:
            lookup_tables = get_lookup_tables(force_create=False)

        source_subfolder = source_folder / location["deims_id"]
        target_subfolder = target_folder / location["deims_id"]

        get_pft_from_files(
            location,
            species_data_specs,
            source_subfolder,
            lookup_tables,
            save_single_files=True,  # False to skip saving intermediate files
            target_folder=target_subfolder,
        )
    else:
        logger.error(f"Coordinates not found for DEIMS ID '{deims_id}'. Skipping site.")


def assign_pfts_for_sites(
    site_ids=None, source_folder=None, target_folder=None, lookup_tables=None
):
    """
    Assign Plant Functional Types (PFT) to species for a list of sites.

    Parameters:
        site_ids (list): List of sites by DEIMS IDs (strings).
        source_folder (Path): Path to the folder containing species data files.
        target_folder (Path): Path to the folder to save processed species data.
        lookup_tables (dict): Dictionary with lookup tables for species mapping to PFTs.
    """
    # Examples if not specified otherwise in function call
    if site_ids is None:
        # Specify selected site IDs, these need to be in essp.SPECIES_DATA_SPECS_PER_SITE
        site_ids = essp.ELTER_SITE_IDS
        # site_ids = ["6b62feb2-61bf-47e1-b97f-0e909c408db8"]  # Montagna di Torricchio

    if source_folder is None:
        dotenv_config = dotenv_values(".env")
        source_folder = Path(dotenv_config["ELTER_DATA_PROCESSED"])

    if target_folder is None:
        target_folder = Path.cwd() / "grasslandSites"

    if lookup_tables is None:
        lookup_tables = get_lookup_tables(force_create=False)

    for deims_id in site_ids:
        assign_pfts(
            deims_id,
            source_folder,
            target_folder=target_folder,
            lookup_tables=lookup_tables,
        )


def main():
    """
    Runs the script with default arguments for calling the script.
    """
    parser = argparse.ArgumentParser(
        description="Set default arguments for calling the script."
    )

    # Define command-line arguments
    parser.add_argument(
        "--locations",
        type=ut.parse_locations,
        help="List of location dictionaries containing coordinates ('lat', 'lon') or DEIMS IDs ('deims_id')",
    )
    parser.add_argument(
        "--source_folder",
        type=Path,
        help="Path to the folder containing species data files",
    )
    parser.add_argument(
        "--target_folder",
        type=Path,
        help="Path to the folder to save processed species data",
    )
    parser.add_argument(
        "--lookup_tables",
        type=dict,
        help="Dictionary with lookup tables for species data",
    )
    args = parser.parse_args()

    assign_pfts_for_sites(
        site_ids=args.locations,
        source_folder=args.source_folder,
        target_folder=args.target_folder,
        lookup_tables=args.lookup_tables,
    )


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
