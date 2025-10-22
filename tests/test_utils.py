"""
Module Name: test_utils.py
Description: Test utility functions for ucgrassland building block.

Developed by Thomas Banitz (UFZ) with contributions by Franziska Taubert (UFZ).

Copyright (C) 2025
- Helmholtz Centre for Environmental Research GmbH - UFZ, Germany

Licensed under the EUPL, Version 1.2 or - as soon they will be approved
by the European Commission - subsequent versions of the EUPL (the "Licence").
You may not use this work except in compliance with the Licence.

You may obtain a copy of the Licence at:
https://joinup.ec.europa.eu/software/page/eupl
"""

from pathlib import Path

import numpy as np
import pyproj
import pytest

from ucgrassland.utils import (
    add_string_to_file_name,
    download_file_opendap,
    get_source_from_elter_data_file_name,
    get_tuple_list,
    replace_substrings,
    reproject_coordinates,
)


def test_add_string_to_file_name(caplog):
    """Test add_string_to_file_name function."""
    test_cases = [
        ("data.txt", "_v2", "data_v2.txt"),
        ("report.csv", "_final", "report_final.csv"),
        ("image.jpeg", "_edited", "image_edited.jpeg"),
        ("no_extension", "_suffix", "no_extension_suffix"),
        ("/path/to/data.txt", "_v2", "/path/to/data_v2.txt"),
        ("./relative/path/report.csv", "_final", "./relative/path/report_final.csv"),
        (
            r"C:\absolute\path\image.jpeg",
            "_edited",
            r"C:\absolute\path\image_edited.jpeg",
        ),
    ]

    for original, string_to_add, expected in test_cases:
        result = add_string_to_file_name(original, string_to_add)
        assert result == Path(expected), f"Expected {expected}, got {result}"

    assert add_string_to_file_name("data.txt", "_v2", new_suffix=".csv") == Path(
        "data_v2.csv"
    ), "Failed to change file extension"

    with caplog.at_level("ERROR"):
        assert add_string_to_file_name("", "_v2") == "", "Failed on empty file name"
        assert "File name is empty. Cannot add string." in caplog.text


def test_get_source_from_elter_data_file_name(caplog):
    """Test get_source_from_elter_data_file_name function."""
    test_cases = [
        ("COUNTRYCODE_SITENAME_source.txt", "source"),
        (Path("COUNTRYCODE_SITENAME_source.txt"), "source"),
        ("CODE_site_data_source.csv", "data_source"),
        ("code.site_data_source__extra.info.txt", "data_source__extra_info"),
        ("randomfile.txt", ""),  # Invalid format
    ]

    with caplog.at_level("ERROR"):
        for file_name, expected_source in test_cases:
            result = get_source_from_elter_data_file_name(file_name)
            assert result == expected_source, (
                f"Expected {expected_source}, got {result}"
            )

        assert (
            "does not conform to expected eLTER data file name format. Cannot extract data source."
            in caplog.text
        )

    assert (
        get_source_from_elter_data_file_name(
            "one_two_three_four.suffix", front_strings_to_remove=1
        )
        == "two_three_four"
    )

    assert (
        get_source_from_elter_data_file_name(
            "one_two_three_four.suffix", front_strings_to_remove=3
        )
        == "four"
    )

    with pytest.raises(ValueError):
        get_source_from_elter_data_file_name(1234)  # file_name not str or Path


def test_replace_substrings(caplog):
    """Test replace_substrings function."""
    test_cases = [
        # Single string input
        ("hello world", "hello", "good bye", False, "good bye world"),
        ("hello world", "hello", "good bye", True, "hello world"),  # No change
        ("file.txt", ".txt", ".csv", True, "file.csv"),
        ("file.txt", ".txt", ".csv", False, "file.csv"),
        ("no match here", "absent", "present", False, "no match here"),  # No change
        # List of strings input
        (["cat", "bird", "dog"], "bird", "wolf", False, ["cat", "wolf", "dog"]),
        (["cat", "bird", "birds"], "bird", "wolf", True, ["cat", "wolf", "birds"]),
        (
            ["data.csv", "report.csv.zip"],
            ".csv",
            ".txt",
            False,
            ["data.txt", "report.txt.zip"],
        ),
        (
            ["data.csv", "report.csv.zip"],
            ".csv",
            ".txt",
            True,
            ["data.txt", "report.csv.zip"],
        ),
        (["no match"], "absent", "present", False, ["no match"]),  # No change
        # Mixed types in list with warning
        (
            ["valid string", 123, None],
            "string",
            "text",
            False,
            ["valid text", 123, None],
        ),
        # List of lists input
        (
            [["apple", "banana"], ["cherry", "date"]],
            "a",
            "A",
            False,
            [["Apple", "bAnAnA"], ["cherry", "dAte"]],
        ),
        (
            [["apple", "banana"], ["cherry", "date"]],
            "a",
            "A",
            True,
            [["apple", "bananA"], ["cherry", "date"]],
        ),
    ]

    for (
        input_data,
        substrings_to_replace,
        replacement_string,
        at_end,
        expected,
    ) in test_cases:
        if isinstance(input_data, list) and any(
            not isinstance(item, str) for item in input_data
        ):
            with caplog.at_level("WARNING"):
                result = replace_substrings(
                    input_data,
                    substrings_to_replace,
                    replacement_string,
                    at_end=at_end,
                    warning_no_string=True,
                )
                assert (
                    caplog.text.count("is not a string. No replacements performed.")
                    == 2
                )
        else:
            result = replace_substrings(
                input_data,
                substrings_to_replace,
                replacement_string,
                at_end=at_end,
            )
        assert result == expected, f"Expected {expected}, got {result}"

    caplog.clear()

    with caplog.at_level("ERROR"):
        with pytest.raises(ValueError):
            replace_substrings(1234, "old", "new")  # input_data not str or list

        assert (
            "Input data must be a string, a list of strings, or a list of lists."
            in caplog.text
        )


def test_get_tuple_list(caplog):
    """Test get_tuple_list function, which converts a list of lists or tuples or strings to a list of tuples, with parameters:
    input_list (list): List of lists or tuples or strings.
        replace_nan (str): String to replace nan values (default is 'nan').
        replace_none (str): String to replace None values (default is 'None').
        columns_to_remove (list): List of column indices to remove (default is empty).
        return_sorted (bool): Whether to return the list sorted (default is False).
        header_lines (int): Number of header lines to skip and return unchanged in the output (default is 0).
          Returns: list: List of tuples."""

    # Basic conversion with default parameters
    test_cases = [
        # list of lists
        ([[1, 2], [3, 4]], [(1, 2), (3, 4)]),
        # list of tuples
        ([(1, 2), (3, 4)], [(1, 2), (3, 4)]),
        # list of strings
        (["ab", "cd"], [("ab",), ("cd",)]),
        # with NaN and None replacement
        ([[1, np.nan], [None, 4]], [(1, "nan"), ("None", 4)]),
    ]

    for input_list, expected in test_cases:
        result = get_tuple_list(input_list)
        assert result == expected, f"Expected {expected}, got {result}"

    # Different replacement strings
    input_list = [(1, np.nan), (None, 4), ("None", "nan")]
    replace_nan = "NA"
    replace_none = "none value found"
    expected = [(1, replace_nan), (replace_none, 4), ("None", "nan")]
    result = get_tuple_list(
        input_list, replace_nan=replace_nan, replace_none=replace_none
    )
    assert result == expected, f"Expected {expected}, got {result}"

    # No replacements
    result = get_tuple_list(input_list, replace_nan=None, replace_none=None)
    assert result == input_list, f"Expected {input_list}, got {result}"

    # Remove specific columns
    input_list = [[1, 2, "3"], [4, 5, "6"], [7, 8, "9"]]
    expected = [(1, "3"), (4, "6"), (7, "9")]
    result = get_tuple_list(input_list, columns_to_remove=[1])
    assert result == expected, f"Expected {expected}, got {result}"

    input_list = [[1, 4, "b"], [1, 4, "a"], [2, 1, "a"], [1, 3, "c"], [1, 2, "d"]]
    expected = sorted([tuple(row) for row in input_list])
    result = get_tuple_list(input_list, return_sorted=True)
    assert result == expected, f"Expected {expected}, got {result}"

    expected = sorted([(row[0], row[2]) for row in input_list])
    result = get_tuple_list(input_list, columns_to_remove=[1], return_sorted=True)
    assert result == expected, f"Expected {expected}, got {result}"

    # Header lines
    input_list = ["Header line 1", "Header line 2", [3, 4], [1, 2]]
    expected = ["Header line 1", "Header line 2", (1, 2), (3, 4)]
    result = get_tuple_list(input_list, header_lines=2, return_sorted=True)
    assert result == expected, f"Expected {expected}, got {result}"

    # Invalid input types
    with caplog.at_level("ERROR"):
        with pytest.raises(ValueError):
            get_tuple_list("not a list")  # input_list not a list
            assert "Input must be a list of lists or tuples or strings." in caplog.text

        caplog.clear()
        with pytest.raises(ValueError):
            get_tuple_list([1, 2, 3])  # list entries not list, tuple, or string
            assert "Input must be a list of lists or tuples or strings." in caplog.text

        caplog.clear()
        with pytest.raises(ValueError):
            get_tuple_list([[1, 2], (3, 4), "ef"])  # mixed list
            assert (
                "Input list must contain only lists, or only tuples, or only strings."
                in caplog.text
            )

        caplog.clear()
        with pytest.raises(ValueError):
            get_tuple_list([[1, 2, 3], [4, 5]])
            assert (
                "All lists or tuples in the input list must have the same length."
                in caplog.text
            )

        caplog.clear()
        with pytest.raises(TypeError):
            get_tuple_list(
                [[1, 2, 3], [1, "5", 6]], return_sorted=True
            )  # column 1 not comparable
            assert "Cannot sort tuple list. Entries are not comparable." in caplog.text


def test_reproject_coordinates():
    """Test reproject_coordinates function."""
    # Input coordinates as lat lon pairs in EPSG:4326 (WGS 84) format
    lat_lon_pairs = [
        (52.52, 13.405),  # Berlin, Germany
        (60.1695, 24.9354),  # Helsinki, Finland
        (41.9028, 12.4964),  # Rome, Italy
    ]
    target_crs_list = [
        "EPSG:4326",  # WGS 84, same as input
        "EPSG:32633",  # WGS 84 / UTM zone 33N
        "EPSG:3035",  # ETRS89 / LAEA Europe
        "EPSG:3857",  # WGS 84 / Pseudo-Mercator
    ]

    for lat, lon in lat_lon_pairs:
        # Test if reprojecting to the same CRS as input returns the same coordinates
        assert reproject_coordinates(lat, lon, "EPSG:4326") == (lon, lat)

        # Test reprojecting to different target CRS, inlcuding the same as input
        for target_crs in target_crs_list:
            expected_east_north = pyproj.Transformer.from_crs(
                "EPSG:4326", target_crs, always_xy=True
            ).transform(lon, lat)
            generated_east_north = reproject_coordinates(lat, lon, target_crs)

            assert np.allclose(
                expected_east_north, generated_east_north, atol=0, rtol=1e-12
            )


def test_download_file_opendap(tmp_path, caplog):
    """Test download of a file from the OPeNDAP server."""
    # Create a temporary file name and download
    file_name = "test_file.txt"
    test_folder = "_test_folder"
    local_file_path = tmp_path / file_name

    download_file_opendap(file_name, test_folder, tmp_path)

    # Test that the downloaded file exists and has the expected content
    assert local_file_path.exists()
    assert local_file_path.is_file()

    with open(local_file_path, "r") as f:
        downloaded_content = f.read()
        assert downloaded_content.startswith("Test file content:")

    # Test download of a non-existing file
    file_name = "non_existing_file.txt"
    local_file_path = tmp_path / file_name

    with caplog.at_level("WARNING"):
        download_file_opendap(file_name, test_folder, tmp_path)

    assert f"File '{file_name}' not found on OPeNDAP server." in caplog.text
    assert local_file_path.exists() is False, "Local file should not exist."
