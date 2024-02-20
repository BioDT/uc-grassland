"""
Module Name: check_if_grassland.py
Author: Thomas Banitz, Franziska Taubert, BioDT
Date: October, 2023
Description: Functions for checking if coordinates are grassland according to given TIF land cover map.


Land cover maps used: 

Preidl, Sebastian; Lange, Maximilian; Doktor, Daniel (2020):
Land cover classification map of Germany's agricultural area based on Sentinel-2A data from 2016.
PANGAEA, https://doi.org/10.1594/PANGAEA.910837

Pflugmacher, Dirk; Rabe, Andreas; Peters, Mathias; Hostert, Patrick (2018):
Pan-European land cover map of 2015 based on Landsat and LUCAS data. 
PANGAEA, https://doi.org/10.1594/PANGAEA.896282

# still to be included (multiple TIF files or API?):
European Union's Copernicus Land Monitoring Service information (2020):
High Resolution Layer (HRL) Grassland 2018 raster, Europe.
https://doi.org/10.2909/60639d5b-9164-4135-ae93-fb4132bb6d83

# further candidate maps:
https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v100#citations
https://zenodo.org/records/7254221
https://zenodo.org/records/7254221

https://gdz.bkg.bund.de/index.php/default/digitale-geodaten/digitale-landschaftsmodelle/corine-land-cover-5-ha-stand-2018-clc5-2018.html

"""

from copernicus import utils as ut_cop
import numpy as np

# import os
import pandas as pd
from pathlib import Path
import pyproj
import rasterio
import utils as ut
import xml.etree.ElementTree as ET


def get_map_specs():
    """
    Set up file names and legend file extensions for different maps.

    Returns:
        dict of dict: Each key maps to a dictionary containing "tif_file" and "leg_ext" keys for file information.
    """
    # Different maps and respective categories files
    # Default folder is 'land_cover_map_tif' subfolder of the project root.
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

    Args:
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


def reproject_coordinates(lat, lon, target_crs):
    """
    Reproject latitude and longitude coordinates to a target CRS.

    Args:
        lat (float): Latitude.
        lon (float): Longitude.
        target_crs (str): Target Coordinate Reference System in WKT format.

    Returns:
        tuple (float): Reprojected coordinates (easting, northing).
    """
    # Define the source CRS (EPSG:4326 - WGS 84, commonly used for lat/lon)
    src_crs = pyproj.CRS("EPSG:4326")

    # Create a transformer to convert from the source CRS to the target CRS
    # (always_xy: use lon/lat for source CRS and east/north for target CRS)
    transformer = pyproj.Transformer.from_crs(src_crs, target_crs, always_xy=True)

    # Reproject the coordinates (order is lon, lat!)
    east, north = transformer.transform(lon, lat)

    return east, north


def create_category_mapping(leg_file):
    """
    Create a mapping of category indices to category names from legend file (XML or XLSX or ...).

    Args:
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


def extract_raster_values(tif_file, coordinates):
    """
    Extract values from raster file at specified coordinates.

    Args:
        tif_file (str): Path to TIF file.
        category_mapping (dict): Mapping of category indices to category names.
        coordinates (list of dict): List of dictionaries with "lat" and "lon" keys.

    Returns:
        list: A list of extracted values.
    """
    extracted_values = []

    with rasterio.open(tif_file) as src:
        # Get the target CRS (as str in WKT format) from the TIF file
        target_crs = src.crs.to_wkt()
        # (GER_Preidl, EUR_Pflugmacher use Lambert Azimuthal Equal Area in meters)

        for coord in coordinates:
            # Reproject the coordinates to the target CRS
            east, north = reproject_coordinates(coord["lat"], coord["lon"], target_crs)

            # Extract the value at the specified coordinates
            value = next(src.sample([(east, north)]))
            extracted_values.append(value[0])

    return extracted_values


def get_categories(tif_file, category_mapping, coordinates):

    extracted_values = extract_raster_values(tif_file, coordinates)

    # Get categories of extracted values
    extracted_categories = np.array(
        [category_mapping.get(value, "Unknown Category") for value in extracted_values]
    )

    return extracted_categories


# def check_desired_categories(
#     extracted_values, category_mapping, coordinates, target_categories
# ):
def check_desired_categories(extracted_categories, target_categories, coordinates):
    """
    Check if the category of extracted values at specified coordinates matches target categories.

    Args:
        extracted_values (list or numpy array): List of extracted values as integers.
        category_mapping (dict): Mapping of category indices to category names.
        coordinates (list of dict): List of dictionaries with "lat" and "lon" keys.
        target_categories (list of str): List of target categories to check for.

    Returns:
        numpy array of bool: Array indicating whether any of the target categories are matched.
    """
    # # Get categories of extracted values
    # extracted_categories = np.array(
    #     [category_mapping.get(value, "Unknown Category") for value in extracted_values]
    # )

    # Check if extracted categories are in any of the target categories
    is_target_categories = np.isin(extracted_categories, target_categories)

    # Print check results
    for index, match in enumerate(is_target_categories):
        coord = coordinates[index]
        category = extracted_categories[index]

        if match:
            print(
                f"Confirmed: Lat. {coord['lat']}, Lon. {coord['lon']} is classified as '{category}'."
            )
        else:
            print(
                f"Warning: Lat. {coord['lat']}, Lon. {coord['lon']} is classified as '{category}', not in the target categories!"
            )

    return is_target_categories


# def check_if_grassland(tif_file, category_mapping, coordinates):
def check_if_grassland(extracted_values, category_mapping):
    """
    Extract categories at specified coordinates and check if grassland according to mapping.

    Args:
        tif_file (str): Path to TIF file.
        category_mapping (dict): Mapping of category indices to category names.
        coordinates (list of dict): List of dictionaries with "lat" and "lon" keys.

    Returns:
        numpy array of bool: Array indicating whether any of the grassland categories are matched.
    """
    # # Get values at coordinates
    # extracted_values = extract_raster_values(tif_file, coordinates)

    # Set accepted categories and check
    target_categories = [
        "Grassland",
        "grassland",
        "grass",
    ]  # should "Legumes" also be in here? probably not
    # is_target_categories = check_desired_categories(
    #     extracted_values, category_mapping, coordinates, target_categories
    # )

    is_target_categories = check_desired_categories(
        extracted_categories, target_categories, coordinates
    )

    return is_target_categories


def check_coordinates(locations, map_key):
    print("Starting grassland check...")
    tif_file, category_mapping = get_map_and_legend(map_key)

    for location in locations:
        if ("lat" in location) and ("lon" in location):
            location["category"] = get_categories(tif_file, category_mapping, location)
            location["is_grass"] = check_if_grassland(
                tif_file, category_mapping, [location]
            )[0]
        elif "deims_id" in location:
            location = ut_cop.get_deims_coordinates(location["deims_id"])
            location["category"] = get_categories(tif_file, category_mapping, location)
            location["is_grass"] = check_if_grassland(
                tif_file, category_mapping, [location]
            )[0]
        else:
            raise ValueError(
                "No location defined. Please provide coordinates ('lat', 'lon') or DEIMS.iD!"
            )

    # Final confirmation statement.
    print("Grassland check completed.")


# EXAMPLE USE


# Initial confirmation statement.
# print("Starting grassland check...")

# Test use (TIF and legend file need to be in the project root's subfolder "landCoverMapsTif")
# map_key = "GER_Preidl"
map_key = "EUR_Pflugmacher"  # "EUR_..."
# tif_file, category_mapping = get_map_and_legend(map_key)

# Example to get coordinates from DEIMS.iDs from XLS file
elter_xls_file = (
    ut.get_package_root()
    / "elterCallGrasslandSites"
    / "_elter_grassland_reply_CWohner_SVenier__extended_TBanitz.xlsx"
)
locations = ut.get_deims_ids_from_xls(elter_xls_file, header_row=1)
check_coordinates(locations, map_key)


coordinates_checked = []

# for deims_id in locations:
#     coord = ut_cop.get_deims_coordinates(deims_id)

#     if coord["found"]:
#         coord["deims_id"] = deims_id
#         coord["is_grass"] = check_if_grassland(tif_file, category_mapping, [coord])[0]
#         coordinates_checked.append(coord)


# Some example coordinates for checking wihtout DEIMS.iDs
locations = [
    {"lat": 51.3919, "lon": 11.8787},  # GER, GCEF grassland site
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


check_coordinates(locations, map_key)

# for coord in coordinates_checked:
#     # Check locations for grassland if not already done (during DEIMS.iD search).
#     if not "is_grass" in coord:
#         coord["is_grass"] = check_if_grassland(tif_file, category_mapping, [coord])[0]
