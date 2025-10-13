"""
Module Name: convert_raw_data_from_special_format.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: March, 2025
Description: Helper functions for converting raw data of eLTER sites to standard format.

Developed in the BioDT project (until 2025-05) by Thomas Banitz (UFZ) with contributions by Franziska Taubert (UFZ),
Tuomas Rossi (CSC) and Taimur Haider Khan (UFZ).

Further developed (from 2025-06) by Thomas Banitz (UFZ) with contributions by Franziska Taubert (UFZ).

Copyright (C) 2025
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
"""

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import dotenv_values

from ucgrassland.logger_config import logger


def convert_raw_data_MAM_C():
    """
    Convert raw data from xls file to standard format for eLTER site
    c85fc568-df0c-4cbc-bd1e-02606a36c2bb (Appennino centro-meridionale: Majella-Matese).
    """
    dotenv_config = dotenv_values(".env")
    source_folder = Path(
        f"{dotenv_config['ELTER_DATA_PROCESSED']}/c85fc568-df0c-4cbc-bd1e-02606a36c2bb"
    )
    file_name = "FEM_Revised.xlsx"

    # Read data from xls file
    raw_data = pd.read_excel(source_folder / file_name, sheet_name="DATA_COL")
    new_rows = []

    # For each row in raw_data, extract the column entries with general information
    for _, row in raw_data.iterrows():
        site_code = row["SITE_CODE"]
        station_code = row["STATION_CODE"]
        vert_offset = row["VERT_OFFSET"]
        time = row["TIME"]

        if pd.isna(vert_offset):
            vert_offset = "NA"

        # Extract values for each species column (E to end)
        for column in raw_data.columns[4:]:
            column_name = column
            column_value = row[column]

            # Add new row if column value is finite and greater than 0
            if pd.notna(column_value) and column_value > 0:
                new_rows.append(
                    {
                        "SITE_CODE": site_code,
                        "STATION_CODE": station_code,
                        "VERT_OFFSET": vert_offset,
                        "VARIABLE": "Cover",
                        "TIME": time,
                        "TAXA": column_name,
                        "VALUE": column_value,
                        "UNIT": "%",
                    }
                )

    # Save new data to a csv file
    new_file_name = "IT_AppenninoCentroMeridionale_data_cover__from_FEM_Revised.csv"
    new_data = pd.DataFrame(new_rows)
    new_data.to_csv(source_folder / new_file_name, index=False, sep=";")


def convert_raw_data_ASQ_C():
    """
    Convert raw data from xls file to standard format for eLTER site
    270a41c4-33a8-4da6-9258-2ab10916f262 (AgroScapeLab Quillow (ZALF))"
    """
    dotenv_config = dotenv_values(".env")
    source_folder = Path(
        f"{dotenv_config['ELTER_DATA_PROCESSED']}/270a41c4-33a8-4da6-9258-2ab10916f262"
    )
    file_name = "Coverage_per_species_ReplicationPlotYear.csv"
    site_code = "https://deims.org/270a41c4-33a8-4da6-9258-2ab10916f262"

    # Read data from csv file
    raw_data = pd.read_csv(source_folder / file_name, sep=";")
    new_rows = []

    # Read additional data for replication dates from csv file
    file_name = "Species_number_Coverage_ReplicationPlotFieldYearMonth.csv"
    time_data = pd.read_csv(source_folder / file_name, sep=";")

    # For each row in raw_data, extract the column entries with general information
    for _, row in raw_data.iterrows():
        year = row["Year"]
        station_code = row["Plot"]
        replication = row["Replication"]

        # Extract time from time_data, find month for row that matches Plot, Year and Replication
        # check if there is only one row that matches the criteria

        months = time_data[
            (time_data["Plot"] == station_code)
            & (time_data["Year"] == year)
            & (time_data["Replication"] == replication)
        ]["Month"].values

        if len(months) == 1:
            # set date to 15th of month in format DD.MM.YYYY
            time = f"15.{months[0]:02d}.{year}"
        elif len(months) == 0:
            logger.warning(
                f"No month found in time data for Plot {station_code}, Year {year}, Replication {replication}."
            )
            time = f"{year}"
        else:
            # set date to mean each month found
            dates_ordinal = [datetime(year, month, 15).toordinal() for month in months]
            time = datetime.fromordinal(
                int(sum(dates_ordinal) / len(dates_ordinal))
            ).strftime("%d.%m.%Y")

            logger.warning(
                f"Multiple months found ({months}) in time data for Plot {station_code}, Year {year}, Replication {replication}. "
                f"Using mean date: {time}."
            )

        # Extract values for each species column (E to end)
        for column in raw_data.columns[3:]:
            column_name = column
            column_value = row[column]
            # check if column value is float
            if pd.notna(column_value) and not isinstance(column_value, (float)):
                # replace commas
                if isinstance(column_value, str):
                    if "," in column_value:
                        logger.warning(
                            f"Replacing comma(s) in value '{column_value}' in column {column}."
                        )
                        column_value = column_value.replace(",", "")

                    column_value = float(column_value)
                else:
                    logger.warning(
                        f"Value '{column_value}' in column {column} is not a float, string or nan."
                    )
                    column_value = None

            # Add new row if column value is finite and greater than 0
            if column_value and column_value > 0:
                new_rows.append(
                    {
                        "SITE_CODE": site_code,
                        "STATION_CODE": station_code,
                        "REPLICATION": replication,
                        "VARIABLE": "Cover",
                        "TIME": time,
                        "TAXA": column_name,
                        "VALUE": column_value,
                        "UNIT": "%",
                    }
                )

    # Save new data to a csv file
    new_file_name = "DE_AgroScapeQuillow_data_cover__from_SpeciesFiles.csv"
    new_data = pd.DataFrame(new_rows)
    new_data.to_csv(source_folder / new_file_name, index=False, sep=";")


def convert_raw_data_KUL(forbidden_cover_threshold=0):
    """
    Convert raw data from xls file to standard format for eLTER site
    KUL-site (KU Leuven).

    Parameters
    ----------
    forbidden_cover_threshold : float
        The threshold for excluding plots based on cover of non-grassland species (default: 0).
    """
    dotenv_config = dotenv_values(".env")
    source_folder = Path(f"{dotenv_config['ELTER_DATA_PROCESSED']}/KUL-site")
    file_name = "VanMeerbeek_data.xlsx"
    plots_excluded = []

    # Read other data from xls file
    other_data = pd.read_excel(source_folder / file_name, sheet_name="Other data")

    for _, row in other_data.iterrows():
        station_code = row["Plot_ID"]
        cover_woody = float(row["Cover_woody"]) if pd.notna(row["Cover_woody"]) else 0.0
        cover_reed = float(row["Cover_reed"]) if pd.notna(row["Cover_reed"]) else 0.0
        forbidden_cover = cover_woody + cover_reed

        if forbidden_cover > forbidden_cover_threshold:
            logger.warning(
                f"Excluding plot {station_code} due to cover of non-grassland species (woody, reed): "
                f"{forbidden_cover:.2f} > {forbidden_cover_threshold}."
            )
            plots_excluded.append(station_code)

    # Read data from xls file
    raw_data = pd.read_excel(source_folder / file_name, sheet_name="Vegetation data")
    new_rows = []
    site_code = "KUL-site"
    vert_offset = "NA"

    # OPTION: read other data with "year since last mowing" entries and add...

    if len(raw_data) == len(other_data):
        # check that each entry in Plot_ID column of raw_data is also in other_data
        for plot_id in raw_data["Plot_ID"]:
            if plot_id not in other_data["Plot_ID"].values:
                raise ValueError(
                    f"Plot ID {plot_id} in 'Vegetation data' not found in 'Other data'."
                )
    else:
        raise ValueError(
            f"Number of rows in 'Vegetation data' ({len(raw_data)}) and in 'Other data' ({len(other_data)}) do not match."
        )

    # For each row in raw_data, extract the column entries with general information
    for _, row in raw_data.iterrows():
        station_code = row["Plot_ID"]
        time = row["Date"]

        if station_code in plots_excluded:
            # logger.info(f"Skipping excluded plot {station_code}.")
            continue

        # Extract values for each species column (E to end)
        for column in raw_data.columns[2:]:
            column_name = column.replace("_", " ")
            column_value = row[column]

            # Add new row if column value is finite and greater than 0
            if pd.notna(column_value) and column_value > 0:
                new_rows.append(
                    {
                        "SITE_CODE": site_code,
                        "STATION_CODE": station_code,
                        "VERT_OFFSET": vert_offset,
                        "VARIABLE": "Cover",
                        "TIME": time,
                        "TAXA": column_name,
                        "VALUE": column_value,
                        "UNIT": "%",
                    }
                )

    if plots_excluded:
        logger.warning(
            f"Excluded {len(plots_excluded)} of {len(raw_data)} plots for site KUL-site: {plots_excluded}."
        )

    # Save new data to a csv file
    new_file_name = "BE_KUL-site_cover__from_VanMeerbeek_data.csv"
    new_data = pd.DataFrame(new_rows)
    new_data.to_csv(source_folder / new_file_name, index=False, sep=";")


def convert_raw_data_CVL(moss_cover_threshold=50):
    """
    Convert raw data from xls file to standard format for eLTER site
    Certoryje-Vojsicke Louky meadows

    Parameters
    ----------
    moss_cover_threshold : float
        The threshold for excluding plots based on moss cover (default: 50%).
    """
    dotenv_config = dotenv_values(".env")
    source_folder = Path(
        f"{dotenv_config['ELTER_DATA_PROCESSED']}/4c8082f9-1ace-4970-a603-330544f22a23"
    )
    file_name = "4c8082f9-1ace-4970-a603-330544f22a23_regrassed_fields_Bile Karpaty__Czech_Republic__Version_2020_eLTER.xlsx"

    # Read data from xls file
    # read column wise, use column B for names and other columns for values
    raw_data = pd.read_excel(source_folder / file_name, sheet_name="List1")

    # Assume column B is at index 1 (zero-based), and columns C onward are values
    var_names = raw_data.iloc[:, 1]  # Column B for variable names
    var_values = raw_data.iloc[:, 2:-2]  # Columns C to second last column for values

    # Set variable names as index
    raw_data = var_values.T
    raw_data.columns = var_names

    new_rows = []
    site_code = "https://deims.org/4c8082f9-1ace-4970-a603-330544f22a23"
    vert_offset = "NA"

    plots_excluded = []

    # For each row in raw_data, extract the column entries with general information
    for _, row in raw_data.iterrows():
        station_code = row["Sample (relevé) code"]
        time = row["Date of data collecting"]
        moss_cover = row["Cover moss layer (%)"]

        if pd.notna(moss_cover) and float(moss_cover) > moss_cover_threshold:
            logger.warning(
                f"Excluding plot {station_code} due to moss cover {moss_cover} > {moss_cover_threshold}."
            )
            plots_excluded.append(station_code)
            continue

        # Extract values for each species column (in transposed data)
        for column in raw_data.columns[32:]:
            column_value = row[column]

            # Add new row if column value is finite and greater than 0
            if pd.notna(column_value) and column_value > 0:
                new_rows.append(
                    {
                        "SITE_CODE": site_code,
                        "STATION_CODE": station_code,
                        "VERT_OFFSET": vert_offset,
                        "VARIABLE": "Cover",
                        "TIME": time,
                        "TAXA": column,
                        "VALUE": column_value,
                        "UNIT": "%",
                    }
                )
    if plots_excluded:
        logger.warning(
            f"Excluded {len(plots_excluded)} of {len(raw_data)} plots for site CVL: {plots_excluded}."
        )

    # Save new data to a csv file
    new_file_name = "CZ_Certoryje-Vojsice_cover__from_regrassed_fields_Bile_Karpaty.csv"
    new_data = pd.DataFrame(new_rows)
    new_data.to_csv(source_folder / new_file_name, index=False, sep=";")


def convert_raw_data_BEXIS(forbidden_cover_threshold=0, moss_cover_threshold=50.0):
    """
    Convert raw data from xls file to standard format for eLTER site
    BEXIS-sites (Germany).

    Parameters
    ----------
    forbidden_cover_threshold : float
        The threshold for excluding plots based on cover of non-grassland species (default: 0).
    """
    dotenv_config = dotenv_values(".env")
    site_ids = [
        "4d7b73d7-62da-4d96-8cb3-3a9a744ae1f4",  # BEXIS-site-SEG
        "56c467e5-093f-4b60-b5cf-880490621e8d",  # BEXIS-site-HEG
        "a51f9249-ddc8-4a90-95a8-c7bbebb35d29",  # BEXIS-site-AEG
    ]
    site_names = ["SEG", "HEG", "AEG"]
    vert_offset = "NA"

    # Mapping from German to English month names
    month_map = {
        "Jan": "01",
        "Feb": "02",
        "Mär": "03",
        "Apr": "04",
        "Mai": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Okt": "10",
        "Nov": "11",
        "Dez": "12",
    }

    pft_map = {
        "gräser": "grass",
        "leguminosen": "legume",
        "kräuter": "forb",
        "bäume und sträucher": "(woody)",
        "farngewächse": "(fern)",
    }

    first_observation_row = 13
    valid_entries = ["gräser", "leguminosen", "kräuter"]
    forbidden_entries = ["bäume und sträucher", "farngewächse"]
    pft_list = valid_entries + forbidden_entries

    # Read data from xls files
    for site_name in site_names:
        new_rows = []
        source_folder = Path(
            f"{dotenv_config['ELTER_DATA_PROCESSED']}/{site_ids[site_names.index(site_name)]}"
        )
        file_name = f"{site_name[0]}_2024.xlsx"
        sheet_names = pd.ExcelFile(source_folder / file_name).sheet_names
        plots_excluded = []

        for station_code in sheet_names:
            raw_data = pd.read_excel(source_folder / file_name, sheet_name=station_code)
            # get indexes for year columns based on conditions
            value_columns = (raw_data.columns.str.len() == 4) & (
                raw_data.columns.str.startswith("20")
            )
            # Assume column A is at index 0 (zero-based), and columns B onward are values
            var_names = raw_data.iloc[:, 0]  # Column A for variable names
            var_values = raw_data.iloc[:, value_columns]

            # Set variable names as index
            raw_data = var_values.T
            raw_data.columns = var_names

            # Error if first observation row is not "Arten"
            if raw_data.columns[first_observation_row].lower() != "arten":
                raise ValueError(
                    f"Unexpected table format in observations for plot {station_code}: "
                    f"Row {first_observation_row} should be 'Arten', but is '{raw_data.columns[first_observation_row]}'."
                )

            # convert all entries from first observation row to float
            columns_to_convert = raw_data.columns[first_observation_row:].tolist() + [
                "Deckung Sträucher",
                "Deckung Kräuter",
                "Deckung Moose",
                "Deckung Flechten",
                "Deckung offener Boden",
                "Artenzahl",
                "Biomasse (dt/ha)",
            ]
            # columns_to_convert = remove_duplicates(columns_to_convert)
            columns_to_convert = np.unique(columns_to_convert)

            for column in columns_to_convert:
                # Merge multiple columns for same species
                if isinstance(raw_data[column], pd.DataFrame):
                    logger.warning(
                        f"Found {raw_data[column].shape[1]} data rows for species {column} "
                        f"and plot {station_code}. Merging rows."
                    )
                    merged = []

                    for idx, row in raw_data[column].iterrows():
                        non_nan = row.dropna()

                        if len(non_nan) == 0:
                            merged.append(np.nan)
                        elif len(non_nan) == 1:
                            merged.append(float(non_nan.iloc[0]))
                        else:
                            raise ValueError(
                                f"Conflicting entries for species '{raw_data[column].columns[0]}' in year {idx}: {list(non_nan)}"
                            )

                    column_idx = raw_data.columns.get_loc(column).argmax()
                    merged_column = pd.Series(
                        merged,
                        index=raw_data[column].index,
                        name=raw_data[column].columns[0],
                    )
                    raw_data.drop(columns=[column], inplace=True)
                    raw_data.insert(column_idx, column, merged_column)
                else:
                    raw_data[column] = pd.to_numeric(raw_data[column], errors="coerce")

            # Search row indexes for valid and forbidden entries
            valid_entry_indexes = {}
            forbidden_entry_indexes = {}

            for idx, column in enumerate(raw_data.columns):
                for valid_entry in valid_entries:
                    if column.lower() == valid_entry:
                        valid_entry_indexes[valid_entry] = idx
                        break

                for forbidden_entry in forbidden_entries:
                    if column.lower() == forbidden_entry:
                        forbidden_entry_indexes[forbidden_entry] = idx
                        break

            if forbidden_entry_indexes:
                # Invalid entries are expected at the end after the valid entries
                if max(valid_entry_indexes.values()) > min(
                    forbidden_entry_indexes.values()
                ):
                    raise ValueError(
                        f"Plot {station_code} has valid entries after entries for non-grassland species."
                    )
                else:
                    logger.warning(
                        f"Plot {station_code} has entries for non-grassland species."
                    )

                # Get sum of all entries from min(forbidden_entry_indexes.values()) to end for each row
                for year, row in raw_data.iterrows():
                    sum_forbidden = 0

                    for column in raw_data.columns[
                        min(forbidden_entry_indexes.values()) :
                    ]:
                        if pd.notna(row[column]):
                            sum_forbidden += row[column]

                    if sum_forbidden > forbidden_cover_threshold:
                        logger.warning(
                            f"Excluding plot {station_code} due to sum of cover for non-grassland species in year {year}: "
                            f"{sum_forbidden} > {forbidden_cover_threshold}."
                        )
                        plots_excluded.append(station_code)
                        break

            if station_code not in plots_excluded:
                # NOTE: select types of non-grassland species to consider for exclusion
                forbidden_cover = raw_data["Deckung Sträucher"].fillna(0)
                moss_cover = raw_data["Deckung Moose"].fillna(0) + raw_data[
                    "Deckung Flechten"
                ].fillna(0)

                if forbidden_cover.max() > forbidden_cover_threshold:
                    logger.warning(
                        f"Excluding plot {station_code} due to maximum total cover of non-grassland species (shrubs): "
                        f"{forbidden_cover.max()} > {forbidden_cover_threshold}."
                    )
                    plots_excluded.append(station_code)
                elif moss_cover.max() > moss_cover_threshold:
                    logger.warning(
                        f"Excluding plot {station_code} due to maximum moss cover (moss + lichens): "
                        f"{moss_cover.max()} > {moss_cover_threshold}."
                    )
                    plots_excluded.append(station_code)

            if station_code in plots_excluded:
                continue

            # For each row in raw_data, extract the column entries with general information, rows should be named by year now
            for year, row in raw_data.iterrows():
                # reset pft to be sure it is not carried over from previous year or site
                pft = "NA"

                herb_cover = row["Deckung Kräuter"]
                open_soil_cover = row["Deckung offener Boden"]
                biomass_g_m2 = round(row["Biomasse (dt/ha)"] * 10, 2)
                # dt to g: * 100000, ha to m2: / 10000
                species_count = (
                    int(row["Artenzahl"]) if pd.notna(row["Artenzahl"]) else 0
                )
                entries_count = len(new_rows)  # track to check added entries

                # read date from german format dd. mmm, e.g. 15. Jan
                obs_date = row["Datum"]

                if pd.isna(obs_date) or obs_date in ["", "NANA", "NA. NA"]:
                    if species_count > 0:
                        logger.warning(
                            f"Missing observation date ('{obs_date}') for "
                            f"plot {station_code}, year {year}. Assuming default date {year}-05-20."
                        )
                    obs_date = "20. Mai"  # assume default date

                day_month = obs_date.split()

                if len(day_month) == 2:
                    month = month_map[day_month[1][:3]]

                    if day_month[0].startswith("-") or day_month[0] in ["0.", "00."]:
                        day = "01"
                        logger.warning(
                            f"Incorrect observation date ('{obs_date}') for "
                            f"plot {station_code}, year {year}. Assuming date {year}-{month}-{day}."
                        )
                    else:
                        day = day_month[0].rstrip(".").zfill(2)

                    time = f"{year}-{month}-{day}"
                else:
                    raise ValueError(
                        f"Unexpected date format for year {year}: {day_month}"
                    )

                # Extract values for each species column
                for column in raw_data.columns[first_observation_row + 1 :]:
                    if column.lower() in pft_list:
                        pft = pft_map[column.lower()]
                    else:
                        if pft == "NA":
                            raise ValueError(
                                f"Missing PFT information for species '{column}' in plot {station_code}, year {year}."
                            )

                        column_value = row[column]

                        # Add new row if column value is finite and greater than 0
                        if pd.notna(column_value) and column_value > 0:
                            new_rows.append(
                                {
                                    "SITE_CODE": "BEXIS-site-" + site_name,
                                    "STATION_CODE": station_code,
                                    "VERT_OFFSET": vert_offset,
                                    "VARIABLE": "Cover",
                                    "TIME": time,
                                    "TAXA": column,
                                    "VALUE": column_value,
                                    "UNIT": "%",
                                    "PFT_ORIGINAL": pft,
                                    " ": "",
                                    "TOTAL_HERB_COVER": herb_cover,
                                    "OPEN_SOIL_COVER": open_soil_cover,
                                    "TOTAL_BIOMASS_G_M2": biomass_g_m2,
                                }
                            )

                if species_count != len(new_rows) - entries_count:
                    logger.warning(
                        f"Species count mismatch for year {year}: "
                        f"expected {species_count} from observation file ('Artenzahl'), "
                        f"but found {len(new_rows) - entries_count} species entries."
                    )
                elif species_count == 0:
                    logger.warning(
                        f"No species observations found for plot {station_code}, year {year}."
                    )

        if plots_excluded:
            logger.warning(
                f"Excluded {len(plots_excluded)} of {len(sheet_names)} plots for site BEXIS-site-{site_name}: {plots_excluded}."
            )

        # Save new data to a csv file
        new_file_name = (
            f"DE_BEXIS-site-{site_name}_data_cover__from_31973_5_Dataset.csv"
        )
        new_data = pd.DataFrame(new_rows)
        new_data.to_csv(source_folder / new_file_name, index=False, sep=";")


if __name__ == "__main__":
    forbidden_cover_threshold = 5.0
    moss_cover_threshold = 100.0
    convert_raw_data_BEXIS(
        forbidden_cover_threshold=forbidden_cover_threshold,
        moss_cover_threshold=moss_cover_threshold,
    )
    convert_raw_data_KUL(forbidden_cover_threshold=forbidden_cover_threshold)
    convert_raw_data_CVL(moss_cover_threshold=moss_cover_threshold)
    convert_raw_data_MAM_C()
    # convert_raw_data_ASQ_C()
