"""
Module Name: check_if_grassland.py
Author: Thomas Banitz, Taimur Khan, Tuomas Rossi, Franziska Taubert, BioDT
Date: October, 2023
Description: Functions for checking if coordinates are grassland according to given TIF land cover map.


Land cover maps and classifications used: 

Eunis EEA habitat types (version 2012):
https://eunis.eea.europa.eu/habitats-code-browser.jsp?expand=290,86,1743,2421,2891,525#level_525
(Only for DEIMS Sites: Get all habitat types of a site, check if any of them is grassland.)

European Union's Copernicus Land Monitoring Service information (2020):
High Resolution Layer (HRL) Grassland 2018 raster, Europe. 
https://doi.org/10.2909/60639d5b-9164-4135-ae93-fb4132bb6d83
REST API
https://sdi.eea.europa.eu/catalogue/copernicus/eng/catalog.search#/metadata/60639d5b-9164-4135-ae93-fb4132bb6d83

Pflugmacher, Dirk; Rabe, Andreas; Peters, Mathias; Hostert, Patrick (2018):
Pan-European land cover map of 2015 based on Landsat and LUCAS data. 
PANGAEA, https://doi.org/10.1594/PANGAEA.896282

Preidl, Sebastian; Lange, Maximilian; Doktor, Daniel (2020):
Land cover classification map of Germany's agricultural area based on Sentinel-2A data from 2016.
PANGAEA, https://doi.org/10.1594/PANGAEA.910837

Schwieder, Marcel; Tetteh, Gideon Okpoti; Blickensdörfer, Lukas; Gocht, Alexander; Erasmi, Stefan (2024):
Agricultural land use (raster): National-scale crop type maps for Germany from combined time series of Sentinel-1, Sentinel-2 and Landsat data (2017 to 2021)
Zenodo, https://zenodo.org/records/10640528

German ATKIS digital landscape model 2015
Bundesamt für Kartographie und Geodäsie, 2015. 
Digitales Basis-Landschaftsmodell (AAA-Modellierung). 
GeoBasis-DE. Geodaten der deutschen Landesvermessung.
(derived via land use maps by Lange et al. (2022), https://data.mendeley.com/datasets/m9rrv26dvf/1)


# further candidate maps:
https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v100#citations
https://zenodo.org/records/7254221
https://zenodo.org/records/7254221

https://gdz.bkg.bund.de/index.php/default/digitale-geodaten/digitale-landschaftsmodelle/corine-land-cover-5-ha-stand-2018-clc5-2018.html
https://land.copernicus.eu/en/products/corine-land-cover

"""

import argparse
from copernicus import utils as ut_cop
import deims
import pandas as pd
from pathlib import Path
import requests
import utils as ut
import xml.etree.ElementTree as ET


def get_map_specs(map_key):
    """
    Set up map file names and specifications based on provided map key.

    Args:
        map_key (str): Identifier of the map to be used.

    Returns:
        dict: Dictionary containing the following keys:
            'file_stem': Stem of the file names.
            'map_ext': File extension for the map.
            'leg_ext': File extension for the legend (may extend the stem).
            'url_folder': URL to folder containing the files.
            'subfolder': Subfolder name for local files or files on opendap server.
    """
    if map_key == "GER_Preidl":
        map_specs = {
            "file_stem": "preidl-etal-RSE-2020_land-cover-classification-germany-2016",
            "map_ext": ".tif",
            "leg_ext": ".tif.aux.xml",
            "url_folder": "http://134.94.199.14/grasslands-pdt/landCoverMaps/",
            "subfolder": "landCoverMaps",
        }
    elif map_key == "EUR_Pflugmacher":
        map_specs = {
            "file_stem": "europe_landcover_2015_RSE-Full3",
            "map_ext": ".tif",
            "leg_ext": "_legend.xlsx",
            "url_folder": "https://hs.pangaea.de/Maps/EuropeLandcover/",  # http://134.94.199.14/grasslands-pdt/landCoverMaps/
            "subfolder": "landCoverMaps",
        }
    elif map_key.startswith("GER_Schwieder_"):
        map_year = map_key.split("_")[-1]  # get year from map key

        if map_year in ["2017", "2018", "2019", "2020", "2021"]:
            map_specs = {
                "file_stem": "CTM_GER_",
                "map_ext": map_year + "_rst_v202_COG.tif",
                "leg_ext": "LegendEN_rst_v202.xlsx",
                "url_folder": "https://zenodo.org/records/10640528/files/",
                "subfolder": "landCoverMaps",
            }
        else:
            print(f"Warning: Land cover map for key '{map_key}' not found!")

            return None
    elif map_key.startswith("GER_Lange_"):
        map_year = map_key.split("_")[-1]  # get year from map key

        if map_year in ["2017", "2018"]:
            map_specs = {
                "file_stem": "",  # "map_ext": ".tif",
                "leg_ext": "GER_Lange_Legend.xlsx",
                "url_folder": "https://data.mendeley.com/public-files/datasets/m9rrv26dvf/files/",
                "subfolder": "landCoverMaps",
            }
            map_specs["map_ext"] = (
                "98d7c7ab-0a8f-4c2f-a78f-6c1739ee9354/file_downloaded"
                if map_year == 2017
                else "d871429a-b2a6-4592-b3e5-4650462a9ac3/file_downloaded"
            )
        else:
            print(f"Warning: Land cover map for key '{map_key}' not found!")

            return None
    else:
        print(f"Warning: Land cover map for key '{map_key}' not found!")

        return None

    return map_specs


def get_map_and_legend(map_key, map_local=False):
    """
    Check if TIF file and categories file are avaible, read categories from file.

    Parameters:
        map_key (str): Identifier of the map to be used.
        map_local (bool): Look for map as local file (default is False).

    Returns:
        tuple: Tuple containing the following values:
            str: Full path or url of TIF file.
            dict: Mapping of category indices to category names.
    """

    # Get map specifications and map file name
    map_specs = get_map_specs(map_key)
    tif_file_name = map_specs["file_stem"] + map_specs["map_ext"]

    if map_local:
        # Get map from local file
        tif_file = ut.get_package_root() / map_specs["subfolder"] / tif_file_name

        if not tif_file.is_file():
            # Get tif map file from opendap server
            ut.download_file_opendap(
                tif_file_name, map_specs["subfolder"], tif_file.parent
            )

        if tif_file.is_file():
            print(f"Land cover map found. Using '{tif_file}'.")
        else:
            raise FileNotFoundError(f"Land cover map file '{tif_file}' not found!")
    else:
        # Get map directly from url, no download
        tif_file = map_specs["url_folder"] + tif_file_name

        if ut.check_url(tif_file):
            print(f"Land cover map found. Using '{tif_file}'.")
        else:
            raise FileNotFoundError(f"Land cover map file '{tif_file}' not found!")

    # Get categories
    # Local file option only, files are very small and can be downloaded if not exisiting
    leg_file_name = map_specs["file_stem"] + map_specs["leg_ext"]
    leg_file = ut.get_package_root() / map_specs["subfolder"] / leg_file_name

    if not leg_file.is_file():
        # Get categories file from opendap server
        ut.download_file_opendap(leg_file_name, map_specs["subfolder"], leg_file.parent)

    if leg_file.is_file():
        # Read categories from file
        print(f"Categories found. Using '{leg_file}'.")
        category_mapping = create_category_mapping(leg_file)
    else:
        raise FileNotFoundError(f"Categories file '{leg_file}' not found!")

    return tif_file, category_mapping


def create_category_mapping(leg_file):
    """
    Create a mapping of category indices to category names from legend file (XML or XLSX or ...).

    Parameters:
        leg_file (str): The path to the leg file containing category names (in specific format).

    Returns:
        dict: A mapping of category indices to category names.
    """
    category_mapping = {}

    if leg_file.suffix == ".xlsx":
        try:
            df = pd.read_excel(leg_file)

            # Assuming category elements are listed in the first two columns (index and name)
            category_mapping = {row[0]: row[1] for row in df.values}
            # # Alternative using the row names 'code' and 'class_names'
            # category_mapping = (df[["code", "class_name"]].set_index("code")["class_name"].to_dict())
        except Exception as e:
            print(f"Error reading XLSX file: {str(e)}")
    elif leg_file.suffix == ".xml":
        try:
            tree = ET.parse(leg_file)
            root = tree.getroot()

            # Assuming category elements are nested within CategoryNames within PAMRasterBand
            category_names = root.find(".//CategoryNames")

            if category_names is not None:
                for index, category in enumerate(category_names):
                    category_name = category.text
                    category_mapping[index] = category_name
        except Exception as e:
            print(f"Error reading XML file: {str(e)}")

    return category_mapping


def get_category_tif(tif_file, category_mapping, location):
    """
    Get the category based on the raster value at the specified location.

    Parameters:
        tif_file (Path): Path to the raster file.
        category_mapping (dict): Mapping of raster values to categories.
        location (dict): Dictionary with 'lat' and 'lon' keys for extracting raster value.

    Returns:
        str: Category corresponding to the raster value at the specified location,
             or "Unknown Category" if the value is not found in the mapping.
    """
    return category_mapping.get(
        ut.extract_raster_value(tif_file, location), "Unknown Category"
    )


def get_category_deims(location, map_key):
    """
    Get all categories based on habitat types (eunisHabitat) of DEIMS-Site.

    Parameters:
        location (dict): Dictionary with 'lat' and 'lon' keys for extracting categories.
        map_key (str): Identifier of the map to be used.

    Returns:
        str: Category as classified ('grassland' or 'non-grassland') if found.
    """
    if "deims_id" in location:
        location_record = deims.getSiteById(location["deims_id"])
        categories = []

        if (
            location_record["attributes"]["environmentalCharacteristics"][map_key]
            is not None
        ):
            for item in location_record["attributes"]["environmentalCharacteristics"][
                map_key
            ]:
                print(f"Habitat: {item['label']}")
                categories.append(item["label"])
        else:
            print(f"Habitat: None")
            categories.append("None")

        return categories


def get_category_hrl_grassland(location):
    """
    Get the category based on HRL Grassland raster at the specified location.

    Parameters:
        location (dict): Dictionary with 'lat' and 'lon' keys for extracting raster value.

    Returns:
        str: Category as classified if found (e.g. 'grassland', 'non-grassland').
    """
    # Define URL and request
    url = "https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_Grassland_2018/ImageServer"

    # # test for CORINE
    # # params unclear
    # url = "https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_WM/MapServer"

    geometry = {
        "x": location["lon"],
        "y": location["lat"],
        "spatialReference": {"wkid": 4326},
    }
    params = {
        "geometry": str(geometry),
        "geometryType": "esriGeometryPoint",
        "pixelSize": "0.1",
        "f": "json",
    }

    # Send request
    response = requests.get(f"{url}/identify", params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # Check if 'value' key exists in the response
        if "value" in data:
            value = data["value"]

            # Return classification based on value
            if value == "0":
                return "non-grassland"
            if value == "1":
                return "grassland"
            if value == "254":
                return "unclassifiable (no satellite image available, clouds, shadows or snow)"
            if value == "255":
                return "outside area"

            # Handle unknown values
            print(f"Warning: Unknown value for specified location: {value}.")

            return value
        else:
            print("Warning: No value for specified location.")
    else:
        print(f"Error: {response.status_code}")

    return None


def check_desired_categories(category, target_categories, location):
    """
    Check if the given category is one of the target categories.

    Parameters:
        category (str): Category to check.
        target_categories (list): List of target categories to compare against.
        location (dict): Dictionary with 'lat' and 'lon' keys.

    Returns:
        bool: True if the category is in the target categories, False otherwise.
    """
    # Check if extracted categories are in any of the target categories
    is_target_categories = category in target_categories

    # Print check results
    if is_target_categories:
        print(
            f"Confirmed: Lat. {location['lat']:.6f}, Lon. {location['lon']:.6f}",
            f"is classified as '{category}'.",
        )
    else:
        print(
            f"Not in target categories: Lat. {location['lat']:.6f}, Lon. {location['lon']:.6f}",
            f"is classified as '{category}'.",
        )

    return is_target_categories


def check_if_grassland(category, location, map_key=None):
    """
    Check if a category represents grassland based on the given category mapping.

    Parameters:
        category (str): Category to check.
        location (dict): Dictionary with 'lat' and 'lon' keys.
        map_key (str): Optional key to identify the DEIMS record habitat key (default is None).

    Returns:
        bool: True if the category represents grassland, False otherwise.
    """
    if map_key == "eunisHabitat":
        # Set accepted eunis EEA habitat types
        grass_labels = ["E", "E1", "E2", "E3", "E4", "E5"]
        # not included:
        # E6 : Inland salt steppes
        # E7 : Sparsely wooded grasslands
        habitat_label = category.split("(")[-1].strip(")")
        is_grassland = habitat_label == grass_labels[0]

        if not is_grassland:
            # Check if any element in the reference list is a prefix of part_in_brackets
            for label in grass_labels[1:]:
                if habitat_label.startswith(label):
                    is_grassland = True
                    break
    else:
        # Set accepted categories
        grass_categories = ["Grassland", "grassland", "grass", "Permanent grassland"]
        # not inlcuded:
        # "Legumes"

        is_grassland = check_desired_categories(category, grass_categories, location)

    return is_grassland


def check_locations_for_grassland(locations, map_key, file_name=None):
    """
    Check if given locations correspond to grassland areas based on the provided land cover map.

    Parameters:
        locations (list): List of location dictionaries containing coordinates ('lat', 'lon') or DEIMS.iD.
        map_key (str): Identifier of the map to be used.
        file_name (str or Path): Optional. Path to save the check results (default file will be created otherwise).

    Returns:
        None
    """
    print("Starting grassland check...")
    deims_keys = ["eunisHabitat"]
    tif_keys = [
        "EUR_Pflugmacher",
        "GER_Preidl",
        "GER_Schwieder_2017",
        "GER_Schwieder_2018",
        "GER_Schwieder_2019",
        "GER_Schwieder_2020",
        "GER_Schwieder_2021",
        "GER_Lange_2017",
        "GER_Lange_2018",
    ]
    hrl_keys = ["HRL_Grassland"]
    grassland_check = []

    if map_key in deims_keys:
        for location in locations:
            if "deims_id" in location:
                site_check = ut_cop.get_deims_coordinates(location["deims_id"])
                all_categories = get_category_deims(site_check, map_key)
                site_check["is_grass"] = False

                for index, category in enumerate(all_categories):
                    # Check only needed if grass not found yet
                    site_check["is_grass"] = site_check[
                        "is_grass"
                    ] or check_if_grassland(category, site_check, map_key)
                    site_check[("category" + "{:03d}".format(index + 1))] = category

                # Print check results
                if site_check["is_grass"]:
                    print(
                        f"Confirmed: Site with centroid Lat.",
                        f"{site_check['lat']:.4f}, Lon. {site_check['lon']:.4f}",
                        f"contains habitat classified as grassland.",
                    )
                else:
                    print(
                        f"Not in target categories: Site with centroid Lat.",
                        f"{site_check['lat']:.4f}, Lon. {site_check['lon']:.4f}",
                        f"contains no habitat classified as grassland.",
                    )
            else:
                raise ValueError(
                    f"DEIMS.iD needed with map key '{map_key}' for requesting site information!"
                )

            grassland_check.append(site_check)
    elif map_key in tif_keys:
        # Get TIF map and categories from legend file (local file or download from server)
        tif_file, category_mapping = get_map_and_legend(map_key, map_local=False)

        for location in locations:
            if ("lat" in location) and ("lon" in location):
                site_check = location
            elif "deims_id" in location:
                site_check = ut_cop.get_deims_coordinates(location["deims_id"])
            else:
                raise ValueError(
                    "No location defined. Please provide coordinates ('lat', 'lon') or DEIMS.iD!"
                )

            # Check for grassland if coordinates present
            if ("lat" in site_check) and ("lon" in site_check):
                site_check["category"] = get_category_tif(
                    tif_file, category_mapping, site_check
                )
                site_check["is_grass"] = check_if_grassland(
                    site_check["category"], site_check
                )

            grassland_check.append(site_check)
    elif map_key in hrl_keys:
        for location in locations:
            if ("lat" in location) and ("lon" in location):
                site_check = location
            elif "deims_id" in location:
                site_check = ut_cop.get_deims_coordinates(location["deims_id"])
            else:
                raise ValueError(
                    "No location defined. Please provide coordinates ('lat', 'lon') or DEIMS.iD!"
                )

            # Check for grassland if coordinates present
            if ("lat" in site_check) and ("lon" in site_check):
                site_check["category"] = get_category_hrl_grassland(site_check)
                site_check["is_grass"] = check_if_grassland(
                    site_check["category"], site_check
                )

            grassland_check.append(site_check)
    else:
        raise ValueError(
            f"Map key '{map_key}' not found. Please provide valid map key!"
        )

    # Save results to file
    if file_name is None:
        file_name = (
            ut.get_package_root()
            / "landCoverCheckResults"
            / ("grasslandCheck_" + map_key + ".txt")
        )
    column_names = ut.get_unique_keys(grassland_check)
    ut.list_to_file(grassland_check, column_names, file_name)

    # Final confirmation statement.
    print("Grassland check completed.")


def parse_locations(locations_str):
    """
    Parses the input string containing location information.

    Parameters:
        locations_str (str): String containing location information.

    Returns:
        list: List of dictionaries, each containing either coordinates ('lat', 'lon') or DEIMS IDs ('deims_id').
    """
    locations = []

    for item in locations_str.split(";"):
        if "lat" in item and "lon" in item:
            coordinates = item.split(",")
            locations.append(
                {"lat": float(coordinates[0]), "lon": float(coordinates[1])}
            )
        elif "deims_id" in item:
            locations.append({"deims_id": item.split(":")[1]})
        else:
            raise ValueError("Invalid location format.")

    return locations


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
        type=parse_locations,
        help="List of location dictionaries containing coordinates ('lat', 'lon') or DEIMS IDs ('deims_id')",
    )
    parser.add_argument(
        "--map_key",
        type=str,
        default="GER_Lange_2018",
        choices=[
            "eunisHabitat",
            "HRL_Grassland",
            "EUR_Pflugmacher",
            "GER_Preidl",
            "GER_Schwieder_2017",
            "GER_Schwieder_2018",
            "GER_Schwieder_2019",
            "GER_Schwieder_2020",
            "GER_Schwieder_2021",
            "GER_Lange_2017",
            "GER_Lange_2018",
        ],
        help="""Options: 
        'eunisHabitat', 
        'HRL_Grassland', 
        'EUR_Pflugmacher', 
        'GER_Preidl', 
        'GER_Schwieder_2017', 
        'GER_Schwieder_2018', 
        'GER_Schwieder_2019', 
        'GER_Schwieder_2020', 
        'GER_Schwieder_2021',
        'GER_Lange_2017',
        'GER_Lange_2018'.""",
    )
    parser.add_argument(
        "--file_name",
        type=str,
        default=None,
        help="File name to save grassland check results (default file will be created if not specified).",
    )
    args = parser.parse_args()

    # Example coordinates
    if args.locations is None:
        # Example to get coordinates from DEIMS.iDs from XLS file
        file_name = ut.get_package_root() / "grasslandSites" / "_elter_call_sites.xlsx"
        country_code = "DE"
        args.locations = ut.get_deims_ids_from_xls(
            file_name, header_row=1, country=country_code
        )
        args.file_name = file_name.parent / (
            file_name.stem
            + "_"
            + country_code
            + "__grasslandCheck_"
            + args.map_key
            + ".txt"
        )  # ".txt" or ".xlsx"

        # # Example coordinates for checking without DEIMS.iDs
        # args.locations = [
        #     {"lat": 51.390427, "lon": 11.876855},  # GER, GCEF grassland site
        #     {
        #         "lat": 51.3919,
        #         "lon": 11.8787,
        #     },  # GER, GCEF grassland site, centroid, non-grassland in HRL!
        #     {"lat": 51.3521825, "lon": 12.4289394},  # GER, UFZ Leipzig
        #     {"lat": 51.4429008, "lon": 12.3409231},  # GER, Schladitzer See, lake
        #     {"lat": 51.3130786, "lon": 12.3551142},  # GER, Auwald, forest within city
        #     {"lat": 51.7123725, "lon": 12.5833917},  # GER, forest outside of city
        #     {"lat": 46.8710811, "lon": 11.0244728},  # AT, should be grassland
        #     {"lat": 64.2304403, "lon": 27.6856269},  # FIN, near LUMI site
        #     {"lat": 64.2318989, "lon": 27.6952722},  # FIN, LUMI site
        #     {"lat": 49.8366436, "lon": 18.1540575},  # CZ, near IT4I Ostrava
        #     {"lat": 43.173, "lon": 8.467},  # Mediterranean Sea
        #     {"lat": 30, "lon": 1},  # out of Europe
        # ]

    # Default file name will be used as no file name is passed here
    check_locations_for_grassland(args.locations, args.map_key, args.file_name)


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
