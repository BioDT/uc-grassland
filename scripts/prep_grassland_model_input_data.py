"""
Module Name: prep_grassland_model_input_data.py
Description: Download all input data and prepare as needed for grassland model simulations.

Developed in the BioDT project by Thomas Banitz (UFZ) with contributions by Franziska Taubert (UFZ)
and Tuomas Rossi (CSC).

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
"""

import argparse
import shutil
import warnings
from datetime import datetime
from pathlib import Path

import check_if_grassland
import prep_management_data
import prep_soil_data
import prep_weather_data
import utils as ut
from prep_observation_data import OBSERVATION_DATA_SPECS_PER_SITE


def add_coordinate_infos(coordinates):
    """
    Add information to coordinates dictionary.

    Parameters:
        coordinates (dict): Coordinates dictionary with 'lat' and 'lon'.

    Returns:
        dict: Coordinates dictionary with additional information (if 'lat' and 'lon' are present, otherwise None):
            'formatted_lat' (str): Formatted latitude string.
            'formatted_lon' (str): Formatted longitude string.
            'file_start' (str): Start of file name.
            'location_head_folder' (Path): Location head folder.
    """

    if "lat" in coordinates and "lon" in coordinates:
        # Prepare location coordinates for file names and folder
        formatted_lat = f"lat{coordinates['lat']:.6f}"
        formatted_lon = f"lon{coordinates['lon']:.6f}"
        file_start = f"{formatted_lat}_{formatted_lon}"
        coordinates.update(
            {
                "formatted_lat": formatted_lat,
                "formatted_lon": formatted_lon,
                "file_start": file_start,
                "location_head_folder": Path(
                    ut.get_package_root() / "grasslandModelInputFiles" / file_start
                ),
            }
        )

        return coordinates
    else:
        warnings.warn(
            "Coordinates not correctly defined. Please provide as dictionary "
            "({'lat': float, 'lon': float})! "
            f"Cannot use these coordinates: {coordinates}."
        )

        return None


def get_input_data(
    coordinates_list,
    years,
    *,
    skip_grass_check=False,
    skip_weather=False,
    download_weather_area=True,
    skip_soil=False,
    skip_management=False,
):
    """
    Process data to be used as grassland site information and model input:
        checks if the location is grassland according to different land cover sources,
        downloads and prepares weather data,
        downloads and prepares soil data,
        downloads and prepares management data.

    Parameters:
        coordinates (list of dict): List of dictionaries with 'lat' and 'lon' keys.
        years (list of int): Years list.
        skip_grass_check (bool): Skip grassland checks (default is False).
        skip_weather (bool): Skip weather data preparation (default is False).
        skip_soil (bool): Skip soil data preparation (default is False).
        skip_management (bool): Skip management data preparation (default is False).
    """
    # Init dialogue
    location_count = len(coordinates_list)
    print(
        f"Preparing input data for coordinates list with {location_count} locations ..."
    )

    # Check if grassland according to all available land cover maps
    if skip_grass_check:
        print("Grassland checks skipped.")
    else:
        default_land_cover_map_keys = [
            "EUR_hrl_grassland",
            "EUR_Pflugmacher",
            "GER_Preidl",
            "GER_Schwieder_2017",
            "GER_Schwieder_2018",
            "GER_Schwieder_2019",
            "GER_Schwieder_2020",
            "GER_Schwieder_2021",
            "GER_Lange_2017",
            # "GER_Lange_2018", only 1 GER_Lange map needed as both use German ATKIS digital landscape model 2015
        ]

        for coordinates in coordinates_list:
            coordinates = add_coordinate_infos(coordinates)

            if coordinates is not None:
                print(
                    f"Preparing grassland check data for latitude: {coordinates['lat']},",
                    f"longitude: {coordinates['lon']} ...",
                )
                grassland_checks = []
                land_cover_map_keys = default_land_cover_map_keys.copy()

                # "EUR_eunis_habitat" only works for DEIMS.iDs
                if coordinates.get("deims_id"):
                    land_cover_map_keys.append("EUR_eunis_habitat")

                for map_key in land_cover_map_keys:
                    check_this_map = check_if_grassland.check_locations_for_grassland(
                        [coordinates], map_key
                    )
                    grassland_checks.append(check_this_map[0])

                file_name = (
                    coordinates["location_head_folder"]
                    / "landCover"
                    / f"{coordinates['file_start']}__grasslandCheck__allMaps.txt"
                )
                grassland_checks.sort(key=lambda x: x["map_year"])
                check_if_grassland.check_results_to_file(
                    grassland_checks, file_name=file_name
                )

    # Run weather script
    if skip_weather:
        print("Weather data preparation skipped.")
    else:
        # Use preliminary target folder for all weather data, later move to each single location folder
        target_folder = (
            ut.get_package_root() / "grasslandModelInputFiles" / "weatherDataPrepared"
        )
        prep_weather_data.prep_weather_data(
            coordinates_list,
            years,
            download_whole_area=download_weather_area,
            target_folder=target_folder,
        )

        for coordinates in coordinates_list:
            coordinates = add_coordinate_infos(coordinates)

            # Check target folder for weather files containing these coordinates
            weather_files = list(
                target_folder.glob(
                    f"{coordinates['formatted_lat']}_{coordinates['formatted_lon']}*weather.txt"
                )
            )

            if len(weather_files) > 1:
                warnings.warn(
                    f"More than one weather file found for latitude {coordinates['formatted_lat']}, "
                    f"longitude {coordinates['formatted_lon']}\nin target folder '{target_folder}'.\n"
                    "Moving all files to location folder."
                )

            # Move weather files to location folder
            for weather_file in weather_files:
                final_folder = coordinates["location_head_folder"] / "weather"
                final_folder.mkdir(parents=True, exist_ok=True)
                final_file = final_folder / weather_file.name
                shutil.move(weather_file, final_file)

    # Run soil script
    if skip_soil:
        print("Soil data preparation skipped.")
    else:
        for coordinates in coordinates_list:
            coordinates = add_coordinate_infos(coordinates)
            file_name = (
                coordinates["location_head_folder"]
                / "soil"
                / f"{coordinates['file_start']}__2020__soil.txt"
            )
            prep_soil_data.prep_soil_data(coordinates, file_name=file_name)

    # Run management script
    if skip_management:
        print("Management data preparation skipped.")
    else:
        land_use_map_keys = ["GER_Lange", "GER_Schwieder"]

        for coordinates in coordinates_list:
            coordinates = add_coordinate_infos(coordinates)

            for map_key in land_use_map_keys:
                file_name = (
                    coordinates["location_head_folder"]
                    / "management"
                    / f"{coordinates['file_start']}__{years[0]}-01-01_{years[-1]}-12-31__management__{map_key}.txt"
                )
                prep_management_data.prep_management_data(
                    coordinates, years, map_key, file_name=file_name
                )

    # Finish dialogues
    print(f"Input data preparation finished (for {location_count} locations).")


def prep_grassland_model_input_data(
    coordinates_list,
    first_year,
    last_year,
    *,
    deims_id=None,
    skip_grass_check=False,
    skip_weather=False,
    download_weather_area=False,
    skip_soil=False,
    skip_management=False,
):
    """
    Prepare all necessary data to be used as grassland model input.

    Parameters:
        coordinates (dict): Coordinates dictionary with 'lat' and 'lon', or 'None' using DEIMS.iD.
        first_year (int): First year of desired time period.
        last_year (int): Last year of desired time period.
        deims_id (str): DEIMS.iD (default is None).
    """
    if first_year and last_year:
        first_year = int(first_year)
        last_year = int(last_year)

        if last_year < first_year:
            warnings.warn(
                f"First year {first_year} is after last year {last_year}! Last year set to {first_year}."
            )
            last_year = first_year

        years = list(range(first_year, last_year + 1))
    else:
        years = None

    if years and coordinates_list:
        get_input_data(
            coordinates_list,
            years,
            skip_grass_check=skip_grass_check,
            skip_weather=skip_weather,
            download_weather_area=download_weather_area,
            skip_soil=skip_soil,
            skip_management=skip_management,
        )
    elif years and deims_id:
        location = ut.get_deims_coordinates(deims_id)

        if location["found"]:
            get_input_data(
                [location],
                years,
                skip_grass_check=skip_grass_check,
                skip_weather=skip_weather,
                download_weather_area=False,
                skip_soil=skip_soil,
                skip_management=skip_management,
            )
        else:
            raise ValueError(f"Coordinates for DEIMS.id '{deims_id}' not found!")
    else:
        # Example locations list
        # locations = ut.parse_locations(
        #     "51.390427,11.876855;51.392331,11.883838;102ae489-04e3-481d-97df-45905837dc1a"
        # )

        # # # Example to get location coordinates from CSV file (for single plots/stations)
        # # file_name = (
        # #     ut.get_package_root()
        # #     / "grasslandSites"
        # #     / "DE_RhineMainObservatory_station.csv"
        # # )
        # # # file_name = (
        # # #     ut.get_package_root() / "grasslandSites" / "AT_Hochschwab_station.csv"
        # # # )
        # # years = list(range(1992, 2024))
        # # locations = ut.get_plot_locations_from_csv(file_name)

        # locations = ut.parse_locations("48.960629, 13.395191")

        # # # example: GCEF small scale difference
        # coordinates_list = [
        #     {"lat": 51.390427, "lon": 11.876855},  # GER, GCEF grassland site
        #     {"lat": 51.392331, "lon": 11.883838},  # GER, GCEF grassland site
        #     {
        #         "lat": 51.3919,
        #         "lon": 11.8787,
        #     },  # GER, GCEF grassland site, centroid, non-grassland in HRL
        # ]
        # years = list(range(1998, 1999))

        # # Example to get location coordinates from CSV file (for single plots/stations) - quick run, to be generalized below
        source_folder = Path(
            "c:/Users/banitz/Nextcloud/Cloud/BioDT_ExchangeFranziThomas/BYODE/eLTER_DataCall/data_processed/"
        )
        # deims_id = "11696de6-0ab9-4c94-a06b-7ce40f56c964"
        # station_file = source_folder / deims_id / "IT_Matschertal_station.csv"
        # deims_id = "270a41c4-33a8-4da6-9258-2ab10916f262"
        # station_file = source_folder / deims_id / "DE_AgroScapeQuillow_station.csv"
        # coordinates_list = ut.get_plot_locations_from_csv(station_file)
        # first_year = 1999
        # last_year = 2024
        # years = list(range(first_year, last_year + 1))
        # download_weather_area = True
        skip_grass_check = True
        # skip_weather = True
        skip_soil = True
        skip_management = True

        # get_input_data(
        #     coordinates_list,
        #     years,
        #     skip_grass_check=skip_grass_check,
        #     skip_weather=skip_weather,
        #     download_weather_area=download_weather_area,
        #     skip_soil=skip_soil,
        #     skip_management=skip_management,
        # )

        # # Example to get multiple coordinates from DEIMS.iDs from XLS file, filter only Germany
        # sites_file_name = (
        #     ut.get_package_root() / "grasslandSites" / "_elter_call_sites.xlsx"
        # )
        # site_ids = ut.get_deims_ids_from_xls(
        #     sites_file_name,
        #     header_row=1,
        #     country="ALL",  # "DE" "AT"
        # )
        site_ids = [
            # "11696de6-0ab9-4c94-a06b-7ce40f56c964",  # IT25 - Val Mazia/Matschertal
            # "270a41c4-33a8-4da6-9258-2ab10916f262",  # AgroScapeLab Quillow (ZALF)
            # "31e67a47-5f15-40ad-9a72-f6f0ee4ecff6",  # LTSER Zone Atelier Armorique
            # "324f92a3-5940-4790-9738-5aa21992511c",  # Stubai
            # # "3de1057c-a364-44f2-8a2a-350d21b58ea0",  # Obergurgl
            # # "4ac03ec3-39d9-4ca1-a925-b6c1ae80c90d",  # Hochschwab (AT-HSW) GLORIA
            "61c188bc-8915-4488-8d92-6d38483406c0",  # Randu meadows
            "66431807-ebf1-477f-aa52-3716542f3378",  # LTSER Engure
            "6ae2f712-9924-4d9c-b7e1-3ddffb30b8f1",  # GLORIA Master Site Schrankogel (AT-SCH), Stubaier Alpen
            "6b62feb2-61bf-47e1-b97f-0e909c408db8",  # Montagna di Torricchio
            # "829a2bcc-79d6-462f-ae2c-13653124359d",  # Ordesa y Monte Perdido / Huesca ES
            "9f9ba137-342d-4813-ae58-a60911c3abc1",  # Rhine-Main-Observatory
            "a03ef869-aa6f-49cf-8e86-f791ee482ca9",  # Torgnon grassland Tellinod (IT19 Aosta Valley)
            "b356da08-15ac-42ad-ba71-aadb22845621",  # Nørholm Hede
            "c0738b00-854c-418f-8d4f-69b03486e9fd",  # Appennino centrale: Gran Sasso d'Italia
            "c85fc568-df0c-4cbc-bd1e-02606a36c2bb",  # Appennino centro-meridionale: Majella-Matese
            "e13f1146-b97a-4bc5-9bc5-65322379a567",  # Jalovecka dolina
        ]

        # Get the last full year from now
        last_year = datetime.now().year - 1

        for deims_id in site_ids:
            station_file = (
                source_folder
                / deims_id
                / OBSERVATION_DATA_SPECS_PER_SITE[deims_id]["station_file"]
            )
            coordinates_list = ut.get_plot_locations_from_csv(station_file)

            # Specify site-specific time range
            first_year = max(
                1950, OBSERVATION_DATA_SPECS_PER_SITE[deims_id]["start_year"] - 10
            )
            years = list(range(first_year, last_year + 1))

            get_input_data(
                coordinates_list,
                years,
                skip_grass_check=skip_grass_check,
                skip_weather=skip_weather,
                download_weather_area=download_weather_area,
                skip_soil=skip_soil,
                skip_management=skip_management,
            )


def main():
    """
    Run script with default arguments for calling the script.
    """
    parser = argparse.ArgumentParser(
        description="Set default arguments for calling the script."
    )

    # Define command-line arguments
    parser.add_argument(
        "--coordinates_list",
        type=list,
        help="List of coordinates dictionaries with 'lat' and 'lon' keys.",
    )
    parser.add_argument(
        "--first_year",
        type=int,
        help="First year for which to generate input data.",
    )
    parser.add_argument(
        "--last_year",
        type=int,
        help="Last year for which to generate input data.",
    )
    parser.add_argument("--deims_id", help="DEIMS.iD")
    parser.add_argument(
        "--skip_grass_check",
        action="store_true",
        help="Skip grassland checks (default is False).",
    )
    parser.add_argument(
        "--skip_weather",
        action="store_true",
        help="Skip weather data preparation (default is False).",
    )
    parser.add_argument(
        "--download_weather_single_points",
        action="store_false",
        dest="download_weather_area",
        help="Download single points, not whole area covering all coordinates in the list (default is False).",
    )
    parser.add_argument(
        "--skip_soil",
        action="store_true",
        help="Skip soil data preparation (default is False).",
    )
    parser.add_argument(
        "--skip_management",
        action="store_true",
        help="Skip management data preparation (default is False).",
    )
    args = parser.parse_args()
    prep_grassland_model_input_data(
        coordinates_list=args.coordinates_list,
        first_year=args.first_year,
        last_year=args.last_year,
        deims_id=args.deims_id,
        skip_grass_check=args.skip_grass_check,
        skip_weather=args.skip_weather,
        download_weather_area=args.download_weather_area,
        skip_soil=args.skip_soil,
        skip_management=args.skip_management,
    )


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
