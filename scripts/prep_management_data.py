"""
Module Name: prep_management_data.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: April, 2024
Description: Download management data and prepare as needed for GRASSMIND input. 

Management data source 'GER_Lange' map:
    Lange, Maximilian; Feilhauer, Hannes; Kühn, Ingolf; Doktor, Daniel (2022):
    Mapping land-use intensity of grasslands in Germany with machine learning and Sentinel-2 time series,
    Remote Sensing of Environment, https://doi.org/10.1016/j.rse.2022.112888

    Based on grassland classifaction according to:
        German ATKIS digital landscape model 2015.

Management data source 'GER_Schwieder' map:
    Schwieder, Marcel; Wesemeyer, Maximilian; Frantz, David; Pfoch, Kira; Erasmi, Stefan; Pickert, Jürgen;
    Nendel, Claas; Hostert, Patrick (2022):
    Mapping grassland mowing events across Germany based on combined Sentinel-2 and Landsat 8 time series,
    Remote Sensing of Environment, https://doi.org/10.1016/j.rse.2021.112795

    Based on grassland classification according to:
        Blickensdörfer, Lukas; Schwieder, Marcel; Pflugmacher, Dirk; Nendel, Claas; Erasmi, Stefan; 
        Hostert, Patrick (2021):
        National-scale crop type maps for Germany from combined time series of Sentinel-1, Sentinel-2 and 
        Landsat 8 data (2017, 2018 and 2019), https://zenodo.org/records/5153047.

Mowing default dates according to:
    Filipiak, Matthias; Gabriel, Doreen; Kuka, Katrin (2022):
    Simulation-based assessment of the soil organic carbon sequestration in grasslands in relation to 
    management and climate change scenarios, https://doi.org/10.1016/j.heliyon.2023.e17287

    See also:
        Schmid, Julia (2022): 
        Modeling species-rich ecosystems to understand community dynamics and structures emerging from 
        individual plant interactions, PhD thesis, Chapter 4, Table C.7, https://doi.org/10.48693/160
"""

import argparse
# from copernicus import utils as ut_cop
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
import utils as ut
import warnings


def construct_management_data_file_name(folder, location, years, map_key, file_suffix):
    """
    Construct data file name.

    Parameters:
        folder (str or Path): Folder where data file will be stored.
        location (str or dict): Location information ('DEIMS.iD' or {'lat': float, 'lon': float}).
        years (list): List of years covered by management data.
        map_key (str): Key to identify land use map.
        file_suffix (str): File suffix (e.g. '.txt').

    Returns:
        Path: Constructed data file name as a Path object.
    """
    # Get folder with path appropriate for different operating systems
    folder = Path(folder)

    if ("lat" in location) and (
        "lon" in location
    ):  # location as dictionary with lat, lon
        formatted_lat = f"lat{location['lat']:.6f}"  # .replace(".", "-")
        formatted_lon = f"lon{location['lon']:.6f}"  # .replace(".", "-")
        file_start = f"{formatted_lat}_{formatted_lon}"
    elif "deims_id" in location:  # DEIMS.iD
        file_start = location["deims_id"]
    elif isinstance(location, str):  # location as string (DEIMS.iD)
        file_start = location
    else:
        raise ValueError("Unsupported location format.")

    file_name = (
        folder
        / f"{file_start}__{years[0]}-01-01_{years[-1]}-12-31__management__{map_key}{file_suffix}"
    )

    return file_name


def management_data_to_txt_file(
    map_key,
    map_properties,
    location,
    years,
    management_data,
    is_raw_data=False,
    fill_mode="none",
):
    """
    Write management data to a text file.

    Parameters:
        map_key (str): Key to identify land use map.
        map_properties (list): List of map properties.
        location (str or dict): Location information ('DEIMS.iD' or {'lat': float, 'lon': float}).
        years (list): List of years covered by management data.
        management_data (numpy.ndarray): Management data.
        is_raw_data (bool): Whether data are raw (default is False).
        fill_mode (str): Method for completing missing data (default is 'none').

    Returns:
        None
    """
    # Create data file name and header line
    if is_raw_data:
        file_name = construct_management_data_file_name(
            "managementDataRaw", location, years, map_key, "_Raw.txt"
        )

        # Header line, capitalize only the first letter of each string
        management_columns = [s.capitalize() for s in ["Year"] + map_properties]
        management_fmt = "%.0f" + "\t%.4f" * len(map_properties)  # no digits for year
        print_message = (
            f"Text file with raw management data from '{map_key}' map prepared."
        )
    else:
        if fill_mode == "none":
            file_end = ".txt"
        else:
            file_end = f"__fill_{fill_mode}.txt"

        file_name = construct_management_data_file_name(
            "managementDataPrepared", location, years, map_key, file_end
        )
        management_columns = [
            "Date",
            "MowHeight[m]",
            "Fertilizer[gm-2]",
            "Irrigation[mm]",
            "Seeds_PFT1",
            "Seeds_PFT2",
            "Seeds_PFT3",
        ]
        management_fmt = "%s\t%s\t%s\t%s\t%s\t%s\t%s"
        print_message = (
            f"Text file with final management data from '{map_key}' map prepared."
        )

        # Prepare empty management data for writing to file
        if not management_data:
            management_data = np.empty((0, len(management_columns)), dtype=str)

    # Create data directory if missing
    Path(file_name).parent.mkdir(parents=True, exist_ok=True)

    np.savetxt(
        file_name,
        management_data,
        delimiter="\t",
        fmt=management_fmt,
        header="\t".join(management_columns),
        comments="",
    )

    print(print_message)


def get_management_map_file(
    map_key, year, property="mowing", applicability=False, map_local=False
):
    """
    Generate file path or URL for a management map based on provided map key, property name and year.

    Parameters:
        map_key (str): Key to identify land use map.
        year (str): Year.
        property (str): Management property (default is 'mowing').
        applicability (bool): Get area-of-applicability-map (default is False).
        map_local (bool): Read map from local file (default is False).

    Returns:
        pathlib.Path: File path to the land use map.
    """
    if map_key == "GER_Lange":
        if map_local:
            # Return local map file
            file_name = (
                "S2_Germany_" + str(year) + "_AOA_" + property + ".tif"
                if applicability
                else "S2_Germany_" + str(year) + "_" + property + ".tif"
            )
            map_file = ut.get_package_root() / "landUseMaps" / map_key / file_name

            if map_file.is_file():
                return map_file
            else:
                print(
                    f"Error: Local file '{map_file}' not found! Trying to access via url..."
                )
                map_local = False

        if not map_local:
            # Return map file URL
            if year == 2017:
                if applicability:
                    if property == "mowing":
                        file_name = "98d7c7ab-0a8f-4c2f-a78f-6c1739ee9354"
                    elif property == "fertilisation":
                        file_name = "7a4b70a9-95b3-4a06-ae8b-082184144494"
                    elif property == "grazing":
                        file_name = "e83a9d4a-ea55-44dd-b3fb-2ee7cb046e92"
                    elif property == "LUI":
                        file_name = "4e7ab052-bd47-4ccf-9560-57ceb080945a"
                    else:
                        warnings.warn(
                            f"Property '{property}' not found in '{map_key}' map!",
                            UserWarning,
                        )

                        return None
                else:
                    if property == "mowing":
                        file_name = "14a1d2b6-11c8-4e31-ac19-45a7b805428d"
                    elif property == "fertilisation":
                        file_name = "deaca5bf-8999-4ccf-beac-ab47210051f6"
                    elif property == "grazing":
                        file_name = "611798da-e43d-4de6-9ff5-d5fb562fbf46"
                    elif property == "LUI":
                        file_name = "54995bd6-2811-4198-ba55-675386510260"
                    else:
                        warnings.warn(
                            f"Property '{property}' not found in '{map_key}' map!",
                            UserWarning,
                        )

                        return None
            elif year == 2018:
                if applicability:
                    if property == "mowing":
                        file_name = "d871429a-b2a6-4592-b3e5-4650462a9ac3"
                    elif property == "fertilisation":
                        file_name = "3b24279c-e9ab-468d-86b8-fe1fadc121bf"
                    elif property == "grazing":
                        file_name = "69701524-ed47-4e4b-9ef2-e355f5103d76"
                    elif property == "LUI":
                        file_name = "0efe31de-1275-4cab-b470-af1ce9f28363"
                    else:
                        warnings.warn(
                            f"Property '{property}' not found in '{map_key}' map!",
                            UserWarning,
                        )

                        return None
                else:
                    if property == "mowing":
                        file_name = "0eb6a466-417b-4b30-b5f8-070c3f2c99c3"
                    elif property == "fertilisation":
                        file_name = "aa81ef4f-4ed4-489a-9d52-04d1fd3a357a"
                    elif property == "grazing":
                        file_name = "2bc29d3f-08d1-4508-a0ca-c83517216f69"
                    elif property == "LUI":
                        file_name = "28b419a6-c282-42fa-a23a-72676a288171"
                    else:
                        warnings.warn(
                            f"Property '{property}' not found in '{map_key}' map!",
                            UserWarning,
                        )

                        return None
            else:
                warnings.warn(
                    f"'{map_key}' {property} map not available for {year}!", UserWarning
                )

                return None
            map_file = (
                "https://data.mendeley.com/public-files/datasets/m9rrv26dvf/files/"
                + file_name
                + "/file_downloaded"
            )

            if ut.check_url(map_file):
                return map_file
            else:
                print(f"Error: File '{map_file}' not found!")
    elif map_key == "GER_Schwieder":
        if year in [2017, 2018, 2019, 2020, 2021]:
            file_name = "GLU_GER_" + str(year) + "_SUM_DOY_COG.tif"

            if map_local:
                map_file = (
                    Path(r"c:/_D/biodt_data/") / "landUseMaps" / map_key / file_name
                )  # ut.get_package_root() / "landUseMaps" / map_key / file_name

                if map_file.is_file():
                    return map_file
                else:
                    print(
                        f"Error: Local file '{map_file}' not found! Trying to access via url..."
                    )
                    map_local = False

            if not map_local:
                map_file = (
                    "http://134.94.199.14/grasslands-pdt/landUseMaps/"
                    + map_key
                    + "/"
                    + file_name
                )  # or zenodo address: "https://zenodo.org/records/10609590/files/" + file_name

                if ut.check_url(map_file):
                    return map_file
                else:
                    print(f"Error: File '{map_file}' not found!")
        else:
            warnings.warn(
                f"'{map_key}' {property} map not available for {year}!", UserWarning
            )

            return None


def get_GER_Lange_data(coordinates, map_properties, years):
    """
    Read management data for given coordinates from GER_Lange map for respective year and return as array.

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

    # Initialize property_data array with nans
    property_data = np.full(
        (len(years), len(map_properties) + 1),
        np.nan,
        dtype=float,
    )
    warn_no_grassland = True

    # Extract values from tif maps for each year and each property
    for y_index, year in enumerate(years):
        # Add year to management data
        property_data[y_index, 0] = year

        # Add management properties from tif maps
        for p_index, property in enumerate(map_properties, start=1):
            # Extract property value
            map_file = ut.check_url(
                get_management_map_file(map_key, year, property, applicability=False)
            )

            if map_file:
                print(
                    f"{property[0].upper() + property[1:]} map for {year} found. Using '{map_file}'."
                )

                # Extract and check AOA value
                aoa_file = ut.check_url(
                    get_management_map_file(map_key, year, property, applicability=True)
                )

                if aoa_file:
                    print(
                        f"{property[0].upper() + property[1:]} map AOA for {year} found. Using '{aoa_file}'."
                    )
                    within_aoa = ut.extract_raster_value(aoa_file, coordinates)

                    if within_aoa == -1:
                        if warn_no_grassland:
                            warnings.warn(
                                f"Location not classified as grassland in '{map_key}' map.",
                                UserWarning,
                            )
                            warn_no_grassland = False
                        break

                    property_value = ut.extract_raster_value(map_file, coordinates)

                    if within_aoa:
                        print(
                            f"{year}, {property} : {property_value}. Within area of applicability."
                        )
                        property_data[y_index, p_index] = property_value
                    else:
                        print(
                            f"{year}, {property} : {property_value}. Not used, outside area of applicability!"
                        )

    return property_data


def get_GER_Schwieder_data(coordinates, map_properties, years):
    """
    Read mowing data for given coordinates from GER_Schwieder map for respective year and return as array.
        Schwieder, Marcel; Wesemeyer, Maximilian; Frantz, David; Pfoch, Kira; Erasmi, Stefan; Pickert, Jürgen;
        Nendel, Claas; Hostert, Patrick (2022):
        Mapping grassland mowing events across Germany based on combined Sentinel-2 and Landsat 8 time series,
        Remote Sensing of Environment, https://doi.org/10.1016/j.rse.2021.112795

        Only works for locations classified as (permanent) grassland in 2017, 2018 and 2019 according to
        Blickensdörfer et al. (2021), https://zenodo.org/records/5153047.

        Properties:
            Mowing: number of moving events (max. 6) and their dates (day of year).

    Parameters:
        coordinates (tuple): Coordinates ('lat', 'lon') to extract management data.
        map_properties (list): List of properties to extract.
        years (list): List of years to process.

    Returns:
        numpy.ndarray: 2D array containing property data for given years (nan if no grassland or no further mowing event).
    """
    map_key = "GER_Schwieder"
    print(f"Reading management data from '{map_key}' map...")
    map_bands = len(map_properties)
    property = map_properties[0]

    if property != "mowing":
        raise ValueError(
            f"First property to read from '{map_key}' map must be 'mowing'!"
        )

    # Initialize property_data array with nans
    property_data = np.full(
        (
            len(years),
            map_bands + 1,
        ),
        np.nan,
        dtype=object,
    )
    warn_no_grassland = True

    # Extract values from tif maps for each year and each property
    for y_index, year in enumerate(years):
        # Add year to management data
        property_data[y_index, 0] = year
        map_file = ut.check_url(get_management_map_file(map_key, year))

        if map_file:
            print(f"{property.capitalize()} map for {year} found. Using '{map_file}'.")

            # Read mowing events (band 1)
            band_index = 1
            band_value = ut.extract_raster_value(
                map_file, coordinates, band_number=band_index
            )

            if band_value == -9999:
                if warn_no_grassland:
                    warnings.warn(
                        f"Location not classified as grassland in '{map_key}' map.",
                        UserWarning,
                    )
                    warn_no_grassland = False
            else:
                property_data[y_index, band_index] = band_value
                print(f"{year}, {property}: {band_value} event(s).")

                # Add mowing dates if available (bands 2 to end)
                for band_index in range(2, map_bands + 1):
                    band_value = ut.extract_raster_value(
                        map_file, coordinates, band_number=band_index
                    )

                    if band_value != 0:
                        property_data[y_index, band_index] = band_value
                        band_date = ut.day_of_year_to_date(year, int(band_value))
                        print(
                            f"{property.capitalize()} event {band_index - 1}: {band_date.strftime('%Y-%m-%d')}."
                        )

    return property_data


def get_mow_events(year, mow_days, mow_height, leap_year_considered=True):
    """
    Generate mowing event entries for a given year based on specified days and height.

    Parameters:
        year (int): Year for which to generate mowing events.
        mow_days (list of int): Days of year to schedule mowing.
        mow_height (float): Height of mowing (in meters).
        leap_year_considered (bool): Whether leap year was already considered for mow_days (default is True).

    Returns:
        list of list: list of mowing events in Grassmind management input data format,
        one row for each mow_day, containing:
            column 0: date string in format YYYY-MM-DD
            column 1: value of mow_height
            columns 2 to 6: 'NaN' (for no fertilisation, no irrigation and no seeds at this management event)
    """
    # Create result array, date and mow height in first rows, NaN for all other management rows
    mow_events = []
    for day_of_year in mow_days:
        mow_date = ut.day_of_year_to_date(year, day_of_year, leap_year_considered)
        row = [
            mow_date.strftime("%Y-%m-%d"),
            mow_height,
            "NaN",
            "NaN",
            "NaN",
            "NaN",
            "NaN",
        ]
        mow_events.append(row)

    return mow_events


def get_mow_schedule(year, mow_count, mow_height):
    """
    Generate a schedule of mowing dates based on number of mowings (mow_count) for a given year.

    Parameters:
        year (int): Year for which to generate the schedule.
        mow_count (float): Number of mowing events (expected to be between 1 and 5).
        mow_height (float): Height of mowing (in meters).

    Returns:
        numpy.ndarray: Array with mowing events in Grassmind management input data format,
        mow_count rows, each row containing:
            column 0: date string in format YYYY-MM-DD
            column 1: value of mow_height
            columns 2 to 6: value NaN (for no fertilisation, no irrigation and no seeds at this management event)
    """
    # Check if mow_count is NaN
    if np.isnan(mow_count):
        warnings.warn("mow_count is NaN. No schedule will be generated.", UserWarning)

        return np.array([])

    # Check if mow_count is between 1 and 5
    if mow_count < 1:
        mow_count = 1
        warnings.warn(
            "'mow_count' is smaller than 1! Value between 1 and 5 expected. Set to 1.",
            UserWarning,
        )
    elif mow_count > 5:
        mow_count = 5
        warnings.warn(
            "'mow_count' is greater than 5! Value between 1 and 5 expected. Set to 5.",
            UserWarning,
        )

    # Convert mow_count to int
    mow_count = int(mow_count)

    # Define specific days for each number of mow events (cf. Filipiak et al. 2022, Table S6)
    mow_days = {
        1: [213],  # 08-01
        2: [121, 244],  # 05-01, 09-01
        3: [121, 182, 244],  # 05-01, 07-01, 09-01
        4: [105, 166, 213, 274],  # 04-15, 06-15, 08-01, 10-01
        5: [91, 135, 182, 227, 288],  # 04-01, 05-15, 07-01, 08-15, 10-15
    }

    mow_events = get_mow_events(
        year, mow_days[mow_count], mow_height, leap_year_considered=False
    )

    return mow_events


def get_fert_days(mow_days, year):
    """
    Calculate fertilisation dates based on mowing dates for a given year.

    Using time differences between fertilization and mowing events, respectively, according to Filipiak et al. 2022, Table S6.

    Parameters:
        mow_days (list of int): List with day of year for each mowing event.
        year (int): Year for which to calculate the fertlization events.        

    Returns:
        list of int: List with day of year for each fertilisation event.
    """
    event_count = len(mow_days)
    days_ahead = {
        0: [],  # allow empty mow day lists
        1: [122],
        2: [30, 78],
        3: [47, 47, 48],
        4: [45, 45, 31, 47],
        5: [31, 30, 30, 31, 44],
    }

    if event_count not in days_ahead:
        raise ValueError(
            f"No fertilisation day values defined for list of {event_count} mow days."
        )

    deltas = days_ahead[event_count]
    fert_days = []

    # Set earliest possible fertilisation date to 03-01
    earliest_fert_day = 61 if ut.is_leap_year(year) else 60
    earliest_fert_date_str = ut.day_of_year_to_date(year, earliest_fert_day).strftime("%Y-%m-%d")

    # Calculate fertilisation dates using specific days ahead of corresponding mow events
    for idx, mow_day in enumerate(mow_days):
        fert_day = mow_day - deltas[idx]

        if fert_day < earliest_fert_day:            
            print(
                f"Warning: Calculated fertilisation date {ut.day_of_year_to_date(year, fert_day).strftime("%Y-%m-%d")}"
                f" is before earliest date allowed! Set to {earliest_fert_date_str}."
            )
            fert_day = earliest_fert_day
        fert_days.append(fert_day)

    return fert_days


def fert_days_from_mow_days(mow_days_per_year, years):
    """
    Calculate fertilisation dates based on mowing dates.

    Using time differences between fertilization and mowing events, respectively, according to Filipiak et al. 2022, Table S6.

    Parameters:
        mow_days (list of list): List of lists with day of year for each mowing event for each year.
        yeard (list of int): Year for which to calculate the fertlization events.        

    Returns:
        list of list: List of lists with day of year for each fertilisation event for each year.
    """
    fert_days_per_year = []

    for idx, year in enumerate(years):
        fert_days = get_fert_days(mow_days_per_year[idx], year)
        fert_days_per_year.append(fert_days)

    return fert_days_per_year


def get_fert_schedule(year, fert_count, fert_days=None):
    """
    Generate a schedule of fertilisation dates based on number of events for a given year.

    Parameters:
        year (int): Year for which to generate the schedule.
        fert_count (float): Number of fertilisation events (expected to be between 1 and 5).
        fert_days (list of int): Optional list with day of year for each event (default is None).

    Returns:
        numpy.ndarray: Array with fertilisation events in Grassmind management input data format,
        fert_count rows, each row containing:
            column 0: date string in format YYYY-MM-DD
            column 1: value NaN (for no mowing at this management event)
            column 2: value of fert_amount
            columns 3 to 6: value NaN (for no irrigation and no seeds at this management event)
    """
    # Check if fert_count is NaN
    if np.isnan(fert_count):
        warnings.warn("fert_count is NaN. No schedule will be generated.", UserWarning)

        return np.array([])

    # Check if fert_count is between 1 and 5
    if fert_count < 1:
        fert_count = 1
        warnings.warn(
            "'fert_count' is smaller than 1! Value between 1 and 5 expected. Set to 1.",
            UserWarning,
        )
    elif fert_count > 5:
        fert_count = 5
        warnings.warn(
            "'fert_count' is greater than 5! Value between 1 and 5 expected. Set to 5.",
            UserWarning,
        )

    # Convert fert_count to int
    fert_count = int(fert_count)

    # Check if specific days for fertilisation events are provided
    if fert_days:
        if len(fert_days) > fert_count:
            warnings.warn(
                f"List of fertilisation days for {year} has more entries than 'fert_count'."
                f" Only first {fert_count} days will be used!",
                UserWarning,
            )
        elif len(fert_days) < fert_count:
            warnings.warn(
                f"List of fertilisation days for {year} has fewer entries than expected for 'fert_count' = {fert_count}."
                " List not used, replaced by standard schedule!",
                UserWarning,
            )
            fert_days = None

    if not fert_days:
        # Define specific days for each number of fertilisation events (cf. Filipiak et al. 2022, Table S6)
        fert_days_default = {
            1: [91],  # 04-01
            2: [91, 166],  # 04-01, 06-15
            3: [74, 135, 196],  # 03-15, 05-15, 07-15
            4: [60, 121, 182, 227],  # 03-01, 05-01, 07-01, 08-15
            5: [60, 105, 152, 196, 244],  # 03-01, 04-15, 06-01, 07-15, 09-01
        }
        fert_days = fert_days_default[fert_count]

    # Define specific amounts for each number of fertilisation events (cf. Filipiak et al. 2022, Table S6)
    fert_amounts = {  # in g/m²
        1: [5.5],
        2: [6.5, 3.5],
        3: [12.5, 3.25, 3.25],
        4: [16.5, 4, 2, 2],
        5: [21, 2.5, 2.5, 2.5, 2.5],
    }

    # Create result array, date in first row, fertilisation amount in third row, NaN for all other management rows
    fert_events = []

    for d_index, day_of_year in enumerate(fert_days):
        fert_date = ut.day_of_year_to_date(
            year, day_of_year, leap_year_considered=False
        )
        row = [
            fert_date.strftime("%Y-%m-%d"),
            "NaN",
            fert_amounts[fert_count][d_index],
            "NaN",
            "NaN",
            "NaN",
            "NaN",
        ]
        fert_events.append(row)

    return fert_events


def convert_management_data(
    management_data_raw, map_key, fill_mode, mow_height=0.05, mow_count_default=2
):
    """
    Convert raw management data into structured mowing and fertilisation events.

    Parameters:
        management_data_raw (list of list): Raw management data containing yearly mowing and fertilisation info.
        map_key (str): Key to identify land use map ('GER_Lange' or 'GER_Schwieder').
        fill_mode (str): Method for completing missing data.
        mow_height (float): Height of mowing (in meters, default is 0.05).
        mow_count_default (int): Number of annual events when using fill_mode 'default' for completing data (default is 2).

    Returns:
        list of list: List of mowing events in Grassmind management input data format,
        one row for each management event, containing:
            column 0: date string in format YYYY-MM-DD
            column 1: value of mowing height (if mowing event, otherwise 'NaN')
            column 2: value of fertilisation amount (if fertilisation event, otherwise 'NaN')
            columns 3 to 6: 'NaN' (for no irrigation and no seeds at this management event)
    """
    management_events = []
    years = np.array([int(entry[0]) for entry in management_data_raw])
    years_with_mow_data = np.array([])
    mow_days_per_year = [[] for _ in range(len(years))]
    fert_days_per_year = [[] for _ in range(len(years))]

    # MOWING
    if map_key in ["GER_Lange", "GER_Schwieder"]:
        # Read mowing, same column for "GER_Lange" and "GER_Schwieder"
        mow_count_per_year = np.array([entry[1] for entry in management_data_raw])
        years_with_mow_data = years[~np.isnan(mow_count_per_year)]

        if map_key == "GER_Lange":
            # Add mowing events to management events, using default schedule
            for idx in np.where(mow_count_per_year > 0)[0]:
                mow_schedule = get_mow_schedule(
                    years[idx], mow_count_per_year[idx], mow_height
                )
                management_events.extend(mow_schedule)
        elif map_key == "GER_Schwieder":
            # Get specific mowing dates for each year with mowing, add to management events
            for idx in np.where(mow_count_per_year > 0)[0]:
                entry = management_data_raw[idx]
                mow_days_per_year[idx] = [
                    int(x) for x in entry[2 : int(mow_count_per_year[idx]) + 2]
                ]
                mow_events = get_mow_events(
                    years[idx],
                    mow_days_per_year[idx],
                    mow_height,
                    leap_year_considered=True,
                )
                management_events.extend(mow_events)

    # Fill mowing for years without data
    fill_mode = fill_mode.lower()
    epsilon = 1e-10
    mow_count_fill = 0
    no_mow_data_for_mean = False

    if fill_mode == "mean":
        # Use means of data retrieved for remaining years as well
        print("Completing management data with means from years with data...")
        
        if years_with_mow_data.size > 0:
            mow_count_float = (
                np.nanmean(mow_count_per_year)
            )
            mow_count_fill = round(mow_count_float + epsilon)
            print(
                f"Mean annual mowing events: {mow_count_float:.4f} "
                f"(from {years_with_mow_data.size} years). "
                f"Using {mow_count_fill} events per year."
            )
        else:
            # No data for any of the years, use default option instead
            print(
                "No mowing data for any year to calculate mean and complete other years."
            )
            no_mow_data_for_mean = True

    if fill_mode == "default" or no_mow_data_for_mean:
        # Use default management settings for years without data
        mow_count_fill = mow_count_default
        print(
            "Completing management data with default values... "
            f"Using {mow_count_fill} events per year."
        )           

    mow_count_per_year[np.isnan(mow_count_per_year)] = mow_count_fill

    # Add all remaining mowing events to schedule
    for idx, year in enumerate(years):
        if mow_count_per_year[idx] > 0 and not year in years_with_mow_data:
            mow_schedule = get_mow_schedule(year, mow_count_fill, mow_height)
            management_events.extend(mow_schedule)

    # FERTILISATION
    if map_key == "GER_Lange":
        # Read fertilisation data for "GER_Lange"
        fertilised_per_year = np.array([entry[2] for entry in management_data_raw])
        fert_count_per_year = np.zeros_like(fertilised_per_year)

        # If data say fertilisation, adapt number of events to mowing events (even if mowing==0)!
        for idx in np.where(fertilised_per_year == 1)[0]:
            fert_count_per_year[idx] = mow_count_per_year[idx]

        # Fill fertilisation years without data
        idx_to_fill = np.where(np.isnan(fertilised_per_year))[0]
        no_fert_data_for_mean = False

        if fill_mode == "mean":
            if np.any(~np.isnan(fertilised_per_year)):
                # Use means of data retrieved for remaining years as well
                fert_count_float = np.mean(
                    fert_count_per_year[~np.isnan(fertilised_per_year)]
                )
                fert_count_fill = round(fert_count_float + epsilon)
                print(
                    f"Mean number of fertilisation events: {fert_count_float:.4f} per year. "
                    f"Using {fert_count_fill} events per year (but never more than mowing events of the same year)."
                )

                # Fill in fertilisation events, but not more than mowing events of the same year
                fert_count_per_year[idx_to_fill] = np.minimum(
                    fert_count_fill, mow_count_per_year[idx_to_fill]
                )
            else:
                # No data for any of the years, use default option instead
                print(
                    "No fertilisation data for any year to calculate mean and complete other years."
                )
                no_fert_data_for_mean = True

        if fill_mode == "default" or no_fert_data_for_mean:
            # Use number of mowing events as default for years without fertilisation data
            print(
                "Using the same number of fertilisation events as mowing events for each year."
            )
            fert_count_per_year[idx_to_fill] = mow_count_per_year[idx_to_fill]
    elif map_key == "GER_Schwieder":
        if fill_mode in ["mean", "default"]:
            # No fertilisation data, use number of mowing events as default
            print(
                f"'{map_key}' map has no fertilisation data. "
                "Using the same number of fertilisation events as mowing events for each year."
            )
            fert_count_per_year = mow_count_per_year
            fert_days_per_year = fert_days_from_mow_days(mow_days_per_year, years)

    # Add all fertilisation events to schedule
    for idx, year in enumerate(years):
        if fert_count_per_year[idx] > 0:
            fert_schedule = get_fert_schedule(
                year, fert_count_per_year[idx], fert_days_per_year[idx]
            )
            management_events.extend(fert_schedule)

    return sorted(management_events)


def data_processing(
    map_key, fill_missing_data, mow_height, years, coordinates, deims_id
):
    """
    Read management data from land use map. Write to .txt files.

    Parameters:
        map_key (str): Key to identify land use map ('GER_Lange' or 'GER_Schwieder').
        fill_missing_data (str): String to identify method for filling missing data ('mean', 'default', 'none').
        mow_height (float): Height of mowing (in meters).
        years (list): List of years to process.
        coordinates (dict): Dictionary with 'lat' and 'lon' keys of location.
        deims_id (str): Identifier of eLTER site.
    """
    if coordinates is None:
        if deims_id:
            coordinates = ut.get_deims_coordinates(deims_id)
        else:
            raise ValueError(
                "No location defined. Please provide coordinates or DEIMS.iD!"
            )
    else:
        print(f"Latitude: {coordinates['lat']}, Longitude: {coordinates['lon']}")

    if map_key == "GER_Lange":
        map_properties = [
            "mowing",
            "fertilisation",
            "grazing",
            "LUI",
        ]  #  , "fertilisation", "grazing", "LUI"
        management_data_raw = get_GER_Lange_data(coordinates, map_properties, years)
    elif map_key == "GER_Schwieder":
        map_properties = [
            "mowing",
            "date_1",
            "date_2",
            "date_3",
            "date_4",
            "date_5",
            "date_6",
        ]
        management_data_raw = get_GER_Schwieder_data(coordinates, map_properties, years)
    else:
        raise ValueError(
            f"Map key '{map_key}' not found. Please provide valid map key!"
        )

    management_data_to_txt_file(
        map_key,
        map_properties,
        coordinates,
        years,
        management_data_raw,
        is_raw_data=True,
    )

    management_data_prepared = convert_management_data(
        management_data_raw, map_key, fill_missing_data, mow_height
    )

    management_data_to_txt_file(
        map_key,
        [],
        coordinates,
        years,
        management_data_prepared,
        is_raw_data=False,
        fill_mode=fill_missing_data,
    )


def prep_management_data(
    map_key,
    fill_missing_data,
    mow_height,
    years,
    coordinates,
    deims_id,
):
    """
    Prepare management data to be used as GRASSMIND input.

    Parameters:
        map_key (str): Key to identify land use map ('GER_Lange' or 'GER_Schwieder').
        fill_missing_data (str): String to identify the method for filling missing data ('mean', 'default', 'none').
        mow_height (float): Height of mowing (in meters).
        years (list or None): List of years to process, or 'None' for default value.
        coordinates (dict): Coordinates dictionary with 'lat' and 'lon', or 'None' using DEIMS.iD.
        deims_id (str or None): DEIMS.iD, or 'None' for default value.

    """

    if years is None:
        years = list(range(2013, 2024))  # list(range(2017, 2019))

    if fill_missing_data is None:
        fill_missing_data = "default"

    # Example to get multiple coordinates from DEIMS.iDs from XLS file, filter only Germany
    file_name = ut.get_package_root() / "grasslandSites" / "_elter_call_sites.xlsx"
    locations = ut.get_deims_ids_from_xls(file_name, header_row=1, country="DE")

    # locations = [{"deims_id": "fd8b85c0-93ef-4a41-8706-3c4be9dec8e5"}]

    for location in locations:
        data_processing(
            map_key,
            fill_missing_data,
            mow_height,
            years,
            coordinates=None,
            deims_id=location["deims_id"],
        )

    # Example coordinates for checking without DEIMS.iDs
    locations = [
        {"lat": 51.390427, "lon": 11.876855},  # GER, GCEF grassland site
        {
            "lat": 51.3919,
            "lon": 11.8787,
        },  # GER, GCEF grassland site, centroid, non-grassland in HRL!
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

    for location in locations:
        data_processing(
            map_key,
            fill_missing_data,
            mow_height,
            years,
            coordinates=location,
            deims_id=None,
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
        "--map_key",
        type=str,
        default="GER_Schwieder",
        choices=["GER_Lange", "GER_Schwieder"],
        help="Options: 'GER_Lange', 'GER_Schwieder'. (Can be extended.)",
    )
    parser.add_argument(
        "--fill_missing_data",
        type=str,
        default="mean",
        choices=["mean", "default", "none"],
        help="Options: 'mean', 'default', 'none'.",
    )
    parser.add_argument(
        "--mow_height",
        type=float,
        default=0.05,
        help="Height of mowing (in meters).",
    )
    parser.add_argument("--years", nargs="*", type=int, help="List of years")
    parser.add_argument(
        "--coordinates",
        type=lambda s: dict(lat=float(s.split(",")[0]), lon=float(s.split(",")[1])),
        help="Coordinates as 'lat,lon'",
    )
    parser.add_argument("--deims_id", type=int, help="DEIMS.iD")

    args = parser.parse_args()

    prep_management_data(
        map_key=args.map_key,
        fill_missing_data=args.fill_missing_data,
        mow_height=args.mow_height,
        years=args.years,
        coordinates=args.coordinates,
        deims_id=args.deims_id,
    )


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
