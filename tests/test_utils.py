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

import numpy as np
import pyproj

from ucgrassland.utils import reproject_coordinates


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
