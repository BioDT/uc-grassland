"""
Module Name: prep_observation_data.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: 2024
Description: Prepare eLTER observation data as needed for comparison to grassland model output.

Developed in the BioDT project (until 2025-05) by Thomas Banitz (UFZ) with contributions by Franziska Taubert (UFZ),
Tuomas Rossi (CSC) and Taimur Haider Khan (UFZ).

Further developed (from 2025-06) by Thomas Banitz (UFZ) with contributions by Franziska Taubert (UFZ).

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
from pathlib import Path
from types import MappingProxyType

import pandas as pd
from dotenv import dotenv_values

from ucgrassland import assign_pfts as apft
from ucgrassland import utils as ut
from ucgrassland.logger_config import logger

# Define observation data specifications for selected sites with grassland observation data, including:
#     name (str): Site name.
#     variables (list): List of observation variables.
#     file_names (dict): Dictionary with file names for observation variables.
#     observation_columns (dict): Dictionary with observation columns for observation variables.
#     pft_lookup_files (dict): Dictionary with PFT lookup file names for observation variables.
#     pft_lookup_specs (dict): Dictionary with PFT lookup specifications for observation variables.

# TODO: have layer in obs columns only if exisiting in data tables (can be empty though)
OBSERVATION_DATA_SPECS_PER_SITE = MappingProxyType(
    {
        "11696de6-0ab9-4c94-a06b-7ce40f56c964": {
            "name": "IT25 - Val Mazia-Matschertal",
            "variables": ["cover"],
            "short_names": {"cover": "VMM-C"},
            "file_names": {"cover": "IT_Matschertal_data_abund.csv"},
            "observation_columns": {"cover": "default", "management": "default"},
            "pft_lookup_files": {
                "cover": "lat46.692800_lon10.615700__PFT__data_abund.txt"
            },
            "pft_lookup_specs": {"cover": "default"},
            "station_file": "IT_Matschertal_station.csv",
            "start_year": 2009,
        },
        "270a41c4-33a8-4da6-9258-2ab10916f262": {
            "name": "AgroScapeLab Quillow (ZALF)",
            "variables": ["cover"],
            "short_names": {"cover": "ASQ-C"},
            # "file_names": {"cover": "DE_AgroScapeQuillow_data_cover.csv"},
            # "observation_columns": {"cover": "default"},
            "file_names": {
                "cover": "DE_AgroScapeQuillow_data_cover__from_SpeciesFiles.csv"
            },
            "observation_columns": {
                "cover": {
                    "plot": "STATION_CODE",
                    "subplot": "REPLICATION",
                    "time": "TIME",
                    "species": "TAXA",
                    "value": "VALUE",
                    "unit": "UNIT",
                },
                "management": None,
            },
            # "pft_lookup_files": {
            #     "cover": "lat53.360000_lon13.800000__PFT__data_cover.txt"
            # },
            # "pft_lookup_specs": {"cover": "default"},
            "pft_lookup_files": {"cover": "lat53.360000_lon13.800000__PFT__names.txt"},
            "pft_lookup_specs": {
                "cover": {
                    "key_column": "Code",
                    "info_column": "PFT combined",
                    "info_name": "PFT",
                }
            },
            "station_file": "DE_AgroScapeQuillow_station.csv",
            "start_year": 2000,
        },
        "31e67a47-5f15-40ad-9a72-f6f0ee4ecff6": {
            "name": "LTSER Zone Atelier Armorique",
            "variables": ["cover", "indices"],  # indices not considered yet
            "short_names": {"cover": "ZAA-C", "indices": "ZAA-I"},
            "file_names": {
                "cover": "FR_AtelierArmorique_data_cover.csv",
                "indices": "FR_AtelierArmorique_data_indices.csv",
            },
            "observation_columns": {
                "cover": "default",  # "TAXA" uses species codes
                "indices": {
                    "plot": "STATION_CODE",
                    "time": "TIME",
                    "species": "Dominant species",
                    "value": "",
                    "unit": "",
                },
                "management": None,
            },
            "pft_lookup_files": {
                "cover": "lat48.600000_lon-1.533330__PFT__reference.txt",
                "indices": "lat48.600000_lon-1.533330__PFT__data_indices.txt",
            },
            "pft_lookup_specs": {
                "cover": {
                    "key_column": "CODE",
                    "info_column": "PFT combined",
                    "info_name": "PFT",
                },
                "indices": "default",
            },
            "station_file": "FR_AtelierArmorique_station.csv",
            "start_year": 2015,
        },
        "324f92a3-5940-4790-9738-5aa21992511c": {
            "name": "Stubai (combination of Neustift meadows and Kaserstattalm)",
            "variables": ["cover"],
            "short_names": {"cover": "STB-C"},
            "file_names": {"cover": "AT_Stubai_data_abund.csv"},
            "observation_columns": {"cover": "default", "management": "default"},
            "pft_lookup_files": {
                "cover": "lat47.116700_lon11.300000__PFT__data_abund.txt"
            },
            "pft_lookup_specs": {"cover": "default"},
            "station_file": "AT_Stubai_station.csv",
            "start_year": 1995,
        },
        "3de1057c-a364-44f2-8a2a-350d21b58ea0": {
            "name": "Obergurgl",
            "variables": [
                "absolute_frequency"
            ],  # FREQ (pres/abs in 100 subplots of 1 m²)
            "short_names": {"absolute_frequency": "OGL-AF"},
            "file_names": {"absolute_frequency": "AT_Obergurgl_data.csv"},
            "observation_columns": {
                "absolute_frequency": "default",
                "management": None,
            },
            "pft_lookup_files": {
                "absolute_frequency": "lat46.867100_lon11.024900__PFT__data.txt"
            },
            "pft_lookup_specs": {"absolute_frequency": "default"},
            "station_file": "AT_Obergurgl_station.csv",
            "start_year": 2000,
        },
        "4ac03ec3-39d9-4ca1-a925-b6c1ae80c90d": {
            "name": "Hochschwab (AT-HSW) GLORIA",
            "variables": [
                "cover",
                "abundance_gloria_1_8",
            ],  # abundance categories 1-8, very rare to dominant, visual estimate
            "short_names": {"cover": "HSW-C", "abundance_gloria_1_8": "HSW-C18"},
            "file_names": {
                "cover": "AT_Hochschwab_data_cover.csv",
                "abundance_gloria_1_8": "AT_Hochschwab_data_abund.csv",
            },
            "observation_columns": {
                "cover": "default",
                "abundance_gloria_1_8": "default",
                "management": None,
            },
            "pft_lookup_files": {
                "cover": "lat47.622020_lon15.149292__PFT__data_cover.txt",
                "abundance_gloria_1_8": "lat47.622020_lon15.149292__PFT__data_abund.txt",
            },
            "pft_lookup_specs": {"cover": "default", "abundance_gloria_1_8": "default"},
            "station_file": "AT_Hochschwab_station.csv",
            "start_year": 1998,
        },
        "61c188bc-8915-4488-8d92-6d38483406c0": {
            "name": "Randu meadows",
            "variables": ["cover_braun_blanquet"],
            "short_names": {"cover_braun_blanquet": "RND-CBB"},
            "file_names": {"cover_braun_blanquet": "LV_RanduMeadows_data_abund.csv"},
            "observation_columns": {
                "cover_braun_blanquet": "default",
                "management": None,
            },
            "pft_lookup_files": {
                "cover_braun_blanquet": "lat57.814301_lon24.339609__PFT__data_abund.txt"
            },
            "pft_lookup_specs": {"cover_braun_blanquet": "default"},
            "station_file": "LV_RanduMeadows_station.csv",
            "start_year": 1996,
        },
        "66431807-ebf1-477f-aa52-3716542f3378": {
            "name": "LTSER Engure",
            "variables": ["cover"],
            "short_names": {"cover": "ENG-C"},
            "file_names": {"cover": "LV_Engure_data_cover.csv"},
            "observation_columns": {"cover": "default", "management": None},
            "pft_lookup_files": {
                "cover": "lat57.216700_lon23.135000__PFT__data_cover.txt"
            },
            "pft_lookup_specs": {"cover": "default"},
            "station_file": "LV_Engure_station.csv",
            "start_year": 1997,
        },
        "6ae2f712-9924-4d9c-b7e1-3ddffb30b8f1": {
            "name": "GLORIA Master Site Schrankogel (AT-SCH), Stubaier Alpen",
            "variables": ["cover"],
            "short_names": {"cover": "SCH-C"},
            "file_names": {"cover": "AT_Schrankogel_data_cover.csv"},
            "observation_columns": {"cover": "default", "management": None},
            "pft_lookup_files": {
                "cover": "lat47.041162_lon11.098057__PFT__data_cover.txt"
            },
            "pft_lookup_specs": {"cover": "default"},
            "station_file": "AT_Schrankogel_station.csv",
            "start_year": 1994,
        },
        "6b62feb2-61bf-47e1-b97f-0e909c408db8": {
            "name": "Montagna di Torricchio",
            "variables": ["cover_braun_blanquet"],
            "short_names": {"cover_braun_blanquet": "MDT-CBB"},
            "file_names": {
                "cover_braun_blanquet": "IT_MontagnadiTorricchio_data_abund.csv"
            },
            "observation_columns": {
                "cover_braun_blanquet": "default",
                "management": None,
            },
            "pft_lookup_files": {
                "cover_braun_blanquet": "lat42.961400_lon13.019200__PFT__reference.txt"
            },
            "pft_lookup_specs": {
                "cover_braun_blanquet": {
                    "key_column": "CODE",
                    "info_column": "PFT combined",
                    "info_name": "PFT",
                }
            },
            "station_file": "IT_MontagnadiTorricchio_station.csv",
            "start_year": 2006,
        },
        "829a2bcc-79d6-462f-ae2c-13653124359d": {
            "name": "Ordesa y Monte Perdido / Huesca ES",
            "variables": [
                "absolute_frequency"
            ],  # abundance number of contacts each 10 cm in 20 m transects ()
            "short_names": {"absolute_frequency": "OMP-AF"},
            "file_names": {
                "absolute_frequency": "ES_OrdesaYMontePerdido_data_freq.csv"
            },
            "observation_columns": {
                "absolute_frequency": "default",
                "management": None,
            },
            "pft_lookup_files": {
                "absolute_frequency": "lat42.650000_lon0.030000__PFT__data_freq.txt"
            },
            "pft_lookup_specs": {"absolute_frequency": "default"},
            "station_file": "ES_OrdesaYMontePerdido_station.csv",
            "start_year": 1993,
        },
        "9f9ba137-342d-4813-ae58-a60911c3abc1": {
            "name": "Rhine-Main-Observatory",
            "variables": ["cover_braun_blanquet"],
            "short_names": {"cover_braun_blanquet": "RMO-CBB"},
            "file_names": {
                "cover_braun_blanquet": "DE_RhineMainObservatory_data_abund_V3__2016_2020.csv"
            },
            "observation_columns": {
                "cover_braun_blanquet": {
                    "plot": "STATION_CODE",
                    "subplot": "SUBAREA",
                    "layer": "LAYER",
                    "time": "TIME",
                    "species": "TAXA",
                    "value": "VALUE",
                    "unit": "UNIT",
                },
                "management": None,
            },
            "pft_lookup_files": {
                # "cover_braun_blanquet": "lat50.267302_lon9.269139__PFT__abund_data.txt"
                "cover_braun_blanquet": "lat50.267302_lon9.269139__PFT__data_abund_V2.txt"
            },
            "pft_lookup_specs": {"cover_braun_blanquet": "default"},
            "station_file": "DE_RhineMainObservatory_station_reduced.csv",
            "start_year": 2010,
        },
        "a03ef869-aa6f-49cf-8e86-f791ee482ca9": {
            "name": "Torgnon grassland Tellinod (IT19 Aosta Valley)",
            "variables": ["frequency_daget_poissonet"],  # relative abundance?
            # According to the method of Daget and Poissonet (1971), the specific contributions
            # are derived as the quotient between the frequency of a species and the sum
            # of the frequencies of all species.
            "short_names": {"frequency_daget_poissonet": "TGT-F"},
            "file_names": {
                "frequency_daget_poissonet": "IT_TorgnonGrasslandTellinod_data_abund.csv"
            },
            "observation_columns": {
                "frequency_daget_poissonet": "default",
                "management": None,
            },
            "pft_lookup_files": {
                "frequency_daget_poissonet": "lat45.846063_lon7.579028__PFT__data_abund.txt"
            },
            "pft_lookup_specs": {"frequency_daget_poissonet": "default"},
            "station_file": "IT_TorgnonGrasslandTellinod_station.csv",
            "start_year": 2009,
        },
        "b356da08-15ac-42ad-ba71-aadb22845621": {
            "name": "Nørholm Hede",
            "variables": ["cover"],
            "short_names": {"cover": "NHH-C"},
            "file_names": {"cover": "DK_NorholmHede_data_cover.csv"},
            "observation_columns": {
                "cover": {
                    "plot": "STATION_CODE",
                    "subplot": "PLOT (10x10m)",
                    "layer": "LAYER",
                    "time": "TIME",
                    "species": "TAXA",
                    "value": "VALUE",
                    "unit": "UNIT",
                },
                "management": None,
            },
            "pft_lookup_files": {
                "cover": "lat55.680000_lon8.610000__PFT__data_cover.txt"
            },
            "pft_lookup_specs": {"cover": "default"},
            "station_file": "DK_NorholmHede_station.csv",
            "start_year": 1921,
        },
        "c0738b00-854c-418f-8d4f-69b03486e9fd": {
            "name": "Appennino centrale: Gran Sasso d'Italia",
            "variables": ["cover_braun_blanquet"],
            "short_names": {"cover_braun_blanquet": "GSI-CBB"},
            "file_names": {
                "cover_braun_blanquet": "IT_AppenninoCentrale_data_abund.csv"
            },
            "observation_columns": {
                "cover_braun_blanquet": "default",
                "management": None,
            },
            "pft_lookup_files": {
                "cover_braun_blanquet": "lat42.446250_lon13.554978__PFT__data_abund.txt"
            },
            "pft_lookup_specs": {"cover_braun_blanquet": "default"},
            "station_file": "IT_AppenninoCentrale_station.csv",
            "start_year": 1986,
        },
        "c85fc568-df0c-4cbc-bd1e-02606a36c2bb": {
            "name": "Appennino centro-meridionale: Majella-Matese",
            "variables": ["cover"],
            "short_names": {"cover": "MAM-C"},
            # "file_names": {"cover": "IT_AppenninoCentroMeridionale_data_cover.csv"},
            # "observation_columns": {"cover": "default"},
            "file_names": {
                "cover": "IT_AppenninoCentroMeridionale_data_cover__from_FEM_Revised.csv"
            },
            "observation_columns": {"cover": "default", "management": None},
            "pft_lookup_files": {
                "cover": "lat42.086116_lon14.085206__PFT__data_cover.txt"
            },
            "pft_lookup_specs": {"cover": "default"},
            "station_file": "IT_AppenninoCentroMeridionale_station.csv",
            "start_year": 2001,
        },
        "e13f1146-b97a-4bc5-9bc5-65322379a567": {
            "name": "Jalovecka dolina",
            "variables": [
                "cover_categories_1_9"
            ],  # unit of measure of density or biomass - semi-quantitative ordinal scale
            "short_names": {"cover_categories_1_9": "JAD-C19"},
            "file_names": {"cover_categories_1_9": "SK_JaloveckaDolina_data_cover.csv"},
            "observation_columns": {
                "cover_categories_1_9": "default",
                "management": None,
            },
            "pft_lookup_files": {
                "cover_categories_1_9": "lat49.217800_lon19.671900__PFT__data_cover.txt"
            },
            "pft_lookup_specs": {"cover_categories_1_9": "default"},
            "station_file": "SK_JaloveckaDolina_station.csv",
            "start_year": 2002,
        },
        # not eLTER plus
        "KUL-site": {
            "name": "KUL-site (KU Leuven)",
            "variables": ["cover"],  # "biomass"
            "short_names": {"cover": "KUL-C"},
            "file_names": {"cover": "BE_KUL-site_cover__from_VanMeerbeek_data.csv"},
            "observation_columns": {
                "cover": "default",
                "management": None,
            },  # TODO: handle specific management data
            "pft_lookup_files": {
                "cover": "lat51.000000_lon5.000000__PFT__cover__from_VanMeerbeek_data.txt"
            },
            "pft_lookup_specs": {"cover": "default"},
            "station_file": "BE_KUL-site_station_from_shape.csv",  # "BE_KUL-site_station_from_obs.csv"
            "start_year": 2009,
        },
        "4c8082f9-1ace-4970-a603-330544f22a23": {
            "name": "Certoryje-Vojsicke Louky meadows",
            "variables": ["cover"],
            "short_names": {"cover": "CVL-C"},
            "file_names": {
                "cover": "CZ_Certoryje-Vojsice_cover__from_regrassed_fields_Bile_Karpaty.csv"
            },
            "observation_columns": {
                "cover": "default",
                "management": None,
            },  # TODO: handle specific management data
            "pft_lookup_files": {
                "cover": "lat48.854200_lon17.426100__PFT__cover__from_regrassed_fields_Bile_Karpaty.txt"
            },
            "pft_lookup_specs": {"cover": "default"},
            "station_file": "CZ_Certoryje-Vojsice_station.csv",
            "start_year": 2009,
        },
        "4d7b73d7-62da-4d96-8cb3-3a9a744ae1f4": {
            "name": "DFG_Biodiversity_Exploratory_Schorfheide-Chorin",
            "variables": ["cover"],
            "short_names": {"cover": "BX-S-C"},
            "file_names": {
                "cover": "DE_BEXIS-site-SEG_data_cover__from_31973_5_Dataset.csv"
            },
            "observation_columns": {"cover": "default", "management": None},
            "pft_lookup_files": {
                "cover": "lat53.007100_lon13.769500__PFT__data_cover__from_31973_5_Dataset.txt"
            },
            "pft_lookup_specs": {"cover": "default"},
            "station_file": "DE_BEXIS-site-SEG_station.csv",
            "start_year": 2008,
        },
        "56c467e5-093f-4b60-b5cf-880490621e8d": {
            "name": "DFG_Biodiversity_Exploratory_Hainich-Duen",
            "variables": ["cover"],
            "short_names": {"cover": "BX-H-C"},
            "file_names": {
                "cover": "DE_BEXIS-site-HEG_data_cover__from_31973_5_Dataset.csv"
            },
            "observation_columns": {"cover": "default", "management": None},
            "pft_lookup_files": {
                "cover": "lat51.158000_lon10.476200__PFT__data_cover__from_31973_5_Dataset.txt"
            },
            "pft_lookup_specs": {"cover": "default"},
            "station_file": "DE_BEXIS-site-HEG_station.csv",
            "start_year": 2008,
        },
        "a51f9249-ddc8-4a90-95a8-c7bbebb35d29": {
            "name": "DFG_Biodiversity_Exploratory_SchwaebischeAlb",
            "variables": ["cover"],
            "short_names": {"cover": "BX-A-C"},
            "file_names": {
                "cover": "DE_BEXIS-site-AEG_data_cover__from_31973_5_Dataset.csv"
            },
            "observation_columns": {"cover": "default", "management": None},
            "pft_lookup_files": {
                "cover": "lat48.437400_lon9.389380__PFT__data_cover__from_31973_5_Dataset.txt"
            },
            "pft_lookup_specs": {"cover": "default"},
            "station_file": "DE_BEXIS-site-AEG_station.csv",
            "start_year": 2008,
        },
    }
)

# Define target variable names.
TARGET_VARIABLE_NAMES = MappingProxyType(
    {
        "cover_braun_blanquet": "Cover_from_braun_blanquet",
        "cover_categories_1_9": "Cover_from_categories_1_9",
        "abundance_gloria_1_8": "Cover_from_abundance_1_8",
        "frequency_daget_poissonet": "Frequency",
    }
)

# Define default observation column names for observation data.
DEFAULT_OBSERVATION_COLUMNS = MappingProxyType(
    {
        "plot": "STATION_CODE",
        # "subplot": "PLOT (10x10m)",
        # "event_id": "EVENT_ID",  # removed because only used in excluded observation data
        "layer": "LAYER",  # layer added to use only layer 'F', could be adjusted to use also other layers
        "time": "TIME",
        "species": "TAXA",
        "value": "VALUE",
        "unit": "UNIT",
    }
)

# default management columns, NOTE: no subplot or layer handling!
DEFAULT_MANAGEMENT_COLUMNS = MappingProxyType(
    {
        "plot": "STATION_CODE",
        "time": "TIME",
        "defoliation": "DEFOLIATION_TYPE",  # M: mowing, G: grazing, C: combined, A: abandoned, N: no
        "mowing": "ANNUAL_MOWINGS",  # mowing events per year
        "fertilization": "ANNUAL_FERTILIZATIONS",  # fertilization events per year
        "fertilization_organic": "ANNUAL_FERT_ORGANIC",  # fertilization with organic manure
        "fertilization_mineral": "ANNUAL_FERT_MINERAL",  # fertilization with mineral fertilizer
        "grazing": "ANNUAL_GRAZING",  # grazing months per year
    }
)

# Define default PFT lookup specifications.
DEFAULT_PFT_LOOKUP_SPECS = MappingProxyType(
    {
        "key_column": "Species Original",
        "info_column": "PFT combined",
        "info_name": "PFT",
    }
)

# Define mappings of categorical codes to cover values (in %)
BRAUN_BLANQUET_TO_COVER = MappingProxyType(
    {
        # "x", presence, but value unclear, occurs in RMO
        "r": 0.1,
        "R": 0.1,  # assuming same as "r", typo
        "+": 0.3,
        "1": 2.8,
        "2m": 4.5,
        "2a": 10,
        "2b": 20.5,
        "2": 15,  # ??  MDT: 5-25%, also used by: RMO (no info in method file), GSI ("Braun-Blanquet scale (1921), as modified by Pignatti (1959).")
        "3": 37.5,  # modified after expert consultations (was 38 or 38.5 before)
        "4": 62.5,
        "5": 87.5,
    }
)
ABUNDANCE_GLORIA_1_8_TO_COVER = MappingProxyType(
    {
        # Map abundance codes to cover values for "summit area sections" (SAS) as
        # defined in the GLORIA field manual (https://gloria.ac.at/downloads/Manual_5thEd_ENG.pdf, p.41f).
        # Uses interpretation of verbal descriptions, no clear quantitative values found for all codes!
        1: 0.5,  # r! (very rare): One or a few small individuals
        2: 1,  # r (rare): Some individuals at several locations that can hardly be overlooked in a careful observation;
        3: 3,  # rare-scattered
        4: 5,  # s (scattered): Widespread within the section, species can hardly be overlooked, but the presence is not obvious at first glance; individuals are not necessarily evenly dispersed over the entire summit area section
        5: 10,  # scattered-common
        6: 25,  # c (common): Occurring frequently and widespread within the section – presence is obvious at first glance, it covers, however, less than 50% of the SAS’s area;
        7: 50,  # common-dominant
        8: 75,  # d (dominant): Very abundant, making up a high proportion of the phytomass, often forming more or less patchy or dense vegetation layers; species covers more than 50% of the area of the SAS
    }
)
CATEGORIES_1_9_TO_COVER = MappingProxyType(
    {
        # Uses interpretation of verbal descriptions, no clear quantitative values found for codes 1-4!
        1: 0.5,  # very few individuals (1-2)
        2: 1,  # few individuals
        3: 2.5,  # cover < 5%, not abundant
        4: 4.5,  # cover < 5%, abundant
        5: 8.75,  # cover 5 - 12.5%
        6: 18.75,  # cover 12.5 - 25%
        7: 37.5,  # cover 25 - 50%
        8: 62.5,  # cover 50 - 75%
        9: 87.5,  # cover 75 - 100%
    }
)


def read_observation_data(
    file_name, *, new_file=None, header_lines=1, csv_delimiter=";"
):
    """
    Read observation data from a file, optionally save to new .txt file.

    Parameters:
        file_name (Path): Path to the file containing observation data.
        new_file (Path): Path to the new file to save observation data (default is None for not saving).
        header_lines (int): Number of header lines in the file (default is 1).
        csv_delimiter (str): Delimiter for .csv files (default is ";").

    Returns:
        list: List of lists with observation data.
    """
    file_extension = file_name.suffix.lower()
    logger.info(f"Reading observation data from '{file_name}' ...")

    if file_extension == ".csv":
        try:
            df = pd.read_csv(
                file_name,
                header=header_lines - 1,
                encoding="ISO-8859-1",  # encoding="utf-8-sig" would handle BOM, but cause errors with some other files
                delimiter=csv_delimiter,
            )
        except Exception as e:
            logger.error(f"Reading .csv file failed ({e}).")
            return []

        # Get column names and entries in one list, replace incorrectly handled byte order mark (BOM) if present ("\ufeff", converted to "ï»¿")
        df_column_names = [col.replace("ï»¿", "") for col in df.columns]

        if "STATION_CODE" in df_column_names:
            df["STATION_CODE"] = df["STATION_CODE"].fillna(
                "nan"
            )  # prevent NaN values in 'STATION_CODE' column

            # correct entries in 'STATION_CODE' column of form 'Rxx Q1', 'Rxx Q2' etc. to 'Rxx Q01', 'Rxx Q02'
            for index, station_code in enumerate(df["STATION_CODE"]):
                if station_code.startswith("R") and " " in station_code:
                    plot_name, subplot_name = station_code.split(" ", 1)

                    if (
                        subplot_name.startswith("Q")
                        and len(subplot_name) == 2
                        and subplot_name[1].isdigit()
                    ):
                        new_station_code = f"{plot_name} Q{int(subplot_name[1]):02}"
                        logger.info(
                            f"Adjusting plot name in row {index} from '{station_code}' to '{new_station_code}'."
                        )
                        df.at[index, "STATION_CODE"] = new_station_code

        observation_data = [df_column_names]
        observation_data.extend(df.values.tolist())

        if new_file:
            ut.list_to_file(observation_data, new_file)

        # Check for duplicates in observation data
        duplicate_rows = ut.count_duplicates(observation_data, key_column="all")

        if len(duplicate_rows) > 0:
            logger.warning(
                "Observation data have identical entries. Removing duplicates for subsequent processing.\n"
                "Duplicates:\n"
                + "\n".join(
                    [f"'{entry}' ({count})" for entry, count in duplicate_rows.items()]
                )
            )

            if new_file:
                ut.dict_to_file(
                    duplicate_rows,
                    new_file.with_name(
                        new_file.stem + "__duplicate_rows" + new_file.suffix
                    ),
                    column_names=observation_data[0] + ["#Duplicate rows"],
                )

            # Remove duplicates from observation data, keep first occurrence
            observation_data = ut.remove_duplicates(
                observation_data, duplicates=duplicate_rows, header_lines=1
            )

            if new_file:
                ut.list_to_file(
                    observation_data,
                    new_file.with_name(
                        new_file.stem + "__duplicate_rows_removed" + new_file.suffix
                    ),
                )

        # Check for entries that only differ in "SCIENTIFIC_NAME_GBIF" (if existing), all other columns are the same
        scientific_column = ut.find_column_index(
            observation_data, "SCIENTIFIC_NAME_GBIF", warn_not_found=False
        )

        # Try alternative column name "ScientificNameGBIF" if not found
        if scientific_column is None:
            scientific_column = ut.find_column_index(
                observation_data, "ScientificNameGBIF", warn_not_found=False
            )

        if scientific_column is not None:
            # Remove scientific name column from observation data
            observation_data = [
                row[:scientific_column] + row[scientific_column + 1 :]
                for row in observation_data
            ]

            duplicate_rows_except_scientific_name = ut.count_duplicates(
                observation_data, key_column="all"
            )

            if len(duplicate_rows_except_scientific_name) > 0:
                logger.warning(
                    "Observation data have entries that only differ in 'Scientific Name GBIF'.\n"
                    "Duplicates:\n"
                    + "\n".join(
                        [
                            f"'{entry}' ({count})"
                            for entry, count in duplicate_rows_except_scientific_name.items()
                        ]
                    )
                )

                if new_file:
                    ut.dict_to_file(
                        duplicate_rows_except_scientific_name,
                        new_file.with_name(
                            new_file.stem
                            + "__duplicate_rows_except_scientific_name"
                            + new_file.suffix
                        ),
                        column_names=observation_data[0] + ["#Duplicate rows"],
                    )

                # Remove duplicates from observation data, keep first occurrence
                observation_data = ut.remove_duplicates(
                    observation_data,
                    duplicates=duplicate_rows_except_scientific_name,
                    header_lines=1,
                )

        if new_file:
            ut.list_to_file(
                observation_data,
                new_file.with_name(
                    new_file.stem
                    + "__duplicate_rows_and_scientific_name_removed"
                    + new_file.suffix
                ),
            )

        # Check for entries that only differ in value, all other columns are the same
        value_column = ut.find_column_index(observation_data, "VALUE")

        if value_column is not None:
            duplicate_rows_except_value = ut.count_duplicates(
                observation_data,
                key_column="all",
                columns_to_ignore=[value_column],
            )

            if len(duplicate_rows_except_value) > 0:
                logger.warning(
                    "Observation data have entries that only differ in 'VALUE'.\n"
                    "Duplicates:\n"
                    + "\n".join(
                        [
                            f"'{entry}' ({count})"
                            for entry, count in duplicate_rows_except_value.items()
                        ]
                    )
                )

                if new_file:
                    ut.dict_to_file(
                        duplicate_rows_except_value,
                        new_file.with_name(
                            new_file.stem
                            + "__duplicate_rows_except_value"
                            + new_file.suffix
                        ),
                        column_names=observation_data[0][:value_column]
                        + observation_data[0][value_column + 1 :]
                        + ["#Duplicate rows"],
                    )

        return observation_data
    else:
        logger.error(f"File extension '{file_extension}' not supported. Skipping file.")
        return []


def process_single_plot_observation_data(
    plot_data,
    columns,
    plot_name,
    variable,
    pft_lookup,
    observation_pft,
    *,
    pfts=None,
    woody_maximum=5.0,
):
    """
    Process observation data for a single plot and variable, aggregating to PFTs.

    Parameters:
        plot_data (list): List of lists with observation data for the plot.
        columns (dict): Dictionary mapping required column names to their indices in plot_data.
        plot_name (str): Name of the plot.
        variable (str): Variable name of the observation data.
        pft_lookup (dict): Dictionary mapping species names to PFTs.
        observation_pft (pd.DataFrame): DataFrame to store processed PFT observation data.
        pfts (list): List of PFT names to aggregate to (default is None, which uses default PFTs).
        woody_maximum (float): Maximum allowed cover value for woody PFTs (default is 5.0).

    Returns:
        pd.DataFrame: Updated DataFrame with processed PFT observation data.
    """
    target_unit = get_target_unit(variable)

    # Use default PFTs if not specified
    if pfts is None:
        pfts = ["grass", "forb", "legume", "other", "not_assigned"]

    time_points = ut.get_unique_values_from_column(
        plot_data, columns["time"], header_lines=0
    )

    if "value" in columns:
        unit_check = None  # init unit_check, iteratively updated

        # Check for non-grass (and non-moss) maximum based on layer information
        if "layer" in columns:
            for time_point in time_points:
                time_data = ut.get_rows_with_value_in_column(
                    plot_data, columns["time"], time_point
                )
                time_data = ut.remove_duplicates(time_data)
                grass_layer_check = check_for_grass_layer(
                    time_data,
                    columns,
                    plot_name=plot_name,
                    time_point=time_point,
                    variable=variable,
                    woody_maximum=woody_maximum,
                )

                if grass_layer_check is not True:
                    break  # no need to check further time points if one failed
        else:
            logger.warning(
                f"No 'layer' column found in observation data for plot '{plot_name}'. "
                "Assuming all entries belong to grass layer. Using all data."
            )
            grass_layer_check = True

        # Check for woody maximum based on PFT information
        for time_point in time_points:
            time_data = ut.get_rows_with_value_in_column(
                plot_data, columns["time"], time_point
            )
            time_data = ut.remove_duplicates(time_data)
            woody_value_check = check_woody_values(
                time_data,
                columns,
                pft_lookup,
                plot_name=plot_name,
                time_point=time_point,
                variable=variable,
                woody_maximum=woody_maximum,
            )

            if woody_value_check is not True:
                break  # no need to check further time points if one failed

        for time_point in time_points:
            # Get rows from observation data for this plot and time point
            time_data = ut.get_rows_with_value_in_column(
                plot_data, columns["time"], time_point
            )

            if grass_layer_check is True and woody_value_check is True:
                # Remove remaining duplicates from retrieved observation data for this plot and time point
                duplicates = ut.count_duplicates(time_data, key_column="all")

                if len(duplicates) > 0:
                    logger.warning(
                        f"Duplicate species entries remain in retrieved observation data for plot '{plot_name}' "
                        f"at time '{time_point}'. Removing duplicates for subsequent processing.\n"
                        "Duplicate species entries:\n"
                        + "\n".join(
                            [
                                f"'{entry}' ({count})"
                                for entry, count in duplicates.items()
                            ]
                        )
                    )
                    time_data = ut.remove_duplicates(time_data, duplicates=duplicates)

                # Check for remaining duplicates that only differ in value, skip these from processing
                duplicates = ut.count_duplicates(
                    time_data,
                    key_column=columns["species"],
                    columns_to_ignore=[columns["value"]],
                )

                if len(duplicates) > 0:
                    logger.warning(
                        f"Duplicate species entries in plot '{plot_name}' at time '{time_point}'. Cannot process data from values. Skipping time point."
                        " Duplicate species entries:\n"
                        + "\n".join(
                            [
                                f"'{entry}' ({count})"
                                for entry, count in duplicates.items()
                            ]
                        )
                    )
                    new_row = {key: "" for key in observation_pft.columns}
                    new_row.update(
                        {
                            "plot": plot_name,
                            "time": time_point,
                            "invalid_observation": f"{len(duplicates)} non-unique species entries",
                        }
                    )
                else:
                    # Collect entries and add to PFTs
                    pft_values = {key: 0 for key in pfts}
                    pft_counts = {
                        key: 0
                        for key in [f"#{pft}" for pft in pfts] + ["#invalid_value"]
                    }

                    for entry in time_data:
                        species = (
                            entry[columns["species"]].rstrip()  # remove spaces at end
                            if isinstance(entry[columns["species"]], str)
                            else entry[columns["species"]]
                        )
                        pft = apft.reduce_pft_info(pft_lookup.get(species, "not found"))
                        unit = entry[columns["unit"]]
                        value = check_observation_value(
                            entry[columns["value"]],
                            variable,
                            unit=unit,
                            unit_check=unit_check,
                            plot_name=plot_name,
                            time_point=time_point,
                            species=species,
                        )

                        if pd.isna(value):
                            pft_counts["#invalid_value"] += 1
                        else:
                            pft_values[pft] += value
                            pft_counts[f"#{pft}"] += 1

                            if not pd.isna(unit):
                                unit_check = unit

                    # Add PFT values to observation data
                    new_row = {
                        "plot": plot_name,
                        "time": time_point,
                        "unit": target_unit,
                    }
                    new_row.update(pft_values)
                    new_row.update(pft_counts)
            else:
                # Grass layer and/or woody values check failed. Store error message string.
                if grass_layer_check is True:
                    check_message = woody_value_check
                elif woody_value_check is True:
                    check_message = grass_layer_check
                else:
                    check_message = f"{grass_layer_check}; {woody_value_check}"

                new_row = {key: "" for key in observation_pft.columns}
                new_row.update(
                    {
                        "plot": plot_name,
                        "time": time_point,
                        "invalid_observation": check_message,
                    }
                )

            # Add new row to observation_pft, can be empty if duplicates were found
            new_row_df = pd.DataFrame([new_row])
            observation_pft = pd.concat(
                [observation_pft, new_row_df], ignore_index=True
            )
    else:
        # No 'value' column found, add empty row for this plot and all time points
        for time_point in time_points:
            new_row = {key: "" for key in observation_pft.columns}
            new_row.update(
                {
                    "plot": plot_name,
                    "time": time_point,
                    "invalid_observation": "no 'value' entries",
                }
            )

            # Add new row to observation_pft, can be empty if duplicates were found
            new_row_df = pd.DataFrame([new_row])
            observation_pft = pd.concat(
                [observation_pft, new_row_df], ignore_index=True
            )

    return observation_pft


def check_for_grass_layer(
    data_snippet,
    columns,
    *,
    plot_name="not specified",
    time_point="not specified",
    variable="not specified",
    woody_maximum=0,
    grass_layer_names=["F", "COVE_F", "herb layer"],
    moss_layer_names=["moss layer"],  # "M", "COVE_M" ?
):
    """
    Check if data snippet includes only entries from the grass layer, or otherwise if sum of woody layer entries
        (i.e. ignoring grass and moss layers) exceeds maximum allowed value.

    Parameters:
        data_snippet (list): List of lists with observation data.
        columns (dict): Dictionary with column names for the data.
        plot_name (str): Plot name of the data (default is "not specified").
        time_point (str): Time point of the data (default is "not specified").
        variable (str): Variable name of the data (default is "not specified").
        woody_maximum (float): Maximum allowed value for woody layer entries (default is 0).
        grass_layer_names (list): List of valid grass layer names to look for (default is ["F", "COVE_F", "herb layer"]).
        moss_layer_names (list): List of valid moss layer names to look for (default is ["moss layer"]).

    Returns:
        bool or str: True if grass layer check is successful, otherwise a string with an error message.
    """
    if "layer" in columns:
        layer_entries = ut.get_unique_values_from_column(
            data_snippet, columns["layer"], header_lines=0
        )

        if len(layer_entries) == 1:
            if layer_entries[0] in grass_layer_names:
                # Only one valid layer entry found, use this layer
                return True
            elif layer_entries[0] == "nan":
                # No layer information, use this layer
                logger.warning(
                    f"Only 'nan' found as layer entry for plot '{plot_name}' at time '{time_point}'."
                    " Assuming all entries belong to grass layer, but this might not be the case."
                )
                return True
            else:
                # Only one non-grass layer entry found
                # NOTE: allowed, unless non-grass layer cover is too high, cf. below
                logger.warning(
                    f"Only '{layer_entries[0]}' found as layer entry for plot '{plot_name}' at time '{time_point}'."
                    " No grass layer available."
                )
        else:
            # Multiple layers found, inspect more thouroughly
            logger.warning(
                f"{len(layer_entries)} different layer entries ({layer_entries}) "
                f"found for plot '{plot_name}' at time '{time_point}'."
            )
            grass_layer_count = sum(
                1 for entry in layer_entries if entry in grass_layer_names
            )

            if grass_layer_count > 1:
                # Multiple valid grass layer entries found, skip data
                # NOTE: the case of zero grass layer entries is allowed, unless non-grass layer cover is too high, cf. below
                logger.warning(
                    f"{grass_layer_count} valid grass layer entries found ({layer_entries}) for plot '{plot_name}' at time '{time_point}'."
                    " Need exactly one valid grass layer entry to safely filter data. Skipping data."
                )

                return "Different grass layer entries."

        # Total value for all entries not belonging to grass layer or moss layer, i.e. woody layers
        woody_value = 0

        for i in range(len(data_snippet)):
            if data_snippet[i][columns["layer"]] not in [
                grass_layer_names + moss_layer_names
            ]:
                value = check_observation_value(
                    data_snippet[i][columns["value"]], variable
                )

                if value is not None and not pd.isna(value):
                    woody_value += value

        if woody_value > woody_maximum:
            logger.warning(
                f"Woody cover (neither grass nor moss layer) exceeds maximum "
                f"allowed ({woody_value:.2f} > {woody_maximum}) "
                f"for plot '{plot_name}' at time '{time_point}'. Skipping all data for this plot."
            )

            return (
                f"Woody layers cover too high ({woody_value:.2f} > {woody_maximum}%)."
            )
    else:
        logger.warning(
            "No 'layer' column found. Assuming all data belong to grass layer."
        )

    return True


def check_woody_values(
    data_snippet,
    columns,
    pft_lookup,
    *,
    plot_name="not specified",
    time_point="not specified",
    variable="not specified",
    woody_maximum=5.0,
):
    """
    Check woody values in the data snippet.

    Parameters:
        data_snippet (list): List of lists with observation data.
        columns (dict): Dictionary with column names for the data.
        pft_lookup (dict): Dictionary mapping species to their PFTs
        plot_name (str): Plot name of the data (default is "not specified").
        time_point (str): Time point of the data (default is "not specified").
        variable (str): Variable name of the data (default is "not specified").
        woody_maximum (float): Maximum allowed woody cover percentage (default is 5.0).

    Returns:
        bool or str: True if woody values are within limits, otherwise a string with an error message.
    """
    unit_check = None
    woody_value = 0

    for entry in data_snippet:
        species = (
            entry[columns["species"]].rstrip()  # remove spaces at end
            if isinstance(entry[columns["species"]], str)
            else entry[columns["species"]]
        )
        pft = apft.reduce_pft_info(
            pft_lookup.get(species, "not found"), separate_woody=True
        )

        if pft == "woody":
            unit = entry[columns["unit"]]
            value = check_observation_value(
                entry[columns["value"]],
                variable,
                unit=unit,
                unit_check=unit_check,
                plot_name=plot_name,
                time_point=time_point,
                species=species,
            )

            if not pd.isna(value):
                woody_value += value

                if not pd.isna(unit):
                    unit_check = unit

    if woody_value > woody_maximum:
        logger.warning(
            f"Woody PFT cover exceeds maximum allowed ({woody_value:.2f} > {woody_maximum}) "
            f"for plot '{plot_name}' at time '{time_point}'. Skipping all data for this plot."
        )

        return f"Woody PFT cover too high ({woody_value:.2f} > {woody_maximum}%)."

    return True


def process_observation_data(
    observation_data,
    variable,
    pft_lookup,
    coordinates_list,
    *,
    columns="default",
    new_file=None,
    management_columns=None,
):
    """
    Process observation data for a specific variable and map to PFTs.

    Parameters:
        observation_data (list): List of lists with observation data.
        variable (str): Observation variable name.
        pft_lookup (dict): Dictionary with species-PFT mapping.
        coordinates_list (list): List of dictionaries with plot names ('station_code') and their coordinates ('lat' and 'lon').
        columns (dict): Dictionary with column names for the observation data (default is 'default').
        new_file (Path): Path to the new file to save processed observation data (default is None for not saving).
        management_columns (dict): Dictionary with management-related column names, if applicable (default is None).

    Returns:
        DataFrame: Processed observation data mapped to PFTs or None if variable is not processed.
    """
    # Skip indices because conversion to PFT is not clear
    if variable in ["indices"]:
        logger.warning(
            f"'{variable}' data not fully processed because conversion to quantitative cover values is not possible."
        )

        return None
    elif variable in ["abundance_gloria_1_8", "absolute_frequency"]:
        logger.warning(
            f"'{variable}' data not fully processed because conversion to quantitative cover values is not recommended."
        )

        return None

    if new_file:
        target_folder = new_file.parent

    # Check if "time" column is present in observation data
    time_column = ut.find_column_index(observation_data, "TIME", warn_not_found=False)
    header_lines = 1

    if time_column is None:
        logger.warning(
            f"No 'TIME' column found in raw observation data for variable '{variable}'."
        )
    else:
        # Format entries in 'time' column using ut.format_datestring
        for index, entry in enumerate(observation_data[header_lines:]):
            observation_data[index + header_lines][time_column] = ut.format_datestring(
                entry[time_column]
            )

    if columns == "default":  # or columns is None:
        columns = DEFAULT_OBSERVATION_COLUMNS

    # Export management data if existing
    if management_columns is not None:
        if management_columns == "default":
            management_columns = DEFAULT_MANAGEMENT_COLUMNS

        management_data, management_columns_found = ut.get_list_of_columns(
            observation_data, management_columns.values()
        )
        management_columns_found = [
            key
            for key in management_columns
            if management_columns[key] in management_columns_found
        ]

        # Convert time entries in management data, keep only the year
        if "time" in management_columns_found:
            time_column = management_columns_found.index("time")

            for entry in management_data[header_lines:]:
                entry[time_column] = entry[time_column].split("-")[0]

        # Get unique management entries, remove header lines
        management_data = ut.remove_duplicates(management_data[header_lines:])

        # Add lat/lon to management data if "plot" column is present and coordinates are available
        if "plot" in management_columns_found:
            plot_column = management_columns_found.index("plot")
            management_columns_found = ["lat", "lon"] + management_columns_found

            for index, entry in enumerate(management_data):
                entry[plot_column] = (
                    str(entry[plot_column]).replace("/", "_").replace("?", "？")
                )

                for coordinates in coordinates_list:
                    if entry[plot_column] == coordinates.get("station_code"):
                        management_data[index] = [
                            round(coordinates.get("lat"), 6),
                            round(coordinates.get("lon"), 6),
                        ] + entry

                        break

        # Save management data to file
        ut.list_to_file(
            management_data,
            target_folder / f"{new_file.name.split('PFT')[0]}Management.csv",
            column_names=management_columns_found,
        )

    # Reduce observation data to selected columns, remap column names accordingly
    observation_data, columns_found = ut.get_list_of_columns(
        observation_data, columns.values()
    )

    # Get the keys from the columns dict for which the columns (i.e. the dict values) were found in the data
    columns_found = [key for key in columns if columns[key] in columns_found]

    # Create a new columns dict with the column names found as keys and the corresponding index in the reduced data as values
    columns = {key: index for index, key in enumerate(columns_found)}

    # Process observation data
    if "plot" in columns and "time" in columns:
        plot_names = ut.get_unique_values_from_column(
            observation_data, columns["plot"], header_lines=header_lines
        )

        pfts = ["grass", "forb", "legume", "other", "not_assigned"]
        observation_pft = pd.DataFrame(
            columns=["plot", "time"]
            + pfts
            + ["unit"]
            + [f"#{pft}" for pft in pfts]
            + ["#invalid_value"]
            + ["invalid_observation"]
        )

        for plot_name in plot_names:
            plot_data = ut.get_rows_with_value_in_column(
                observation_data, columns["plot"], plot_name
            )

            if "subplot" in columns:
                # Get unique subplots for this plot
                subplots = ut.get_unique_values_from_column(
                    plot_data, columns["subplot"], header_lines=0
                )

                for subplot in subplots:
                    subplot_data = ut.get_rows_with_value_in_column(
                        plot_data, columns["subplot"], subplot
                    )

                    if target_folder:
                        subplot_str = (
                            f"{subplot:02}"  # min 2 digits
                            if isinstance(subplot, int)
                            else str(subplot)
                        )

                        # Replace slashs in plot name with underscores and question marks with "full width question marks"
                        plot_name_str = (
                            str(plot_name).replace("/", "_").replace("?", "？")
                            + f"__{subplot_str}"
                        )
                        file_name = target_folder / f"{variable}__{plot_name_str}.txt"
                        ut.list_to_file(
                            subplot_data, file_name, column_names=columns.keys()
                        )

                    observation_pft = process_single_plot_observation_data(
                        subplot_data,
                        columns,
                        plot_name_str,
                        variable,
                        pft_lookup,
                        observation_pft,
                        pfts=pfts,
                    )

            else:
                if target_folder:
                    # Replace slashs in plot name with underscores and question marks with "full width question marks"
                    plot_name_str = str(plot_name).replace("/", "_").replace("?", "？")
                    file_name = target_folder / f"{variable}__{plot_name_str}.txt"
                    ut.list_to_file(plot_data, file_name, column_names=columns.keys())

                observation_pft = process_single_plot_observation_data(
                    plot_data,
                    columns,
                    plot_name_str,
                    variable,
                    pft_lookup,
                    observation_pft,
                )

        # Sort observation_pft by time column, and then by plot column
        observation_pft = observation_pft.sort_values(by=["plot", "time"])

        if new_file:
            observation_pft.to_csv(new_file, sep="\t", index=False)
            logger.info(f"Processed observation data written to file\n'{new_file}'.")

        return observation_pft
    else:
        logger.error(
            f"Column 'plot' and/or 'time' not found in observation data for '{variable}'. Skipping processing."
        )
        return None


def check_observation_value(
    value,
    variable,
    *,
    unit=None,
    unit_check=None,
    plot_name="not specified",
    time_point="not specified",
    species="not specified",
):
    """
    Check observation value for validity and return corrected value if necessary.

    Parameters:
        value (str): Observation value.
        variable (str): Observation variable name.
        unit (str): Observation unit (default is None).
        plot_name (str): Plot name (default is None).
        time_point (str): Time point (default is None).
        species (str): Species name (default is None).

    Returns:
        str: Corrected observation value or original value if valid.
    """
    value_in = value

    if variable == "cover":
        try:
            value = float(value_in)

            if value < 0 or value > 100:
                logger.error(
                    f"Invalid cover value '{value}' for species '{species}' "
                    f"in plot '{plot_name}' at time '{time_point}'. "
                    "Cover values must be between 0 and 100 %. Skipping invalid entry."
                )
                return None
        except ValueError:
            # Check for Braun-Blanquet code
            value = BRAUN_BLANQUET_TO_COVER.get(value_in)

            if value is not None:
                logger.warning(
                    f"Value '{value_in}' for '{variable}' of species '{species}' "
                    f"in plot '{plot_name}' at time '{time_point}' is not a number, "
                    f"but a Braun-Blanquet code. Mapped to cover value '{value}'."
                )
            else:
                logger.error(
                    f"Value '{value_in}' for '{variable}' of species '{species}' "
                    f"in plot '{plot_name}' at time '{time_point}' is not a number "
                    "(and not a Braun-Blanquet code). Skipping invalid entry."
                )
                return None

        if not pd.isna(unit) and unit not in ["%", "percent", "abundance"]:
            logger.warning(
                f"Invalid unit '{unit}' for '{variable}' of species '{species}' "
                f"in plot '{plot_name}' at time '{time_point}'. Unit should be '%'."
            )

    elif variable == "cover_braun_blanquet":
        value = BRAUN_BLANQUET_TO_COVER.get(value_in)

        if value is None:
            logger.error(
                f"Invalid Braun-Blanquet code '{value_in}' for species '{species}' "
                f"in plot '{plot_name}' at time '{time_point}'. Skipping invalid entry."
            )
            return None
        else:
            if not pd.isna(unit) and unit.lower() not in [
                "braun_blanquet",
                "code",
                "dimless",
                "dimles",  # account for typo in raw data
            ]:
                logger.warning(
                    f"Invalid unit '{unit}' for '{variable}' of species '{species}' "
                    f"in plot '{plot_name}' at time '{time_point}'."
                )

    elif variable == "cover_categories_1_9":
        value = CATEGORIES_1_9_TO_COVER.get(value_in)

        if value is None:
            logger.error(
                f"Invalid categories 1-9 code '{value_in}' for species '{species}' "
                f"in plot '{plot_name}' at time '{time_point}'. Skipping invalid entry."
            )
            return None
        else:
            if not pd.isna(unit) and unit.lower() != "dimless":
                logger.warning(
                    f"Invalid unit '{unit}' for '{variable}' of species '{species}' "
                    f"in plot '{plot_name}' at time '{time_point}'. Unit should be 'dimless'."
                )

    elif variable == "abundance_gloria_1_8":
        value = ABUNDANCE_GLORIA_1_8_TO_COVER.get(value_in)

        if value is None:
            logger.error(
                f"Invalid Gloria abundance code '{value}' for species '{species}' "
                f"in plot '{plot_name}' at time '{time_point}'. Skipping invalid entry."
            )
            return None
        else:
            if not pd.isna(unit) and unit.lower() not in ["category"]:
                logger.warning(
                    f"Invalid unit '{unit}' for '{variable}' of species '{species}' "
                    f"in plot '{plot_name}' at time '{time_point}'. Unit should be 'category'."
                )

    elif variable == "frequency_daget_poissonet":
        try:
            value = float(value_in)

            if value < 0 or value > 100:
                logger.error(
                    f"Invalid frequency value '{value}' for species '{species}' "
                    f"in plot '{plot_name}' at time '{time_point}'. "
                    "Frequency values must be between 0 and 100 %. Skipping invalid entry."
                )
                return None
        except ValueError:
            logger.error(
                f"Invalid frequency value '{value_in}' for species '{species}' "
                f"in plot '{plot_name}' at time '{time_point}'. Skipping invalid entry."
            )
            return None

    else:
        logger.error(
            f"Variable '{variable}' not supported. Skipping observation value {value_in} "
            f"for species '{species}' in plot '{plot_name}' at time '{time_point}'."
        )
        return None

    if unit is not None and unit_check is not None and unit != unit_check:
        logger.warning(
            f"Unit mismatch for '{variable}' of species '{species}' in plot "
            f"'{plot_name}' at time '{time_point}': {unit_check} vs. {unit}."
        )

    return value


def get_observation_summary(observation_pft, *, new_file=None):
    """
    Get summary statistics from processed observation data.

    Parameters:
        observation_pft (DataFrame): Processed observation data.

    Returns:
        dict: Dictionary with summary statistics from processed observation data.
    """
    pfts = ["grass", "forb", "legume", "other", "not_assigned"]

    # Fill missing values in pft entries with nan to allow calculations
    columns_to_convert = pfts + [f"#{pft}" for pft in pfts] + ["#invalid_value"]
    observation_pft[columns_to_convert] = observation_pft[columns_to_convert].apply(
        pd.to_numeric, errors="coerce"
    )

    # General observation counts
    plot_count = observation_pft["plot"].nunique()  # count of unique plots
    time_points_count = observation_pft["time"].nunique()  # count of unique time points
    observation_count = observation_pft.shape[0]  # total count of observations
    mean_time_points_per_plot = observation_count / plot_count

    # Count invalid time points, and invalid species entries (due to invalid values)
    observations_invalid = observation_pft["invalid_observation"].notna().sum()
    entries_invalid = observation_pft["#invalid_value"].sum()

    # Mean species counts and proportions (omitting invalid values)
    species_count_per_observation = observation_pft[[f"#{pft}" for pft in pfts]].sum(
        axis=1, skipna=False
    )
    mean_species_count = species_count_per_observation.mean()
    min_species_count = species_count_per_observation.min()
    max_species_count = species_count_per_observation.max()

    mean_species_proportion_not_assigned = (
        observation_pft["#not_assigned"] / species_count_per_observation
    ).mean()
    mean_species_proportion_assigned = 1 - mean_species_proportion_not_assigned

    # Mean proportion of the three "grassland" PFTs (grass, forb, legume) per observation
    mean_species_proportion_grassland_pft = (
        observation_pft[[f"#{pft}" for pft in pfts[:3]]].sum(axis=1)
        / species_count_per_observation
    ).mean()

    observation_summary = {
        "plot_count": plot_count,
        "time_points_count": time_points_count,
        "observation_count": observation_count,
        "invalid_observations_omitted": observations_invalid,
        "proportion_invalid_observations": observations_invalid / observation_count,
        "mean_time_points_per_plot": mean_time_points_per_plot,
        "mean_species_count": mean_species_count,
        "min_species_count": min_species_count,
        "max_species_count": max_species_count,
        "invalid_species_entries_omitted": entries_invalid,
        "mean_species_proportion_not_assigned": mean_species_proportion_not_assigned,
        "mean_species_proportion_assigned": mean_species_proportion_assigned,
        "mean_species_proportion_grassland_pft": mean_species_proportion_grassland_pft,
    }

    # Mean counts of all single PFTs
    for pft in pfts:
        observation_summary[f"mean_species_count_{pft}"] = observation_pft[
            f"#{pft}"
        ].mean()

    # Mean values of observation data
    total_value_per_observation = observation_pft[pfts].sum(axis=1, skipna=False)
    observation_summary["mean_total_value"] = total_value_per_observation.mean()
    observation_summary["min_total_value"] = total_value_per_observation.min()
    observation_summary["max_total_value"] = total_value_per_observation.max()

    # Absolute and relative mean values of all single PFTs
    for pft in pfts:
        observation_summary[f"mean_value_{pft}"] = observation_pft[pft].mean()
        observation_summary[f"mean_relative_value_{pft}"] = (
            observation_pft[pft] / total_value_per_observation
        ).mean()

    if new_file:
        ut.dict_to_file(observation_summary, new_file, column_names=None)

    return observation_summary


def get_target_unit(variable):
    if variable in [
        "cover",
        "cover_braun_blanquet",
        "cover_categories_1_9",
        "abundance_gloria_1_8",
        "frequency_daget_poissonet",
    ]:
        return "%"
    else:
        return ""


def get_observations_from_files(
    location,
    observation_data_specs,
    source_folder,
    coordinates_list,
    *,
    target_folder=None,
    target_suffix=".txt",
):
    """
    Get observation data from files and save to .txt files in location subfolder.

    Parameters:
        location (dict): Dictionary with 'name', 'deims_id', 'lat' and 'lon' keys.
        observation_data_specs (dict): Dictionary with 'name' and 'file_names' keys.
        source_folder (Path): Path to the folder containing observation data files.
        coordinates_list (list): List of dictionaries with plot names ('station_code') and their coordinates ('lat' and 'lon').
        target_folder (Path): Path to the folder to save processed observation data (default is None).
        target_suffix (str): Suffix for target files (default is '.txt').

    Returns:
        dict: Dictionary with summary statistics from processed observation data.
    """
    if location["name"] == observation_data_specs["name"]:
        if target_folder is None:
            target_folder = source_folder

        target_subfolder = target_folder / "Observations"
        target_subfolder.mkdir(parents=True, exist_ok=True)

        location_summary = {
            "site_id": location["deims_id"],
            "site_name": location["name"],
            "lat_deims": location["lat"],
            "lon_deims": location["lon"],
        }
        coordinates_found = []

        for variable in observation_data_specs["variables"]:
            file_name = observation_data_specs["file_names"][variable]

            if (source_folder / file_name).exists():
                # Read observation data from raw file and save to new .txt file
                observation_source = ut.get_source_from_elter_data_file_name(file_name)
                target_file = (
                    target_subfolder
                    / f"{location['formatted_lat']}_{location['formatted_lon']}__Observation__Raw__{observation_source}{target_suffix}"
                )
                observation_data = read_observation_data(
                    source_folder / file_name, new_file=target_file
                )

                # Read PFT lookup data from PFT mapping file
                lookup_folder = target_folder / "PFT_Mapping"
                lookup_file = (
                    lookup_folder / observation_data_specs["pft_lookup_files"][variable]
                )
                lookup_specs = observation_data_specs["pft_lookup_specs"][variable]

                if lookup_specs == "default" or lookup_specs is None:
                    lookup_specs = DEFAULT_PFT_LOOKUP_SPECS

                pft_lookup = apft.read_info_dict(
                    lookup_file,
                    lookup_specs["info_name"],
                    key_column=lookup_specs["key_column"],
                    info_column=lookup_specs["info_column"],
                )

                # Process raw observation data
                target_variable = TARGET_VARIABLE_NAMES.get(
                    variable, variable.capitalize()
                )
                target_file = (
                    target_subfolder
                    / f"{location['formatted_lat']}_{location['formatted_lon']}__Observation__PFT__{target_variable}.txt"
                )
                observation_pft = process_observation_data(
                    observation_data,
                    variable,
                    pft_lookup,
                    coordinates_list,
                    columns=observation_data_specs["observation_columns"][variable],
                    new_file=target_file,
                    management_columns=observation_data_specs["observation_columns"][
                        "management"
                    ],
                )

                # Get summary for processed observation data
                if observation_pft is not None:
                    target_file = target_file.with_name(
                        target_file.stem + "__summary" + target_file.suffix
                    )
                    location_summary[variable] = {
                        "target_variable": target_variable,
                        "source": observation_source,
                    }
                    observation_summary = get_observation_summary(
                        observation_pft, new_file=target_file
                    )
                    location_summary[variable].update(observation_summary)

                    # Keep only entries from coordinates_list that occur in observation_pft
                    # NOTE: entries with excluded observation data will remain, as they have an entry in observation_pft

                    for plot_name in observation_pft["plot"].values:
                        for entry in coordinates_list:
                            if entry["station_code"] == plot_name:
                                coordinates_found.append(entry)
                                coordinates_list.remove(entry)
                                break

                    if coordinates_list != []:
                        logger.warning(
                            f"{len(coordinates_list)} plots were not found in processed observation data "
                            f"for site {location['name']} and variable '{variable}': "
                            f"{[entry['station_code'] for entry in coordinates_list]}."
                        )

                else:
                    logger.warning(
                        f"No processed observation data for site {location['name']} and variable '{variable}'."
                    )

        return location_summary, coordinates_found
    else:
        # Stop with error if location names do not match (apparently can be changed in DEIMS package)
        try:
            raise ValueError(
                f"Location names for DEIMS.iD '{location['deims_id']}' do not match "
                f"('{location['name']}' vs.'{observation_data_specs['name']}'). "
                "Cannot process observation data."
            )
        except ValueError as e:
            logger.error(e)
            raise


def prep_observation_data(
    deims_id, source_folder, *, target_folder=None, target_suffix=".txt"
):
    """
    Find and process observation data for a site based on DEIMS ID.

    Parameters:
        deims_id (str): DEIMS ID of the site.
        source_folder (Path): Path to the folder containing observation data files.
        target_folder (Path): Path to the folder to save processed observation data (default is None).
        target_suffix (str): Suffix for target files (default is '.txt').

    Returns:
        dict: Dictionary with summary statistics from processed observation data, if found.
    """
    observation_data_specs = OBSERVATION_DATA_SPECS_PER_SITE.get(deims_id)

    if observation_data_specs is None:
        logger.error(
            f"DEIMS ID '{deims_id}' not found in observation data specifications. Skipping site."
        )
        return

    if target_folder is None:
        target_folder = source_folder

    location = ut.get_deims_coordinates(deims_id)

    if location["found"]:
        source_subfolder = source_folder / location["deims_id"]
        target_subfolder = target_folder / location["deims_id"]
        location["formatted_lat"] = f"lat{location['lat']:.6f}"
        location["formatted_lon"] = f"lon{location['lon']:.6f}"

        # Create coordinates file
        station_file = (
            source_folder
            / location["deims_id"]
            / observation_data_specs["station_file"]
        )
        coordinates_list = ut.get_plot_locations_from_csv(
            station_file, merge_same_locations=False
        )

        # Get observation data from files
        location_summary, coordinates_list = get_observations_from_files(
            location,
            observation_data_specs,
            source_subfolder,
            coordinates_list,
            target_folder=target_subfolder,
            target_suffix=target_suffix,
        )

        # Save coordinates of plots used in observation data to file
        if coordinates_list != []:
            coordinates_file = (
                target_subfolder
                / "Observations"
                / f"{location['formatted_lat']}_{location['formatted_lon']}__Observation__Plot_Coordinates.txt"
            )
            ut.list_to_file(
                coordinates_list,
                coordinates_file,
                column_names=["site_code", "station_code", "lat", "lon", "altitude"],
            )

        return location_summary
    else:
        logger.error(f"Coordinates not found for DEIMS ID '{deims_id}'. Skipping site.")
        return


def observation_summaries_to_list(observation_summaries, *, new_file=None):
    """
    Convert observation summaries to a list and save to a .txt file.

    Parameters:
        observation_summaries (dict): Dictionary with observation summaries.
        new_file (Path): Path to the new file to save observation summaries.
    """
    observation_summaries_list = []
    column_names = None
    site_keys = ["site_id", "site_name", "lat_deims", "lon_deims"]
    var_keys = ["variable", "short_name"]

    for site_summary in observation_summaries.values():
        for key, variable_summary in site_summary.items():
            if key not in site_keys and isinstance(variable_summary, dict):
                # Add dict values from variable_summary to list
                short_name = (
                    OBSERVATION_DATA_SPECS_PER_SITE.get(site_summary["site_id"], {})
                    .get("short_names", {})
                    .get(key, "n.f.")
                )
                row = [
                    site_summary["site_id"],
                    site_summary["site_name"],
                    site_summary["lat_deims"],
                    site_summary["lon_deims"],
                    key,
                    short_name,
                ] + list(variable_summary.values())
                observation_summaries_list.append(row)

                if column_names is None:
                    column_names = list(variable_summary.keys())
                elif column_names != list(variable_summary.keys()):
                    logger.warning(
                        f"Column names for '{key}' do not match previous entries. Keeping column names from first entry."
                    )

    if new_file:
        ut.list_to_file(
            observation_summaries_list,
            new_file,
            column_names=site_keys + var_keys + column_names,
        )


def prep_observation_data_for_sites(
    site_ids=None, source_folder=None, target_folder=None, target_suffix=".txt"
):
    """
    Prepare observation data for selected sites.

    Parameters:
        site_ids (list): List of DEIMS IDs of the sites.
        source_folder (Path): Path to the folder containing observation data files.
        target_folder (Path): Path to the folder to save processed observation data.
    """
    # Examples if not specified otherwise in function call
    if site_ids is None:
        # Specify selected site IDs, these need to be in species_data_specs
        site_ids = [
            "11696de6-0ab9-4c94-a06b-7ce40f56c964",  # IT25 - Val Mazia-Matschertal
            # "270a41c4-33a8-4da6-9258-2ab10916f262",  # AgroScapeLab Quillow (ZALF)
            "31e67a47-5f15-40ad-9a72-f6f0ee4ecff6",  # LTSER Zone Atelier Armorique
            "324f92a3-5940-4790-9738-5aa21992511c",  # Stubai
            # "3de1057c-a364-44f2-8a2a-350d21b58ea0",  # Obergurgl
            # "4ac03ec3-39d9-4ca1-a925-b6c1ae80c90d",  # Hochschwab (AT-HSW) GLORIA
            "61c188bc-8915-4488-8d92-6d38483406c0",  # Randu meadows
            "66431807-ebf1-477f-aa52-3716542f3378",  # LTSER Engure
            "6ae2f712-9924-4d9c-b7e1-3ddffb30b8f1",  # GLORIA Master Site Schrankogel (AT-SCH), Stubaier Alpen
            # "6b62feb2-61bf-47e1-b97f-0e909c408db8",  # Montagna di Torricchio
            # "829a2bcc-79d6-462f-ae2c-13653124359d",  # Ordesa y Monte Perdido / Huesca ES
            "9f9ba137-342d-4813-ae58-a60911c3abc1",  # Rhine-Main-Observatory
            "a03ef869-aa6f-49cf-8e86-f791ee482ca9",  # Torgnon grassland Tellinod (IT19 Aosta Valley)
            "b356da08-15ac-42ad-ba71-aadb22845621",  # Nørholm Hede
            "c0738b00-854c-418f-8d4f-69b03486e9fd",  # Appennino centrale: Gran Sasso d'Italia
            "c85fc568-df0c-4cbc-bd1e-02606a36c2bb",  # Appennino centro-meridionale: Majella-Matese
            "e13f1146-b97a-4bc5-9bc5-65322379a567",  # Jalovecka dolina
            # not eLTER plus
            "KUL-site",  # KU Leuven, Belgium
            "4c8082f9-1ace-4970-a603-330544f22a23",  # Certoryje-Vojsicke Louky meadows
            "4d7b73d7-62da-4d96-8cb3-3a9a744ae1f4",  # BEXIS-site-SEG
            "56c467e5-093f-4b60-b5cf-880490621e8d",  # BEXIS-site-HEG
            "a51f9249-ddc8-4a90-95a8-c7bbebb35d29",  # BEXIS-site-AEG
        ]

    if source_folder is None:
        dotenv_config = dotenv_values(".env")
        source_folder = Path(dotenv_config["ELTER_DATA_PROCESSED"])

    if target_folder is None:
        target_folder = Path.cwd() / "grasslandSites"

    site_observation_summary = {}

    for deims_id in site_ids:
        site_observation_summary[deims_id] = prep_observation_data(
            deims_id,
            source_folder,
            target_folder=target_folder,
            target_suffix=target_suffix,
        )

    summary_file = target_folder / "Observation_Summaries.txt"
    observation_summaries_to_list(site_observation_summary, new_file=summary_file)


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
        type=ut.parse_locations,
        help="List of location dictionaries containing coordinates ('lat', 'lon') or DEIMS IDs ('deims_id')",
    )
    parser.add_argument(
        "--source_folder",
        type=Path,
        help="Path to the folder containing species data files",
    )
    parser.add_argument(
        "--target_folder",
        type=Path,
        help="Path to the folder to save processed observation data",
    )
    parser.add_argument(
        "--target_suffix",
        type=str,
        default=".csv",
        choices=[".txt", ".csv"],
        help="Suffix for raw and cleaned from duplicates data files ('.txt' or '.csv').",
    )
    args = parser.parse_args()

    prep_observation_data_for_sites(
        site_ids=args.locations,
        source_folder=args.source_folder,
        target_folder=args.target_folder,
        target_suffix=args.target_suffix,
    )


# Execute main function when the script is run directly
if __name__ == "__main__":
    main()
