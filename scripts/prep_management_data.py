"""
Module Name: prep_management_data.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: April, 2024
Description: Download management data and prepare as needed for GRASSMIND input. 
"""

import argparse
from copernicus import utils as ut_cop
import numpy as np
from pathlib import Path
import utils as ut


def construct_management_data_file_name(folder, location, file_suffix):
    """
    Construct data file name.

    Parameters:
        folder (str or Path): Folder where the data file will be stored.
        location (str or dict): Location information ('DEIMS.iD' or {'lat': float, 'lon': float}).
        file_suffix (str): File suffix (e.g. '.txt').

    Returns:
        Path: Constructed data file name as a Path object.
    """
    # Get folder with path appropriate for different operating systems
    folder = Path(folder)

    if "deims_id" in location:  # DEIMS.iD
        file_start = location["deims_id"]
    elif ("lat" in location) and (
        "lon" in location
    ):  # location as dictionary with lat, lon
        formatted_lat = f"lat{location['lat']:.2f}".replace(".", "-")
        formatted_lon = f"lon{location['lon']:.2f}".replace(".", "-")
        file_start = f"{formatted_lat}_{formatted_lon}"
    elif isinstance(location, str):  # location as string (DEIMS.iD)
        file_start = location
    else:
        raise ValueError("Unsupported location format.")

    file_name = folder / f"{file_start}_Management{file_suffix}"

    return file_name


def management_data_to_txt_file(
    map_key,
    map_properties,
    location,
    management_data,
):
    """
    Write management data to a text file.

    Parameters:
        map_key (str): Key for the map.
        map_properties (list): List of map properties.
        location (str or dict): Location information ('DEIMS.iD' or {'lat': float, 'lon': float}).
        management_data (numpy.ndarray): Management data.

    Returns:
        None
    """
    # Create data file name and data directory if missing
    file_name = construct_management_data_file_name(
        "managementDataPrepared", location, ".txt"
    )
    Path(file_name).parent.mkdir(parents=True, exist_ok=True)

    # Header line for file, capitalize only the first letter of each string
    management_header = "\t".join(
        map(lambda x: x[0].upper() + x[1:], ["Year"] + map_properties)
    )

    np.savetxt(
        file_name,
        management_data,
        delimiter="\t",
        fmt=["%.0f"] + len(map_properties) * ["%.4f"],  # no digits for year
        header=management_header,
        comments="",
    )

    print(f"Text file with management data from '{map_key}' map prepared.")


def get_management_map_file(map_key, property, year, applicability=False):
    """
    Generate file path for a Management map based on the provided map key, property name and year.

    Parameters:
        map_key (str): Key to identify the land use map.
        property (str): Name of the management property (e.g. "mowing" or "fertilisation").
        depth (str): Year.
        applicability (bool): Get area-of-applicability-map (defaul is False).

    Returns:
        pathlib.Path: File path to the land use map.
    """
    if map_key == "GER_Lange":
        file_name = (
            "S2_Germany_" + str(year) + "_AOA_" + property + ".tif"
            if applicability
            else "S2_Germany_" + str(year) + "_" + property + ".tif"
        )

    return ut.get_package_root() / "landUseMaps" / map_key / file_name


def get_GER_Lange_data(coordinates, map_properties, years):
    """
    Read management data for the given coordinates from GER_Lange map for the respective year and return as array.
        Lange, Maximilian; Feilhauer, Hannes; Kühn, Ingolf; Doktor, Daniel (2022):
        Mapping land-use intensity of grasslands in Germany with machine learning and Sentinel-2 time series,
        Remote Sensing of Environment, https://doi.org/10.1016/j.rse.2022.112888

        Only works for locations classified as grassland according to German ATKIS digital landscape model 2015.

        Properties:
            Mowing: number of moving events.
            Fertilisation: information aggregated into fertilised or not fertilised.
            Grazing: classification bases on grazing intensity (G), given as livestock units (depending on species and age) per ha and day
                (Class 0: G=0, Class 1: 0 < G <= 0.33, Class 2: 0.33 < G <=0.88, Class 3: G > 0.88).
            LUI calculation based on Mowing, Fertilisation and Grazing (cf. Lange et al. 2022).

            Each property's model has a separate area of applicability for each year.

    Parameters:
        coordinates (tuple): Coordinates ('lat', 'lon') to extract management data.
        map_properties (list): List of properties to extract.
        years (list): List of years to process.

    Returns:
        numpy.ndarray: 2D array containing property data for given years (nan if no grassland or outside area of applicability).
    """
    map_key = "GER_Lange"
    print(f"Reading management data from '{map_key}' map...")
    ## TODO: add functionality for testing file availability, download from opendap..

    # Initialize property_data array with nans
    property_data = np.full(
        (
            len(years),
            len(map_properties) + 1,
        ),
        np.nan,
        dtype=float,
    )

    # Initialize non-grassland warning
    warn_no_grassland = True

    # Extract values from tif maps for each property and depth
    for y_index, year in enumerate(years):
        # Add year to the management data
        property_data[y_index, 0] = year

        # Add management properties from tif maps
        for p_index, property in enumerate(map_properties, start=1):
            # Extract property value
            tif_file = get_management_map_file(
                map_key, property, year, applicability=False
            )
            property_value = ut.extract_raster_value(tif_file, coordinates)

            # Extract and check AOA value
            tif_file = get_management_map_file(
                map_key, property, year, applicability=True
            )
            within_aoa = ut.extract_raster_value(tif_file, coordinates)

            if within_aoa == -1:
                if warn_no_grassland:
                    print(
                        f"Warning: Location not classified as grassland in '{map_key}' map."
                    )
                    warn_no_grassland = False

                # Only for checking.
                if not property_value == -1:
                    print(
                        f"Surprise: within_aoa = {within_aoa}, but property value = {property_value}."
                    )
            else:
                if within_aoa:
                    print(
                        f"{year}, {property} : {property_value}. Within area of applicability."
                    )
                    property_data[y_index, p_index] = property_value
                else:
                    print(
                        f"{year}, {property} : {property_value}. Not used, outside area of applicability!"
                    )

                if within_aoa not in [0, 1]:
                    # Only for checking.
                    print(f"Surprise: within_aoa = {within_aoa}")

    return property_data


def data_processing(map_key, years, coordinates, deims_id):
    """
    Read management data from land use map. Write to .txt files.

    Parameters:
        map_key (str): Key to identify the land use map.
        years (list): List of years to process.
        coordinates (list of dict): List of dictionaries with "lat" and "lon" keys.
        deims_id (str): Identifier of the eLTER site.
    """
    if coordinates is None:
        if deims_id:
            coordinates = ut_cop.get_deims_coordinates(deims_id)
        else:
            raise ValueError(
                "No location defined. Please provide coordinates or DEIMS.iD!"
            )

    if map_key == "GER_Lange":
        map_properties = [
            "mowing",
            "fertilisation",
            "grazing",
            "LUI",
        ]  #  , "fertilisation", "grazing", "LUI"
        management_data = get_GER_Lange_data(coordinates, map_properties, years)
    # elif map_key == "GER_Schwieder":
    #     # TODO...
    else:
        raise ValueError(
            f"Map key '{map_key}' not found. Please provide valid map key!"
        )

    management_data_to_txt_file(
        map_key,
        map_properties,
        coordinates,
        management_data,
    )


def prep_management_data(
    years,
    coordinates,
    deims_id,
    map_key,
):
    """
    Prepare management data to be used as GRASSMIND input.

    Parameters:
        years (list or None): List of years to process, or 'None' for default value.
        coordinates (dict): Coordinates dictionary with 'lat' and 'lon', or 'None' using DEIMS.iD.
        deims_id (str or None): DEIMS.iD, or 'None' for default value.
        map_key (str): Key to identify the land use map.
    """

    if years is None:
        years = list(range(2017, 2019))  # list(range(2017, 2019))

    # Example to get multiple coordinates from DEIMS.iDs from XLS file, filter only Germany
    file_name = ut.get_package_root() / "grasslandSites" / "_elter_call_sites.xlsx"
    locations = ut.get_deims_ids_from_xls(file_name, header_row=1, country="DE")

    for location in locations:
        data_processing(map_key, years, coordinates=None, deims_id=location["deims_id"])

    # # Example coordinates for checking without DEIMS.iDs
    # locations = [
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
    #
    # for location in locations:
    #     data_processing(map_key, years, coordinates=location, deims_id=None)


def main():
    """
    Runs the script with default arguments for calling the script.
    """

    parser = argparse.ArgumentParser(
        description="Set default arguments for calling the script."
    )

    # Define command-line arguments
    parser.add_argument("--years", nargs="*", type=int, help="List of years")
    parser.add_argument(
        "--coordinates",
        type=lambda s: dict(lat=float(s.split(",")[0]), lon=float(s.split(",")[1])),
        help="Coordinates as 'lat,lon'",
    )
    parser.add_argument("--deims_id", help="DEIMS.iD")
    parser.add_argument(
        "--map_key",
        type=str,
        default="GER_Lange",
        choices=["GER_Preidl", "GER_Schwieder"],
        help="Options: 'GER_Preidl', 'GER_Schwieder'. (Can be extended.)",
    )

    args = parser.parse_args()

    prep_management_data(
        years=args.years,
        coordinates=args.coordinates,
        deims_id=args.deims_id,
        map_key=args.map_key,
    )


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
