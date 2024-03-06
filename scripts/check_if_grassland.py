"""
Module Name: check_if_grassland.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: October, 2023
Description: Functions for checking if coordinates are grassland according to given TIF land cover map.


Land cover maps and classifications used: 

Preidl, Sebastian; Lange, Maximilian; Doktor, Daniel (2020):
Land cover classification map of Germany's agricultural area based on Sentinel-2A data from 2016.
PANGAEA, https://doi.org/10.1594/PANGAEA.910837

Pflugmacher, Dirk; Rabe, Andreas; Peters, Mathias; Hostert, Patrick (2018):
Pan-European land cover map of 2015 based on Landsat and LUCAS data. 
PANGAEA, https://doi.org/10.1594/PANGAEA.896282

Eunis EEA habitat types (version 2012):
https://eunis.eea.europa.eu/habitats-code-browser.jsp?expand=290,86,1743,2421,2891,525#level_525
(Only for DEIMS Sites: Get all habitat types of a site, check if any of them is grassland.)

European Union's Copernicus Land Monitoring Service information (2020):
High Resolution Layer (HRL) Grassland 2018 raster, Europe. 
https://doi.org/10.2909/60639d5b-9164-4135-ae93-fb4132bb6d83
REST API
https://sdi.eea.europa.eu/catalogue/copernicus/eng/catalog.search#/metadata/60639d5b-9164-4135-ae93-fb4132bb6d83

# further candidate maps:
https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v100#citations
https://zenodo.org/records/7254221
https://zenodo.org/records/7254221

https://gdz.bkg.bund.de/index.php/default/digitale-geodaten/digitale-landschaftsmodelle/corine-land-cover-5-ha-stand-2018-clc5-2018.html

"""

from copernicus import utils as ut_cop
import deims
import pandas as pd
from pathlib import Path
import requests
import utils as ut
import xml.etree.ElementTree as ET


def get_map_specs():
    """
    Set up file names and legend file extensions for different maps.

    Returns:
        dict of dict: Each key maps to a dictionary containing "tif_file" and "leg_ext" keys for file information.
    """
    # Different maps and respective categories files
    # Default folder is 'landCoverMaps' subfolder of the project root.
    # Otherwise use full path to TIF file here!
    map_specs = {
        "GER_Preidl": {
            "tif_file": "preidl-etal-RSE-2020_land-cover-classification-germany-2016.tif",
            "leg_ext": ".tif.aux.xml",
        },
        "EUR_Pflugmacher": {
            "tif_file": "europe_landcover_2015_RSE-Full3.tif",
            "leg_ext": "_legend.xlsx",
        },
    }

    return map_specs


def get_map_and_legend(map_key):
    """
    Check if TIF file and categories file are avaible, read categories from file.

    Parameters:
        map_key (str): Identifier of the map to be used.

    Returns:
        tuple: A tuple containing the following values:
            - str: Full path of TIF file.
            - dict: Mapping of category indices to category names.
    """
    map_specs = get_map_specs()
    tif_file = map_specs[map_key]["tif_file"]

    # Add default path if TIF file not provided with full path
    if not Path(tif_file).is_absolute():
        tif_file = ut.get_package_root() / "landCoverMaps" / tif_file

    # Get default categories file, using extension defined in 'map_specs'
    if tif_file.is_file():
        leg_file = tif_file.parent / (tif_file.stem + map_specs[map_key]["leg_ext"])

        if leg_file.is_file():
            # Get the categories
            category_mapping = create_category_mapping(leg_file)
            print(f"Map and categories found. Using '{tif_file}'.")
        else:
            raise FileNotFoundError(
                f"Land cover categories file '{leg_file}' not found!"
            )
    else:
        raise FileNotFoundError(f"Land cover map file '{tif_file}' not found!")

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
    - tif_file (Path): Path to the raster file.
    - category_mapping (dict): Mapping of raster values to categories.
    - location (dict): Dictionary with 'lat' and 'lon' keys for extracting raster value.

    Returns:
    - str: Category corresponding to the raster value at the specified location,
           or "Unknown Category" if the value is not found in the mapping.
    """
    return category_mapping.get(
        ut.extract_raster_value(tif_file, location), "Unknown Category"
    )


def get_category_deims(location, map_key):
    """
    Get all categories based on habitat types (eunisHabitat) of DEIMS-Site.

    Parameters:
    - location (dict): Dictionary with 'lat' and 'lon' keys for extracting categories.
    - map_key (str): 

    Returns:
    - str: Category as classified ('grassland' or 'non-grassland') if found.
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
                print(f"Habitat: {item["label"]}")
                categories.append(item["label"])
        else:
            print(f"Habitat: None")
            categories.append("None")

        return categories
    
def get_category_hrl_grassland(location):
    """
    Get the category based on HRL Grassland raster at the specified location.

    Parameters:
    - location (dict): Dictionary with 'lat' and 'lon' keys for extracting raster value.

    Returns:
    - str: Category as classified if found (e.g. 'grassland', 'non-grassland'). 
    """    
    # Define URL and request
    url = "https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_Grassland_2018/ImageServer"
    geometry = {
        "x": location["lon"],
        "y": location["lat"],
        "spatialReference": {"wkid": 4326},
    }
    params = {
        "geometry": str(geometry),
        "geometryType": "esriGeometryPoint",
        "pixelSize": "0.1",
        "f": "json"
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
    - category (str): Category to check.
    - target_categories (list): List of target categories to compare against.
    - location (dict): Dictionary with 'lat' and 'lon' keys.

    Returns:
    - bool: True if the category is in the target categories, False otherwise.
    """
    # Check if extracted categories are in any of the target categories
    is_target_categories = category in target_categories

    # Print check results
    if is_target_categories:
        print(
            f"Confirmed: Lat. {location['lat']:.4f}, Lon. {location['lon']:.4f}",
            f"is classified as '{category}'."
        )
    else:
        print(
            f"Not in target categories: Lat. {location['lat']:.4f}, Lon. {location['lon']:.4f}",
            f"is classified as '{category}'."
        )

    return is_target_categories


def check_if_grassland(category, location, map_key=None):
    """
    Check if a category represents grassland based on the given category mapping.

    Parameters:
    - category (str): Category to check.
    - location (dict): Dictionary with 'lat' and 'lon' keys.
    - map_key (str): Optional key to identify the DEIMS record habitat key (default is None).

    Returns:
    - bool: True if the category represents grassland, False otherwise.
    """
    if map_key:
        if map_key == "eunisHabitat":
            grass_labels = ["E", "E1", "E2", "E3", "E4", "E5"]
            # not included:
            # E6 : Inland salt steppes  
            # E7 : Sparsely wooded grasslands 
            habitat_label = category.split("(")[-1].strip(")")
            is_grassland = (habitat_label == grass_labels[0])

            if not is_grassland:
                # Check if any element in the reference list is a prefix of part_in_brackets
                for label in grass_labels[1:]:
                    if habitat_label.startswith(label):
                        is_grassland = True
                        break
    else:
        # Set accepted categories, includes eunis EEA habitat types
        grass_categories = [
            "Grassland",
            "grassland",
            "grass",            
        ]
        # not inlcuded:
        # "Legumes"

        is_grassland = check_desired_categories(category, grass_categories, location)

    return is_grassland


def check_locations_for_grassland(locations, map_key, file_name=None):
    """
    Check if given locations correspond to grassland areas based on the provided land cover map.

    Parameters:
    - locations (list): List of location dictionaries containing coordinates ('lat', 'lon') or DEIMS.iD.
    - map_key (str): Key to identify the land cover map and associated legend files.
    - file_name (str or Path): Optional. Path to save the check results (default file will be created otherwise).

    Returns:
    - None
    """
    print("Starting grassland check...")
    deims_keys = ["eunisHabitat"]
    tif_keys = ["EUR_Pflugmacher", "GER_Preidl"]
    hrl_keys =["HRL_Grassland"]
    grassland_check = []

    if map_key in deims_keys:
        for location in locations:
            if "deims_id" in location:
                site_check = ut_cop.get_deims_coordinates(location["deims_id"])
                all_categories = get_category_deims(site_check, map_key)
                site_check["is_grass"] = False

                for index, category in enumerate(all_categories):
                    # Check only needed if grass not found yet
                    site_check["is_grass"] = site_check["is_grass"] or check_if_grassland(category, site_check, map_key)
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
        # TIF and legend file need to be in the project root's subfolder "landCoverMaps"
        tif_file, category_mapping = get_map_and_legend(map_key)

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
            / "grasslandSites"
            / ("grasslandCheck_" + map_key + ".txt")
        )
    column_names = ut.get_unique_keys(grassland_check)
    ut.list_to_file(grassland_check, column_names, file_name)

    # Final confirmation statement.
    print("Grassland check completed.")


# ### EXAMPLE USE
map_key = "EUR_Pflugmacher"  # options: "eunisHabitat", "EUR_Pflugmacher", "GER_Preidl", "HRL_Grassland", can be extended

# Example to get coordinates from DEIMS.iDs from XLS file
file_name = ut.get_package_root() / "grasslandSites" / "_elter_call_sites.xlsx"
locations = ut.get_deims_ids_from_xls(file_name, header_row=1)
file_name = file_name.parent / (file_name.stem + "__grasslandCheck_" + map_key + ".txt")  # ".txt" or ".xlsx"
check_locations_for_grassland(locations, map_key, file_name)

# Example coordinates for checking without DEIMS.iDs
locations = [
    {"lat": 51.390427, "lon": 11.876855},  # GER, GCEF grassland site
    {"lat": 51.3919, "lon": 11.8787},  # GER, GCEF grassland site, centroid, non-grassland in HRL!
    {"lat": 51.3521825, "lon": 12.4289394},  # GER, UFZ Leipzig
    {"lat": 51.4429008, "lon": 12.3409231},  # GER, Schladitzer See, lake
    {"lat": 51.3130786, "lon": 12.3551142},  # GER, Auwald, forest within city
    {"lat": 51.7123725, "lon": 12.5833917},  # GER, forest outside of city
    {"lat": 46.8710811, "lon": 11.0244728},  # AT, should be grassland
    {"lat": 64.2304403, "lon": 27.6856269},  # FIN, near LUMI site
    {"lat": 64.2318989, "lon": 27.6952722},  # FIN, LUMI site
    {"lat": 49.8366436, "lon": 18.1540575},  # CZ, near IT4I Ostrava
    {"lat": 43.173, "lon": 8.467},  # Mediterranean Sea
    {"lat": 30, "lon": 1},  # out of Europe
]

# Default file name will be used as no file name is passed here
check_locations_for_grassland(locations, map_key)
