import argparse
import warnings
from pathlib import Path

import assign_pfts as apft
import pandas as pd
import utils as ut


def get_observation_data_specs(site_id):
    """
    Get observation data specifications for a specific site with grassland observation data.

    Parameters:
        site_id (str): DEIMS ID of the site.

    Returns:
        dict: Dictionary with observation data specifications for the site:
            'name' (str): Site name.
            'file_names' (list): Files containing observation data.

    Raises:
        ValueError: If site ID is not found in observation data specifications.
    """
    observation_data_specs_per_site = {
        "11696de6-0ab9-4c94-a06b-7ce40f56c964": {
            "name": "IT25 - Val Mazia/Matschertal",
            "variables": ["cover"],
            "file_names": {"cover": "IT_Matschertal_data_abund.csv"},
            "observation_columns": {"cover": "default"},
            "pft_lookup_files": {
                "cover": "lat46.692800_lon10.615700__PFT__data_abund.txt"
            },
            "pft_lookup_specs": {"cover": "default"},
        },
        "31e67a47-5f15-40ad-9a72-f6f0ee4ecff6": {
            "name": "LTSER Zone Atelier Armorique",
            "variables": ["cover", "indices"],  # indices not considered yet
            "file_names": {
                "cover": "FR_AtelierArmorique_data_cover.csv",
                "indices": "FR_AtelierArmorique_data_indices.csv",
            },
            "observation_columns": {
                "cover": "default",  # "TAXA" uses species codes
                "indices": {
                    "plot": "STATION_CODE",
                    "time": "TIME",
                    "species": "Dominant species",
                    "value": "",
                    "unit": "",
                },
            },
            "pft_lookup_files": {
                "cover": "lat48.600000_lon-1.533330__PFT__reference.txt",
                "indices": "lat48.600000_lon-1.533330__PFT__data_indices.txt",
            },
            "pft_lookup_specs": {
                "cover": {
                    "key_column": "CODE",
                    "info_column": "PFT combined",
                    "info_name": "PFT",
                },
                "indices": "default",
            },
        },
        "324f92a3-5940-4790-9738-5aa21992511c": {
            "name": "Stubai (combination of Neustift meadows and Kaserstattalm)",
            "variables": ["cover"],
            "file_names": {"cover": "AT_Stubai_data_abund.csv"},
            "observation_columns": {"cover": "default"},
            "pft_lookup_files": {
                "cover": "lat47.116700_lon11.300000__PFT__data_abund.txt"
            },
            "pft_lookup_specs": {"cover": "default"},
        },
        "3de1057c-a364-44f2-8a2a-350d21b58ea0": {
            "name": "Obergurgl",
            "variables": ["cover"],  # FREQ (pres/abs in 100 subplots of 1 m²)
            "file_names": {"cover": "AT_Obergurgl_data.csv"},
            "observation_columns": {"cover": "default"},
            "pft_lookup_files": {"cover": "lat46.867100_lon11.024900__PFT__data.txt"},
            "pft_lookup_specs": {"cover": "default"},
        },
        "4ac03ec3-39d9-4ca1-a925-b6c1ae80c90d": {
            "name": "Hochschwab (AT-HSW) GLORIA",
            "variables": ["cover", "abundance"],
            "file_names": {
                "cover": "AT_Hochschwab_data_cover.csv",
                "abundance": "AT_Hochschwab_data_abund.csv",
            },
            "observation_columns": {"cover": "default", "abundance": "default"},
            "pft_lookup_files": {
                "cover": "lat47.622020_lon15.149292__PFT__data_cover.txt",
                "abundance": "lat47.622020_lon15.149292__PFT__data_abund.txt",
            },
            "pft_lookup_specs": {"cover": "default", "abundance": "default"},
        },
        "6ae2f712-9924-4d9c-b7e1-3ddffb30b8f1": {
            "name": "GLORIA Master Site Schrankogel (AT-SCH), Stubaier Alpen",
            "variables": ["cover"],
            "file_names": {"cover": "AT_Schrankogel_data_cover.csv"},
            "observation_columns": {"cover": "default"},
            "pft_lookup_files": {
                "cover": "lat47.041162_lon11.098057__PFT__data_cover.txt"
            },
            "pft_lookup_specs": {"cover": "default"},
        },
        "9f9ba137-342d-4813-ae58-a60911c3abc1": {
            "name": "Rhine-Main-Observatory",
            "variables": ["cover_braun_blanquet"],
            "file_names": {
                "cover_braun_blanquet": "DE_RhineMainObservatory_abund_data.csv"
            },
            "observation_columns": {"cover_braun_blanquet": "default"},
            "pft_lookup_files": {
                "cover_braun_blanquet": "lat50.267302_lon9.269139__PFT__abund_data.txt"
            },
            "pft_lookup_specs": {"cover_braun_blanquet": "default"},
        },
        "c85fc568-df0c-4cbc-bd1e-02606a36c2bb": {
            "name": "Appennino centro-meridionale: Majella-Matese",
            "variables": ["cover"],
            "file_names": {"cover": "IT_AppenninoCentroMeridionale_data_cover.csv"},
            "observation_columns": {"cover": "default"},
            "pft_lookup_files": {
                "cover": "lat42.086116_lon14.085206__PFT__data_cover.txt"
            },
            "pft_lookup_specs": {"cover": "default"},
        },
    }

    if site_id in observation_data_specs_per_site.keys():
        return observation_data_specs_per_site[site_id]
    else:
        raise ValueError(
            f"Site ID '{site_id}' not found in observation data specifications."
        )


def braun_blanquet_to_cover(braun_blanquet_code):
    """
    Map Braun-Blanquet codes to cover values.

    Parameters:
        braun_blanquet_code (str): Braun-Blanquet code.

    Returns:
        float: Cover value for the Braun-Blanquet code, if found, otherwise None.
    """
    braun_blanquet_mapping = {
        "r": 0.1,
        "+": 0.3,
        "1": 2.8,
        "2m": 4.5,
        "2a": 10,
        "2b": 20.5,
        "2": 12.5,  # ??
        "3": 38,  # also saw 37.5
        "4": 62.5,
        "5": 87.5,
    }

    if braun_blanquet_code in braun_blanquet_mapping.keys():
        return braun_blanquet_mapping[braun_blanquet_code]
    else:
        raise ValueError(f"Invalid Braun-Blanquet code '{braun_blanquet_code}'.")


def read_observation_data(
    file_name, *, new_file=None, header_lines=1, csv_delimiter=";"
):
    """
    Read observation data from a file, optionally save to new .txt file.

    Parameters:
        file_name (Path): Path to the file containing observation data.
        new_file (Path): Path to the new file to save observation data (default is None for not saving).
        header_lines (int): Number of header lines in the file (default is 1).
        csv_delimiter (str): Delimiter for .csv files (default is ";").

    Returns:
        list: List of lists with observation data.
    """
    file_extension = file_name.suffix.lower()
    print(f"Reading observation data from '{file_name}' ...")

    if file_extension == ".csv":
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

        # Get column names and entries in one list
        df_column_names = df.columns.tolist()
        observation_data = [df_column_names]
        observation_data.extend(df.values.tolist())

        if new_file:
            ut.list_to_file(observation_data, new_file)

        # Check for duplicates in observation data
        duplicate_rows = ut.count_duplicates(
            observation_data,
            key_column="all",
        )

        if len(duplicate_rows) > 0:
            warnings.warn(
                "Observation data have identical entries! Removing duplicates for subsequent processing.\n"
                "Duplicates:\n"
                + "\n".join(
                    [f"'{entry}' ({count})" for entry, count in duplicate_rows.items()]
                )
            )

            if new_file:
                ut.dict_to_file(
                    duplicate_rows,
                    df_column_names + ["#Duplicate rows"],
                    new_file.with_name(new_file.stem + "_duplicate_rows.txt"),
                )

            # Remove duplicates from observation data, keep first occurrence
            observation_data = ut.remove_duplicates(
                observation_data, duplicates=duplicate_rows
            )

            if new_file:
                ut.list_to_file(
                    observation_data,
                    new_file.with_name(new_file.stem + "_duplicate_rows_removed.txt"),
                )

        # Check for entries that only differ in value, all other columns are the same
        value_column = ut.find_column_index(observation_data, "VALUE")

        if value_column is not None:
            duplicate_entries = ut.count_duplicates(
                observation_data,
                key_column="all",
                columns_to_ignore=[value_column],
            )

            if len(duplicate_entries) > 0:
                warnings.warn(
                    "Observation data have entries that only differ in 'VALUE'!\n"
                    "Duplicates:\n"
                    + "\n".join(
                        [
                            f"'{entry}' ({count})"
                            for entry, count in duplicate_entries.items()
                        ]
                    )
                )

                if new_file:
                    ut.dict_to_file(
                        duplicate_entries,
                        df_column_names[:value_column]
                        + df_column_names[value_column + 1 :]
                        + ["#Duplicate entries"],
                        new_file.with_name(new_file.stem + "_duplicate_entries.txt"),
                    )

        return observation_data
    else:
        warnings.warn(
            f"File extension '{file_extension}' not supported. Skipping file."
        )
        return []


def get_default_observation_columns(variable):
    """
    Get default observation columns for a specific observation variable.

    Parameters:
        variable (str): Observation variable name.

        Returns:
        dict: Dictionary with default column names for the observation variable, including:
            'plot' (str): Column name for plot names.
            'time' (str): Column name for time points.
            'species' (str): Column name for species names.
            'value' (str): Column name for observation values.
            'unit' (str): Column name for observation units.
    """
    default_columns = {
        "plot": "STATION_CODE",
        "time": "TIME",
        "species": "TAXA",
        "value": "VALUE",
        "unit": "UNIT",
    }

    if variable in ["cover", "cover_braun_blanquet", "abundance"]:
        return default_columns
    # elif variable == "indices":  ... add more observation variables here
    else:
        warnings.warn(
            f"Unknown observation variable '{variable}'. Returning default columns."
        )
        return default_columns


def get_default_lookup_specs():
    default_columns = {
        "key_column": "Species Original",
        "info_column": "PFT combined",
        "info_name": "PFT",
    }

    return default_columns


def process_observation_data(
    observation_data, variable, pft_lookup, *, columns="default", new_file=None
):
    # Skip abundance because species-level categories conversion to PFT is not clear
    # 1=very rare, 2=rare, 3=rare-scattered, 4=scattered, 5=scattered-common,
    # 6=common, 7=common-dominant, 8=dominant (see GLORIA manual).
    # Skip indices because conversion to PFT is not clear
    if variable in ["abundance", "indices"]:
        warnings.warn(
            f"'{variable}' data not processed because conversion to PFT is not clear. Skipping variable."
        )
        return

    if columns == "default" or columns is None:
        columns = get_default_observation_columns(variable)

    if new_file:
        target_folder = new_file.parent

    # Reduce observation data to selected columns, remap column names accordingly
    observation_data = ut.get_list_of_columns(observation_data, columns.values())
    columns = {key: idx for idx, key in enumerate(columns.keys())}

    # Process observation data
    plot_names = ut.get_unique_values_from_column(
        observation_data, columns["plot"], header_lines=1
    )

    # TODO: some data can further differ by event_id for identical plot names
    pfts = ["grass", "forb", "legume", "other", "not assigned"]
    observation_pft = pd.DataFrame(
        columns=["plot", "time"]
        + pfts
        + ["unit"]
        + [f"#{pft}" for pft in pfts]
        + ["#invalid"]
    )

    for plot_name in plot_names:
        plot_data = ut.get_rows_with_value_in_column(
            observation_data, columns["plot"], plot_name
        )

        if target_folder:
            file_name = target_folder / f"{variable}__{plot_name.replace("/", "_")}.txt"
            ut.list_to_file(plot_data, file_name, column_names=columns.keys())

        time_points = ut.get_unique_values_from_column(
            plot_data, columns["time"], header_lines=0
        )

        for time_point in time_points:
            time_data = ut.get_rows_with_value_in_column(
                plot_data, columns["time"], time_point
            )
            duplicates = ut.count_duplicates(
                time_data,
                key_column=columns["species"],
                columns_to_ignore=[columns["value"]],
            )
            if len(duplicates) > 0:
                warnings.warn(
                    f"Duplicate species entries in plot '{plot_name}' at time '{time_point}'. Cannot process data from values. Skipping time point."
                )
                new_row = {key: "" for key in observation_pft.columns}
                new_row.update(
                    {
                        "plot": plot_name,
                        "time": time_point,
                        "#invalid": f"{len(duplicates)} non-unique species entries",
                    }
                )
            else:
                # Collect entries and add to PFTs
                pft_values = {key: 0 for key in pfts}
                pft_counts = {key: 0 for key in [f"#{pft}" for pft in pfts]}
                unit = None
                invalid_entries = 0

                for entry in time_data:
                    species = entry[columns["species"]]
                    pft = apft.reduce_pft_info(pft_lookup.get(species, "not found"))
                    value = entry[columns["value"]]
                    unit_here = entry[columns["unit"]]

                    if variable == "cover":
                        try:
                            value = float(value)
                        except ValueError:
                            try:
                                value_found = value
                                value = braun_blanquet_to_cover(value_found)
                                warnings.warn(
                                    f"Value '{value_found}' for '{variable}' of species '{species}' "
                                    f"in plot '{plot_name}' at time '{time_point}' is not a number, "
                                    f"but a Braun-Blanquet code. Mapped to cover value '{value}'."
                                )
                            except ValueError:
                                warnings.warn(
                                    f"Value '{value_found}' for '{variable}' of species '{species}' "
                                    f"in plot '{plot_name}' at time '{time_point}' is not a number. "
                                    "Skipping invalid entry."
                                )

                                invalid_entries += 1
                                continue

                        if not pd.isna(unit_here) and unit_here not in [
                            "%",
                            "percent",
                            "abundance",
                        ]:
                            warnings.warn(
                                f"Invalid unit '{unit_here}' for '{variable}' of species '{species}' "
                                f"in plot '{plot_name}' at time '{time_point}'. Unit should be '%'."
                            )

                    elif variable == "cover_braun_blanquet":
                        try:
                            value = braun_blanquet_to_cover(value)
                        except ValueError:
                            warnings.warn(
                                f"Invalid Braun-Blanquet code '{value}' for '{variable}' of species '{species}' "
                                f"in plot '{plot_name}' at time '{time_point}'. Skipping invalid entry."
                            )
                            invalid_entries += 1
                            continue

                        if (
                            not pd.isna(unit_here)
                            and unit_here.lower() != "braun_blanquet"
                        ):
                            warnings.warn(
                                f"Invalid unit '{unit_here}' for '{variable}' of species '{species}' "
                                f"in plot '{plot_name}' at time '{time_point}'. Unit should be 'Braun_Blanquet'."
                            )

                    pft_values[pft] += value
                    pft_counts[f"#{pft}"] += 1

                    if not pd.isna(unit_here):
                        if unit:
                            if unit_here != unit:
                                warnings.warn(
                                    f"Unit mismatch for '{variable}' of species '{species}' in plot "
                                    f"'{plot_name}' at time '{time_point}': {unit} vs. {unit_here}."
                                )
                        else:
                            unit = unit_here

                # Add PFT values to observation data
                new_row = {
                    "plot": plot_name,
                    "time": time_point,
                    "unit": unit,
                    "#invalid": invalid_entries,
                }
                new_row.update(pft_values)
                new_row.update(pft_counts)

            # Add new row to observation_pft, can be empty if duplicates were found
            new_row_df = pd.DataFrame([new_row])
            observation_pft = pd.concat(
                [observation_pft, new_row_df], ignore_index=True
            )

    # sort observation_pft by time column, and then by plot column
    observation_pft = observation_pft.sort_values(by=["time", "plot"])

    if new_file:
        observation_pft.to_csv(new_file, sep="\t", index=False)

    return observation_pft


def get_observations_from_files(location, observation_data_specs, source_folder):
    """
    Get observation data from files and save to .txt files in location subfolder.

    Parameters:
        location (dict): Dictionary with 'name', 'deims_id', 'lat' and 'lon' keys.
        observation_data_specs (dict): Dictionary with 'name' and 'file_names' keys.
        source_folder (Path): Path to the folder containing observation data files.
    """
    if location["name"] == observation_data_specs["name"]:
        # Create location subfolder
        location_folder = source_folder / location["deims_id"] / "Observations"
        location_folder.mkdir(parents=True, exist_ok=True)
        formatted_lat = f"lat{location['lat']:.6f}"
        formatted_lon = f"lon{location['lon']:.6f}"

        for variable in observation_data_specs["variables"]:
            file_name = observation_data_specs["file_names"][variable]

            if (source_folder / file_name).exists():
                # Read observation data from raw file and save to new .txt file
                observation_source = ut.get_source_from_elter_data_file_name(file_name)
                target_file = (
                    location_folder
                    / f"{formatted_lat}_{formatted_lon}__Observation__Raw__{observation_source}.txt"
                )
                observation_data = read_observation_data(
                    source_folder / file_name, new_file=target_file
                )

                # Read PFT lookup data from PFT mapping file
                lookup_folder = source_folder / location["deims_id"] / "PFT_Mapping"
                lookup_file = (
                    lookup_folder / observation_data_specs["pft_lookup_files"][variable]
                )
                lookup_specs = observation_data_specs["pft_lookup_specs"][variable]

                if lookup_specs == "default" or lookup_specs is None:
                    lookup_specs = get_default_lookup_specs()

                pft_lookup = apft.read_info_dict(
                    lookup_file,
                    lookup_specs["info_name"],
                    key_column=lookup_specs["key_column"],
                    info_column=lookup_specs["info_column"],
                )

                # Process raw observation data
                target_file = (
                    location_folder
                    / f"{formatted_lat}_{formatted_lon}__Observation__PFT__{observation_source}.txt"
                )
                observation_pft = process_observation_data(
                    observation_data,
                    variable,
                    pft_lookup,
                    columns=observation_data_specs["observation_columns"][variable],
                    new_file=target_file,
                )


def data_processing(deims_id, source_folder):
    """
    Find and process observation data for a site based on DEIMS ID.

    Parameters:
        deims_id (str): DEIMS ID of the site.
        source_folder (Path): Path to the folder containing observation data files.
    """
    try:
        observation_data_specs = get_observation_data_specs(deims_id)
    except ValueError:
        warnings.warn(
            f"DEIMS ID '{deims_id}' not found in observation data specifications. Skipping site."
        )
        return

    location = ut.get_deims_coordinates(deims_id)

    if location["found"]:
        get_observations_from_files(location, observation_data_specs, source_folder)
    else:
        warnings.warn(
            f"Coordinates not found for DEIMS ID '{deims_id}'. Skipping site."
        )


def prep_observation_data_for_sites(site_ids=None, source_folder=None):
    """
    Prepare observation data for selected sites.

    Parameters:
        site_ids (list): List of DEIMS IDs of the sites.
        source_folder (Path): Path to the folder containing observation data files.
    """
    # Examples if not specified otherwise in function call
    if site_ids is None:
        # Specify selected site IDs, these need to be in species_data_specs
        site_ids = [
            "11696de6-0ab9-4c94-a06b-7ce40f56c964",  # IT25 - Val Mazia/Matschertal
            "31e67a47-5f15-40ad-9a72-f6f0ee4ecff6",  # LTSER Zone Atelier Armorique
            "324f92a3-5940-4790-9738-5aa21992511c",  # Stubai
            "3de1057c-a364-44f2-8a2a-350d21b58ea0",  # Obergurgl
            "4ac03ec3-39d9-4ca1-a925-b6c1ae80c90d",  # Hochschwab (AT-HSW) GLORIA
            "6ae2f712-9924-4d9c-b7e1-3ddffb30b8f1",  # GLORIA Master Site Schrankogel (AT-SCH), Stubaier Alpen
            "9f9ba137-342d-4813-ae58-a60911c3abc1",  # Rhine-Main-Observatory
            "c85fc568-df0c-4cbc-bd1e-02606a36c2bb",  # Appennino centro-meridionale: Majella-Matese
        ]
        # site_ids = ["9f9ba137-342d-4813-ae58-a60911c3abc1"]  # Rhine-Main-Observatory

    if source_folder is None:
        source_folder = ut.get_package_root() / "grasslandSites"

    for deims_id in site_ids:
        data_processing(deims_id, source_folder)


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
    args = parser.parse_args()

    prep_observation_data_for_sites(
        site_ids=args.locations,
        source_folder=args.source_folder,
    )


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
