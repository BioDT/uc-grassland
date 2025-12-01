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

import geopandas as gpd
import numpy as np
import pandas as pd
from dotenv import dotenv_values

from ucgrassland.assign_pfts import get_gbif_family
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
                column_name = column_name.replace("Ã‚Â", "")
                column_name = column_name.replace("Â", "")
                column_name = column_name.replace("Ã", "")
                column_name = column_name.replace("\xa0", " ")
                column_name = column_name.strip()
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
    pft_dict = {}

    # Read other data from xls file
    other_data = pd.read_excel(source_folder / file_name, sheet_name="Other data")

    for _, row in other_data.iterrows():
        station_code = row["Plot_ID"]
        cover_woody = float(row["Cover_woody"]) if pd.notna(row["Cover_woody"]) else 0.0
        # cover_reed = float(row["Cover_reed"]) if pd.notna(row["Cover_reed"]) else 0.0
        forbidden_cover = cover_woody  # + cover_reed

        if forbidden_cover > forbidden_cover_threshold:
            logger.warning(
                f"Excluding plot {station_code} due to cover of non-grassland species (woody): "  # (woody, reed)
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
            pft = pft_dict.get(column_name)

            if pft is None:
                pft = get_pft_KUL(column_name)
                pft_dict[column_name] = pft

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
                        "PFT_ORIGINAL": pft,
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

    # Read and extract plot locations from shapefile
    shapefile_path = source_folder / "Natuurgebieden" / "GPS_data.shp"
    output_csv_path = source_folder / "BE_KUL-site_station_from_shape.csv"
    extract_plot_locations(shapefile_path, output_csv_path, site_code=site_code)


def extract_plot_locations(shapefile_path, output_csv_path, site_code="KUL-site"):
    """
    Extract plot locations from shapefile and save to CSV format.

    Parameters
    ----------
    shapefile_path : str or Path
        Path to the input shapefile.
    output_csv_path : str or Path
        Path to the output CSV file.
    site_code : str
        The site code to be used in the output (default: "KUL-site").
    """
    try:
        # Read the shapefile
        gdf = gpd.read_file(shapefile_path)

        # Convert to WGS84 (EPSG:4326) if not already in that CRS
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")

        # Extract coordinates
        gdf["LAT"] = gdf.geometry.y
        gdf["LON"] = gdf.geometry.x

        for _, row in gdf.iterrows():
            if not np.isclose(row["LAT"], row["lat_dec"], atol=1e-6, rtol=0):
                logger.warning(
                    f"Latitude mismatch for plot {row['Proefvlak']}: {row['LAT']} (from geometry) != {row['lat_dec']} (from attribute). Using {row['LAT']}."
                )

                if not np.isclose(row["LAT"], row["lat_dec"], atol=1e-4, rtol=0):
                    logger.error(
                        f"Significant latitude difference for plot {row['Proefvlak']}: {row['LAT']} (from geometry) vs {row['lat_dec']} (from attribute)."
                    )

            if not np.isclose(row["LON"], row["lon_dec"], atol=1e-6, rtol=0):
                logger.warning(
                    f"Longitude mismatch for plot {row['Proefvlak']}: {row['LON']} (from geometry) != {row['lon_dec']} (from attribute). Using {row['LON']}."
                )

                if not np.isclose(row["LON"], row["lon_dec"], atol=1e-4, rtol=0):
                    logger.error(
                        f"Significant longitude difference for plot {row['Proefvlak']}: {row['LON']} (from geometry) vs {row['lon_dec']} (from attribute)."
                    )

        # Rename station codes, e.g. KVM 80A --> KVM_80
        gdf["STATION_CODE"] = (
            gdf["Proefvlak"].str.replace(" ", "_").str.replace("A", "")
        )

        # Create final dataframe with required columns
        shape_df = pd.DataFrame(
            {
                "SITE_CODE": site_code,
                "STATION_CODE": gdf["STATION_CODE"],
                "LAT": gdf["LAT"],
                "LON": gdf["LON"],
            }
        )

        # Save to CSV
        shape_df.to_csv(output_csv_path, index=False, sep=";")

    except Exception as e:
        print(f"Error processing shapefile: {e}")
        return None


def get_pft_KUL(species_name):
    """
    Get plant functional type (PFT) for a given species name based on predefined mappings.

    Parameters
    ----------
    species_name : str
        The name of the species.

    Returns
    -------
    str
        The corresponding PFT ("woody", "reed", "grass", "legume", or "forb").
    """
    # Woody species according to van Meerbeek, personal communication
    if species_name in [
        "Acer pseudoplatanus",
        "Alnus glutinosa",
        "Amelanchier lamarckii",
        "Betula pendula",
        "Betula pubescens",
        "Calluna vulgaris",
        "Crataegus monogyna",
        "Erica cinerea",
        "Erica tetralix",
        "Frangula alnus",
        "Fraxinus excelsior",
        "Genista anglica",
        "Hippophae rhamnoides",
        "Myrica gale",
        "Pinus sylvestris",
        "Populus tremula",
        "Prunus avium",
        "Quercus petraea",
        "Quercus robur",
        "Quercus rubra",
        "Salix caprea",
        "Salix cinerea",
        "Salix repens",
        "Sorbus aucuparia",
        "Vaccinium myrtillus",
    ]:
        return "(woody)"

    # Family Poaceae, but treated as separate PFT here
    if species_name in ["Phragmites australis"]:
        return "(reed)"

    # Get GBIF family, can be "not found" with an error message
    family = get_gbif_family(species_name)

    if family in ["Poaceae", "Cyperaceae", "Juncaceae"]:
        return "grass"

    if family == "Fabaceae":
        return "legume"

    # All other species are treated as forb, including "not found"
    return "forb"


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


def convert_raw_data_MDT():
    dotenv_config = dotenv_values(".env")
    source_folder = Path(
        f"{dotenv_config['ELTER_DATA_PROCESSED']}/6b62feb2-61bf-47e1-b97f-0e909c408db8"
    )
    file_name = "Longterm_monitoring_plant_diversity_data_Montagna_Torricchio_strict_Nature_Reserve_Italy_v.2.xlsx"
    site_code = "https://deims.org/6b62feb2-61bf-47e1-b97f-0e909c408db8"

    # Read data from xls file
    raw_plot_info = pd.read_excel(source_folder / file_name, sheet_name="Plot info")
    raw_flora_plot = pd.read_excel(source_folder / file_name, sheet_name="Flora plot")
    raw_flora_subplot = pd.read_excel(
        source_folder / file_name, sheet_name="Flora subplots"
    )

    # convert plot names to strings with leading zeros, e.g. 1 --> 01
    raw_plot_info["Plot"] = raw_plot_info["Plot"].apply(lambda x: f"{x:02d}")
    raw_flora_plot["Plot"] = raw_flora_plot["Plot"].apply(lambda x: f"{x:02d}")
    raw_flora_subplot["Plot"] = raw_flora_subplot["Plot"].apply(lambda x: f"{x:02d}")

    # Create station file
    station_data = raw_plot_info

    # rename columns
    station_data = station_data.rename(columns={"Plot": "STATION_CODE"})
    station_data = station_data.rename(columns={"X coord. (EPSG:4326)": "LON"})
    station_data = station_data.rename(columns={"Y coord. (EPSG:4326)": "LAT"})
    station_data = station_data.rename(columns={"Altitude (m a.s.l.)": "ALTITUDE"})

    # drop all other columns, change order of lat and lon columns
    station_data = station_data[["STATION_CODE", "LAT", "LON", "ALTITUDE"]]

    # only keep unique rows
    station_data = station_data.drop_duplicates()

    # check if number of rows matches number of unique station codes
    assert len(station_data) == station_data["STATION_CODE"].nunique(), (
        "Number of rows in station data does not match number of unique station codes."
    )

    # add PLOTSIZE column at end
    station_data.insert(len(station_data.columns), "PLOTSIZE", 100)

    # match station file entries with plot and subplot data
    subplot_cover_years = [2002, 2003]
    plot_cover_years = [2015, 2020, 2024]

    # drop rows in raw_flora_plot that are not in plot_cover_years, same for subplot
    raw_flora_plot = raw_flora_plot[raw_flora_plot["Year"].isin(plot_cover_years)]
    raw_flora_subplot = raw_flora_subplot[
        raw_flora_subplot["Year"].isin(subplot_cover_years)
    ]

    # get unique station codes from merged plot entries in plot and subplot data
    plot_names = pd.concat([raw_flora_plot["Plot"], raw_flora_subplot["Plot"]]).unique()

    # check if station data contains all plot names
    missing_plots = set(plot_names) - set(station_data["STATION_CODE"])

    if missing_plots:
        logger.warning(f"Missing plots in station data: {missing_plots}")

    # check if station data contains any plots not in plot names
    extra_plots = set(station_data["STATION_CODE"]) - set(plot_names)

    if extra_plots:
        logger.warning(f"Deleting extra plots in station data: {extra_plots}")
        station_data = station_data[~station_data["STATION_CODE"].isin(extra_plots)]
        station_data = station_data.reset_index(drop=True)

    new_rows = []

    # create addtional station codes from combining plot and subplot ids
    for _, row in raw_flora_subplot.iterrows():
        plot_id = row["Plot"]
        subplot_id = row["Subplot"]
        station_code = f"{plot_id}_{subplot_id}"

        if station_code not in [row["STATION_CODE"] for row in new_rows]:
            # get lat, lon, altitude from plot id
            plot_row = station_data[station_data["STATION_CODE"] == plot_id]
            if plot_row.empty:
                raise ValueError(
                    f"Plot ID {plot_id} not found in station data for subplot {station_code}."
                )

            lat = plot_row["LAT"].values[0]
            lon = plot_row["LON"].values[0]
            altitude = plot_row["ALTITUDE"].values[0]

            new_rows.append(
                {
                    "STATION_CODE": station_code,
                    "LAT": lat,
                    "LON": lon,
                    "ALTITUDE": altitude,
                    "PLOTSIZE": 1,
                }
            )

    # add new rows to station_data
    if new_rows:
        station_data = pd.concat(
            [station_data, pd.DataFrame(new_rows)], ignore_index=True
        )

    # sort by STATION_CODE
    station_data = station_data.sort_values(by="STATION_CODE").reset_index(drop=True)

    # add SITE_CODE column at the beginning
    station_data.insert(0, "SITE_CODE", site_code)

    # save to csv file
    station_data.to_csv(
        source_folder / "IT_MontagnadiTorricchio_v2_station.csv", index=False, sep=";"
    )

    # Read subplot and plot cover data
    new_rows = []

    for _, row in raw_flora_subplot.iterrows():
        year = row["Year"]

        if year in subplot_cover_years:
            plot_id = row["Plot"]
            subplot_id = row["Subplot"]
            station_code = f"{plot_id}_{subplot_id}"
            species = row["Bartolucci et al._2024"]
            species_alternative = row["Pignatti_1982"]
            cover_value = row["spp_presence_cover"]

            # get obs date form plot info
            plot_info_row = raw_plot_info[
                (raw_plot_info["Plot"] == plot_id) & (raw_plot_info["Year"] == year)
            ]

            # error if multiple or no entries found
            if len(plot_info_row) != 1:
                raise ValueError(
                    f"Expected one entry in plot info for plot {plot_id} and year {year}, but found {len(plot_info_row)}."
                )

            time = plot_info_row["Date"].values[0]

            new_rows.append(
                {
                    "SITE_CODE": site_code,
                    "STATION_CODE": station_code,
                    "VERT_OFFSET": "NA",
                    "VARIABLE": "Cover",
                    "TIME": time,
                    "LAYER": "F",  # herb layer for all subplot entries
                    "TAXA": species,
                    "TAXA_ALT": species_alternative,
                    "VALUE": cover_value,
                    "UNIT": "dimless",
                }
            )

    layer_mapping = {"A": "T", "B": "S", "C": "F"}

    for _, row in raw_flora_plot.iterrows():
        year = row["Year"]

        if year in plot_cover_years:
            station_code = row["Plot"]
            species = row["Bartolucci et al_2024"]
            species_alternative = row["Pignatti_1982"]
            cover_value = row["spp_presence_cover "]
            layer = layer_mapping.get(row["Layer "], "NA")

            # get obs date form plot info
            plot_info_row = raw_plot_info[
                (raw_plot_info["Plot"] == station_code)
                & (raw_plot_info["Year"] == year)
            ]

            # error if multiple or no entries found
            if len(plot_info_row) != 1:
                raise ValueError(
                    f"Expected one entry in plot info for plot {station_code} and year {year}, but found {len(plot_info_row)}."
                )

            time = plot_info_row["Date"].values[0]

            new_rows.append(
                {
                    "SITE_CODE": site_code,
                    "STATION_CODE": station_code,
                    "VERT_OFFSET": "NA",
                    "VARIABLE": "Cover",
                    "TIME": time,
                    "LAYER": layer,
                    "TAXA": species,
                    "TAXA_ALT": species_alternative,
                    "VALUE": cover_value,
                    "UNIT": "dimless",
                }
            )

    # write to csv file
    new_file_name = "IT_MontagnadiTorricchio_v2_cover.csv"
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
        "farngewächse": "(fern)",
        "bäume und sträucher": "(woody)",
    }

    first_observation_row = 13
    valid_entries = ["gräser", "leguminosen", "kräuter", "farngewächse"]
    forbidden_entries = ["bäume und sträucher"]
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
                logger.warning(f"Plot {station_code} has entries for woody species.")
                # Valid entries of PFT "Farngewächse" can occur after the invalid entries
                fern_index = valid_entry_indexes.get("farngewächse")
                forbidden_start_index = min(
                    forbidden_entry_indexes.values()
                )  # only one entry expected, but would work with multiple as well

                if fern_index is not None and fern_index > forbidden_start_index:
                    # we need to store the range from forbidden_start_index to fern_index - 1 for later use
                    forbidden_range = range(forbidden_start_index, fern_index)
                else:
                    forbidden_range = range(
                        forbidden_start_index, len(raw_data.columns)
                    )

                # Get sum of all entries from min(forbidden_entry_indexes.values()) to end for each row
                for year, row in raw_data.iterrows():
                    sum_forbidden = 0

                    for column in raw_data.columns[forbidden_range]:
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
                        # Read and set PFT for following species entries
                        pft = pft_map[column.lower()]
                    else:
                        # Read species entry
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
    moss_cover_threshold = 200.0
    # convert_raw_data_BEXIS(
    #     forbidden_cover_threshold=forbidden_cover_threshold,
    #     moss_cover_threshold=moss_cover_threshold,
    # )
    # convert_raw_data_KUL(forbidden_cover_threshold=forbidden_cover_threshold)
    # convert_raw_data_CVL(moss_cover_threshold=moss_cover_threshold)
    # convert_raw_data_MAM_C()
    convert_raw_data_MDT()
    # convert_raw_data_ASQ_C()
