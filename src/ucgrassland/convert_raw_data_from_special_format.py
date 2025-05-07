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

import warnings
from datetime import datetime
from pathlib import Path

import pandas as pd


def convert_raw_data_MAM_C():
    """
    Convert raw data from xls file to standard format for eLTER site
    c85fc568-df0c-4cbc-bd1e-02606a36c2bb (Appennino centro-meridionale: Majella-Matese).
    """
    source_folder = Path(
        "c:/Users/banitz/Nextcloud/Cloud/BioDT_ExchangeFranziThomas/"
        "BYODE/eLTER_DataCall/data_processed/c85fc568-df0c-4cbc-bd1e-02606a36c2bb"
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
    source_folder = Path(
        "c:/Users/banitz/Nextcloud/Cloud/BioDT_ExchangeFranziThomas/"
        "BYODE/eLTER_DataCall/data_processed/270a41c4-33a8-4da6-9258-2ab10916f262"
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
            warnings.warn(
                f"No month found in time data for Plot {station_code}, Year {year}, Replication {replication}",
                UserWarning,
            )
            time = f"{year}"
        else:
            # set date to mean each month found
            dates_ordinal = [datetime(year, month, 15).toordinal() for month in months]
            time = datetime.fromordinal(
                int(sum(dates_ordinal) / len(dates_ordinal))
            ).strftime("%d.%m.%Y")

            warnings.warn(
                f"Multiple months found ({months}) in time data for Plot {station_code}, Year {year}, Replication {replication}. "
                f"Using mean date: {time}.",
                UserWarning,
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
                        warnings.warn(
                            f"Replacing comma(s) in value '{column_value}' in column {column}.",
                            UserWarning,
                        )
                        column_value = column_value.replace(",", "")

                    column_value = float(column_value)
                else:
                    warnings.warn(
                        f"Value '{column_value}' in column {column} is not a float, string or nan.",
                        UserWarning,
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


if __name__ == "__main__":
    # convert_raw_data_MAM_C()
    convert_raw_data_ASQ_C()
