"""
Module Name: elter_site_specs.py
Description: Define constants for eLTER site IDs used in UC Grassland project.

Developed by Thomas Banitz (UFZ) with contributions by Franziska Taubert (UFZ).

Copyright (C) 2025
- Helmholtz Centre for Environmental Research GmbH - UFZ, Germany

Licensed under the EUPL, Version 1.2 or - as soon they will be approved
by the European Commission - subsequent versions of the EUPL (the "Licence").
You may not use this work except in compliance with the Licence.

You may obtain a copy of the Licence at:
https://joinup.ec.europa.eu/software/page/eupl
"""

from types import MappingProxyType

ELTER_SITE_IDS = [
    "11696de6-0ab9-4c94-a06b-7ce40f56c964",  # IT25 - Val Mazia-Matschertal
    # "270a41c4-33a8-4da6-9258-2ab10916f262",  # AgroScapeLab Quillow (ZALF)
    "31e67a47-5f15-40ad-9a72-f6f0ee4ecff6",  # LTSER Zone Atelier Armorique
    "324f92a3-5940-4790-9738-5aa21992511c",  # Stubai
    # "3de1057c-a364-44f2-8a2a-350d21b58ea0",  # Obergurgl
    "4ac03ec3-39d9-4ca1-a925-b6c1ae80c90d",  # Hochschwab (AT-HSW) GLORIA
    "61c188bc-8915-4488-8d92-6d38483406c0",  # Randu meadows
    "66431807-ebf1-477f-aa52-3716542f3378",  # LTSER Engure
    "6ae2f712-9924-4d9c-b7e1-3ddffb30b8f1",  # GLORIA Master Site Schrankogel (AT-SCH), Stubaier Alpen
    "6b62feb2-61bf-47e1-b97f-0e909c408db8",  # Montagna di Torricchio
    # "829a2bcc-79d6-462f-ae2c-13653124359d",  # Ordesa y Monte Perdido / Huesca ES
    "9f9ba137-342d-4813-ae58-a60911c3abc1",  # Rhine-Main-Observatory
    # "a03ef869-aa6f-49cf-8e86-f791ee482ca9",  # Torgnon grassland Tellinod (IT19 Aosta Valley)
    # "b356da08-15ac-42ad-ba71-aadb22845621",  # Nørholm Hede
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

NON_DEIMS_LOCATIONS = MappingProxyType(
    {
        # rough means of coordinates of all plots for non-DEIMS sites
        "KUL-site": {
            "lat": 51.0,
            "lon": 5.0,
            "deims_id": "KUL-site",
            "found": True,
            "name": "KUL-site (KU Leuven)",
        },
    }
)

KNOWN_DEIMS_LOCATIONS = MappingProxyType(
    {
        "11696de6-0ab9-4c94-a06b-7ce40f56c964": {
            "lat": 46.692800,
            "lon": 10.615700,
            "deims_id": "11696de6-0ab9-4c94-a06b-7ce40f56c964",
            "found": True,
            "name": "IT25 - Val Mazia-Matschertal",
        },
        "31e67a47-5f15-40ad-9a72-f6f0ee4ecff6": {
            "lat": 48.600000,
            "lon": -1.533330,
            "deims_id": "31e67a47-5f15-40ad-9a72-f6f0ee4ecff6",
            "found": True,
            "name": "LTSER Zone Atelier Armorique",
        },
        "324f92a3-5940-4790-9738-5aa21992511c": {
            "lat": 47.116700,
            "lon": 11.300000,
            "deims_id": "324f92a3-5940-4790-9738-5aa21992511c",
            "found": True,
            "name": "Stubai (combination of Neustift meadows and Kaserstattalm)",
        },
        "4ac03ec3-39d9-4ca1-a925-b6c1ae80c90d": {
            "lat": 47.622020,
            "lon": 15.149292,
            "deims_id": "4ac03ec3-39d9-4ca1-a925-b6c1ae80c90d",
            "found": True,
            "name": "Hochschwab (AT-HSW) GLORIA",
        },
        "61c188bc-8915-4488-8d92-6d38483406c0": {
            "lat": 57.814301,
            "lon": 24.339609,
            "deims_id": "61c188bc-8915-4488-8d92-6d38483406c0",
            "found": True,
            "name": "Randu meadows",
        },
        "66431807-ebf1-477f-aa52-3716542f3378": {
            "lat": 57.216700,
            "lon": 23.135000,
            "deims_id": "66431807-ebf1-477f-aa52-3716542f3378",
            "found": True,
            "name": "LTSER Engure",
        },
        "6ae2f712-9924-4d9c-b7e1-3ddffb30b8f1": {
            "lat": 47.041162,
            "lon": 11.098057,
            "deims_id": "6ae2f712-9924-4d9c-b7e1-3ddffb30b8f1",
            "found": True,
            "name": "GLORIA Master Site Schrankogel (AT-SCH), Stubaier Alpen",
        },
        "6b62feb2-61bf-47e1-b97f-0e909c408db8": {
            "lat": 42.9614,
            "lon": 13.0192,
            "deims_id": "6b62feb2-61bf-47e1-b97f-0e909c408db8",
            "found": True,
            "name": "Montagna di Torricchio",
        },
        "9f9ba137-342d-4813-ae58-a60911c3abc1": {
            "lat": 50.267302,
            "lon": 9.269139,
            "deims_id": "9f9ba137-342d-4813-ae58-a60911c3abc1",
            "found": True,
            "name": "Rhine-Main-Observatory",
        },
        "a03ef869-aa6f-49cf-8e86-f791ee482ca9": {
            "lat": 45.846063,
            "lon": 7.579028,
            "deims_id": "a03ef869-aa6f-49cf-8e86-f791ee482ca9",
            "found": True,
            "name": "Torgnon grassland Tellinod (IT19 Aosta Valley)",
        },
        "c0738b00-854c-418f-8d4f-69b03486e9fd": {
            "lat": 42.44625,
            "lon": 13.554978,
            "deims_id": "c0738b00-854c-418f-8d4f-69b03486e9fd",
            "found": True,
            "name": "Appennino centrale: Gran Sasso d'Italia",
        },
        "c85fc568-df0c-4cbc-bd1e-02606a36c2bb": {
            "lat": 42.086116,
            "lon": 14.085206,
            "deims_id": "c85fc568-df0c-4cbc-bd1e-02606a36c2bb",
            "found": True,
            "name": "Appennino centro-meridionale: Majella-Matese",
        },
        "e13f1146-b97a-4bc5-9bc5-65322379a567": {
            "lat": 49.2178,
            "lon": 19.6719,
            "deims_id": "e13f1146-b97a-4bc5-9bc5-65322379a567",
            "found": True,
            "name": "Jalovecka dolina",
        },
        "4c8082f9-1ace-4970-a603-330544f22a23": {
            "lat": 48.8542,
            "lon": 17.4261,
            "deims_id": "4c8082f9-1ace-4970-a603-330544f22a23",
            "found": True,
            "name": "Certoryje-Vojsicke Louky meadows",
        },
        "4d7b73d7-62da-4d96-8cb3-3a9a744ae1f4": {
            "lat": 53.0071,
            "lon": 13.7695,
            "deims_id": "4d7b73d7-62da-4d96-8cb3-3a9a744ae1f4",
            "found": True,
            "name": "DFG_Biodiversity_Exploratory_Schorfheide-Chorin",
        },
        "56c467e5-093f-4b60-b5cf-880490621e8d": {
            "lat": 51.158,
            "lon": 10.4762,
            "deims_id": "56c467e5-093f-4b60-b5cf-880490621e8d",
            "found": True,
            "name": "DFG_Biodiversity_Exploratory_Hainich-Duen",
        },
        "a51f9249-ddc8-4a90-95a8-c7bbebb35d29": {
            "lat": 48.4374,
            "lon": 9.38938,
            "deims_id": "a51f9249-ddc8-4a90-95a8-c7bbebb35d29",
            "found": True,
            "name": "DFG_Biodiversity_Exploratory_SchwaebischeAlb",
        },
    }
)

PFT_COMBINED_COLUMN_NAME = "PFT combined"

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
        # "270a41c4-33a8-4da6-9258-2ab10916f262": {
        #     "name": "AgroScapeLab Quillow (ZALF)",
        #     "variables": ["cover"],
        #     "short_names": {"cover": "ASQ-C"},
        #     # "file_names": {"cover": "DE_AgroScapeQuillow_data_cover.csv"},
        #     # "observation_columns": {"cover": "default"},
        #     "file_names": {
        #         "cover": "DE_AgroScapeQuillow_data_cover__from_SpeciesFiles.csv"
        #     },
        #     "observation_columns": {
        #         "cover": {
        #             "plot": "STATION_CODE",
        #             "subplot": "REPLICATION",
        #             "time": "TIME",
        #             "species": "TAXA",
        #             "value": "VALUE",
        #             "unit": "UNIT",
        #         },
        #         "management": None,
        #     },
        #     # "pft_lookup_files": {
        #     #     "cover": "lat53.360000_lon13.800000__PFT__data_cover.txt"
        #     # },
        #     # "pft_lookup_specs": {"cover": "default"},
        #     "pft_lookup_files": {"cover": "lat53.360000_lon13.800000__PFT__names.txt"},
        #     "pft_lookup_specs": {
        #         "cover": {
        #             "key_column": "Code",
        #             "info_column": PFT_COMBINED_COLUMN_NAME,
        #             "info_name": "PFT",
        #         }
        #     },
        #     "station_file": "DE_AgroScapeQuillow_station.csv",
        #     "start_year": 2000,
        # },
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
                    "info_column": PFT_COMBINED_COLUMN_NAME,
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
        # "3de1057c-a364-44f2-8a2a-350d21b58ea0": {
        #     "name": "Obergurgl",
        #     "variables": [
        #         "absolute_frequency"
        #     ],  # FREQ (pres/abs in 100 subplots of 1 m²)
        #     "short_names": {"absolute_frequency": "OGL-AF"},
        #     "file_names": {"absolute_frequency": "AT_Obergurgl_data.csv"},
        #     "observation_columns": {
        #         "absolute_frequency": "default",
        #         "management": None,
        #     },
        #     "pft_lookup_files": {
        #         "absolute_frequency": "lat46.867100_lon11.024900__PFT__data.txt"
        #     },
        #     "pft_lookup_specs": {"absolute_frequency": "default"},
        #     "station_file": "AT_Obergurgl_station.csv",
        #     "start_year": 2000,
        # },
        "4ac03ec3-39d9-4ca1-a925-b6c1ae80c90d": {
            "name": "Hochschwab (AT-HSW) GLORIA",
            "variables": [
                "cover",
                # "abundance_gloria_1_8",
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
                "cover_braun_blanquet": "IT_MontagnadiTorricchio_v2_cover.csv"
            },
            "observation_columns": {
                "cover_braun_blanquet": "default",
                "management": None,
            },
            "pft_lookup_files": {
                "cover_braun_blanquet": "lat42.961400_lon13.019200__PFT__v2_cover.txt"
            },
            "pft_lookup_specs": {"cover_braun_blanquet": "default"},
            "station_file": "IT_MontagnadiTorricchio_v2_station.csv",
            "start_year": 2002,
        },
        # "829a2bcc-79d6-462f-ae2c-13653124359d": {
        #     "name": "Ordesa y Monte Perdido / Huesca ES",
        #     "variables": [
        #         "absolute_frequency"
        #     ],  # abundance number of contacts each 10 cm in 20 m transects ()
        #     "short_names": {"absolute_frequency": "OMP-AF"},
        #     "file_names": {
        #         "absolute_frequency": "ES_OrdesaYMontePerdido_data_freq.csv"
        #     },
        #     "observation_columns": {
        #         "absolute_frequency": "default",
        #         "management": None,
        #     },
        #     "pft_lookup_files": {
        #         "absolute_frequency": "lat42.650000_lon0.030000__PFT__data_freq.txt"
        #     },
        #     "pft_lookup_specs": {"absolute_frequency": "default"},
        #     "station_file": "ES_OrdesaYMontePerdido_station.csv",
        #     "start_year": 1993,
        # },
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
        # "a03ef869-aa6f-49cf-8e86-f791ee482ca9": {
        #     "name": "Torgnon grassland Tellinod (IT19 Aosta Valley)",
        #     "variables": ["frequency_daget_poissonet"],  # relative abundance?
        #     # According to the method of Daget and Poissonet (1971), the specific contributions
        #     # are derived as the quotient between the frequency of a species and the sum
        #     # of the frequencies of all species.
        #     "short_names": {"frequency_daget_poissonet": "TGT-F"},
        #     "file_names": {
        #         "frequency_daget_poissonet": "IT_TorgnonGrasslandTellinod_data_abund.csv"
        #     },
        #     "observation_columns": {
        #         "frequency_daget_poissonet": "default",
        #         "management": None,
        #     },
        #     "pft_lookup_files": {
        #         "frequency_daget_poissonet": "lat45.846063_lon7.579028__PFT__data_abund.txt"
        #     },
        #     "pft_lookup_specs": {"frequency_daget_poissonet": "default"},
        #     "station_file": "IT_TorgnonGrasslandTellinod_station.csv",
        #     "start_year": 2009,
        # },
        # "b356da08-15ac-42ad-ba71-aadb22845621": {
        #     "name": "Nørholm Hede",
        #     "variables": ["cover"],
        #     "short_names": {"cover": "NHH-C"},
        #     "file_names": {"cover": "DK_NorholmHede_data_cover.csv"},
        #     "observation_columns": {
        #         "cover": {
        #             "plot": "STATION_CODE",
        #             "subplot": "PLOT (10x10m)",
        #             "layer": "LAYER",
        #             "time": "TIME",
        #             "species": "TAXA",
        #             "value": "VALUE",
        #             "unit": "UNIT",
        #         },
        #         "management": None,
        #     },
        #     "pft_lookup_files": {
        #         "cover": "lat55.680000_lon8.610000__PFT__data_cover.txt"
        #     },
        #     "pft_lookup_specs": {"cover": "default"},
        #     "station_file": "DK_NorholmHede_station.csv",
        #     "start_year": 1921,
        # },
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
                "cover": "lat42.086116_lon14.085206__PFT__data_cover__from_FEM_Revised.txt"
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

# Define species data specifications for selected eLTER sites.
# Cf. data at https://b2share.eudat.eu/records/?q=biodt&sort=-&page=1&size=25.
SPECIES_DATA_SPECS_PER_SITE = MappingProxyType(
    {
        "11696de6-0ab9-4c94-a06b-7ce40f56c964": {
            "name": "IT25 - Val Mazia-Matschertal",
            "file_names": ["IT_Matschertal_data_abund.csv"],
            "species_columns": ["TAXA"],
            "extra_columns": [[]],
        },
        # "270a41c4-33a8-4da6-9258-2ab10916f262": {
        #     "name": "AgroScapeLab Quillow (ZALF)",
        #     "file_names": [
        #         "DE_AgroScapeQuillow_data_cover.csv",
        #         "Code_Species_names.csv",
        #     ],
        #     "species_columns": ["TAXA", "Speciesname"],
        #     "extra_columns": [[], ["Code", "Family"]],
        # },
        "31e67a47-5f15-40ad-9a72-f6f0ee4ecff6": {
            "name": "LTSER Zone Atelier Armorique",
            "file_names": [
                "FR_AtelierArmorique_reference.csv",
                "FR_AtelierArmorique_data_indices.csv",
            ],
            "species_columns": ["NAME", "Dominant species"],
            "extra_columns": [["CODE", "FAMILY_NAME"], []],
        },
        "324f92a3-5940-4790-9738-5aa21992511c": {
            "name": "Stubai (combination of Neustift meadows and Kaserstattalm)",
            "file_names": ["AT_Stubai_data_abund.csv"],
            "species_columns": ["TAXA"],
            "extra_columns": [[]],
        },
        # "3de1057c-a364-44f2-8a2a-350d21b58ea0": {
        #     "name": "Obergurgl",
        #     "file_names": [
        #         "AT_Obergurgl_reference.csv",
        #         "AT_Obergurgl_data.csv",
        #     ],
        #     "species_columns": ["NAME", "TAXA"],
        #     "extra_columns": [[], []],
        # },
        "4ac03ec3-39d9-4ca1-a925-b6c1ae80c90d": {
            "name": "Hochschwab (AT-HSW) GLORIA",
            "file_names": [
                "AT_Hochschwab_reference.csv",
                "AT_Hochschwab_data_cover.csv",
                "AT_Hochschwab_data_abund.csv",
            ],
            "species_columns": ["NAME", "TAXA", "TAXA"],
            "extra_columns": [["CODE"], [], []],
        },
        "61c188bc-8915-4488-8d92-6d38483406c0": {
            "name": "Randu meadows",
            "file_names": ["LV_RanduMeadows_data_abund.csv"],
            "species_columns": ["TAXA"],
            "extra_columns": [[]],
        },
        "66431807-ebf1-477f-aa52-3716542f3378": {
            "name": "LTSER Engure",
            "file_names": ["LV_Engure_data_cover.csv"],
            "species_columns": ["TAXA"],
            "extra_columns": [[]],
        },
        "6ae2f712-9924-4d9c-b7e1-3ddffb30b8f1": {
            "name": "GLORIA Master Site Schrankogel (AT-SCH), Stubaier Alpen",
            "file_names": [
                "AT_Schrankogel_reference.csv",
                "AT_Schrankogel_data_cover.csv",
            ],
            "species_columns": ["NAME", "TAXA"],
            "extra_columns": [["CODE"], []],
        },
        "6b62feb2-61bf-47e1-b97f-0e909c408db8": {
            "name": "Montagna di Torricchio",
            "file_names": [
                "IT_MontagnadiTorricchio_v2_cover.csv",
            ],
            "species_columns": ["TAXA"],
            "extra_columns": [
                []
            ],  # [["TAXA_ALT"]] could be used, but needs code adjustment as TAXA column can have duplicates then
        },
        # "829a2bcc-79d6-462f-ae2c-13653124359d": {
        #     "name": "Ordesa y Monte Perdido / Huesca ES",
        #     "file_names": [
        #         "ES_OrdesaYMontePerdido_data_freq.csv"
        #     ],  # "ES_OrdesaYMontePerdido_reference.csv",
        #     "species_columns": ["TAXA"],
        #     "extra_columns": [[]],
        # },
        "9f9ba137-342d-4813-ae58-a60911c3abc1": {
            "name": "Rhine-Main-Observatory",
            "file_names": [
                "DE_RhineMainObservatory_abund_data.csv",
                "DE_RhineMainObservatory_data_abund_V2.xlsx",
            ],
            "species_columns": ["TAXA", "TAXA"],
            "extra_columns": [[], []],
        },
        # "a03ef869-aa6f-49cf-8e86-f791ee482ca9": {
        #     "name": "Torgnon grassland Tellinod (IT19 Aosta Valley)",
        #     "file_names": ["IT_TorgnonGrasslandTellinod_data_abund.csv"],
        #     "species_columns": ["TAXA"],
        #     "extra_columns": [[]],
        # },
        # "b356da08-15ac-42ad-ba71-aadb22845621": {
        #     "name": "Nørholm Hede",
        #     "file_names": ["DK_NorholmHede_data_cover.csv"],
        #     "species_columns": ["TAXA"],
        #     "extra_columns": [[]],
        # },
        "c0738b00-854c-418f-8d4f-69b03486e9fd": {
            "name": "Appennino centrale: Gran Sasso d'Italia",
            "file_names": [
                "IT_AppenninoCentrale_reference.csv",
                "IT_AppenninoCentrale_data_abund.csv",
            ],
            "species_columns": ["CODE", "TAXA"],
            "extra_columns": [[], []],
        },
        "c85fc568-df0c-4cbc-bd1e-02606a36c2bb": {
            "name": "Appennino centro-meridionale: Majella-Matese",
            "file_names": [
                "IT_AppenninoCentroMeridionale_data_cover.csv",
                "IT_AppenninoCentroMeridionale_data_cover__from_FEM_Revised.csv",
            ],
            "species_columns": ["TAXA", "TAXA"],
            "extra_columns": [[], []],
        },
        "e13f1146-b97a-4bc5-9bc5-65322379a567": {
            "name": "Jalovecka dolina",
            "file_names": ["SK_JaloveckaDolina_data_cover.csv"],
            "species_columns": ["TAXA"],
            "extra_columns": [[]],
        },
        # not eLTER plus
        "KUL-site": {
            "name": "KUL-site (KU Leuven)",
            "file_names": ["BE_KUL-site_cover__from_VanMeerbeek_data.csv"],
            "species_columns": ["TAXA"],
            "extra_columns": [["PFT_ORIGINAL"]],
        },
        "4c8082f9-1ace-4970-a603-330544f22a23": {
            "name": "Certoryje-Vojsicke Louky meadows",
            "file_names": [
                "CZ_Certoryje-Vojsice_cover__from_regrassed_fields_Bile_Karpaty.csv"
            ],
            "species_columns": ["TAXA"],
            "extra_columns": [[]],
        },
        "4d7b73d7-62da-4d96-8cb3-3a9a744ae1f4": {
            "name": "DFG_Biodiversity_Exploratory_Schorfheide-Chorin",
            "file_names": ["DE_BEXIS-site-SEG_data_cover__from_31973_5_Dataset.csv"],
            "species_columns": ["TAXA"],
            "extra_columns": [["PFT_ORIGINAL"]],
        },
        "56c467e5-093f-4b60-b5cf-880490621e8d": {
            "name": "DFG_Biodiversity_Exploratory_Hainich-Duen",
            "file_names": ["DE_BEXIS-site-HEG_data_cover__from_31973_5_Dataset.csv"],
            "species_columns": ["TAXA"],
            "extra_columns": [["PFT_ORIGINAL"]],
        },
        "a51f9249-ddc8-4a90-95a8-c7bbebb35d29": {
            "name": "DFG_Biodiversity_Exploratory_SchwaebischeAlb",
            "file_names": ["DE_BEXIS-site-AEG_data_cover__from_31973_5_Dataset.csv"],
            "species_columns": ["TAXA"],
            "extra_columns": [["PFT_ORIGINAL"]],
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
        "info_column": PFT_COMBINED_COLUMN_NAME,
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
