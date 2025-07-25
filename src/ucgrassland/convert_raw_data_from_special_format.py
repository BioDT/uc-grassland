"""
Module Name: convert_raw_data_from_special_format.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: March, 2025
Description: Helper functions for converting raw data of eLTER sites to standard format.

Developed in the BioDT project by Thomas Banitz (UFZ) with contributions by Franziska Taubert (UFZ),
Tuomas Rossi (CSC) and Taimur Haider Khan (UFZ).

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


def convert_raw_data_KUL():
    """
    Convert raw data from xls file to standard format for eLTER site
    KUL-site (KU Leuven).
    """
    dotenv_config = dotenv_values(".env")
    source_folder = Path(f"{dotenv_config['ELTER_DATA_PROCESSED']}/KUL-site")
    file_name = "VanMeerbeek_data.xlsx"

    # Read data from xls file
    raw_data = pd.read_excel(source_folder / file_name, sheet_name="Vegetation data")
    new_rows = []
    site_code = "KUL-site"
    vert_offset = "NA"

    # For each row in raw_data, extract the column entries with general information
    for _, row in raw_data.iterrows():
        station_code = row["Plot_ID"]
        time = row["Date"]

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

    # Save new data to a csv file
    new_file_name = "BE_KUL-site_cover__from_VanMeerbeek_data.csv"
    new_data = pd.DataFrame(new_rows)
    new_data.to_csv(source_folder / new_file_name, index=False, sep=";")


def convert_raw_data_CVL():
    """
    Convert raw data from xls file to standard format for eLTER site
    Certoryje-Vojsicke Louky meadows
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

    # # use row 4 for column names and skip first 3 rows

    # raw_data = pd.read_excel(
    #     source_folder / file_name,
    #     sheet_name="List1",
    #     header=3,
    #     skiprows=3,
    # )
    # raw_data = pd.read_excel(source_folder / file_name, sheet_name="List1")
    new_rows = []
    site_code = "https://deims.org/4c8082f9-1ace-4970-a603-330544f22a23"
    vert_offset = "NA"

    # For each row in raw_data, extract the column entries with general information
    for _, row in raw_data.iterrows():
        station_code = row["Sample (relevé) code"]
        time = row["Date of data collecting"]

        # Extract values for each species column (E to end)
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

    # Save new data to a csv file
    new_file_name = "CZ_Certoryje-Vojsice_cover__from_regrassed_fields_Bile_Karpaty.csv"
    new_data = pd.DataFrame(new_rows)
    new_data.to_csv(source_folder / new_file_name, index=False, sep=";")


if __name__ == "__main__":
    convert_raw_data_KUL()
    convert_raw_data_CVL()
    # convert_raw_data_MAM_C()
    # convert_raw_data_ASQ_C()
