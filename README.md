# BioDT - pDT Grassland
Main repository for workflows belonging to the grassland Digital Twin.

<a href="https://doi.org/10.5281/zenodo.15784817"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.15784817.svg" alt="DOI"></a>

## Installation

### Python Package Installation
The current development version can be installed as:

    pip install git+https://github.com/BioDT/uc-grassland.git@main
    
It requires also installing the following packages:

    pip install git+https://github.com/BioDT/general-copernicus-weather-data.git@main
    pip install git+https://github.com/BioDT/general-soilgrids-soil-data.git@main

### Docker Installation
Alternatively, you can use Docker Compose to run the complete pipeline without manual Python package installation. This is the recommended approach for production environments. See [Usage with Docker Compose](#usage-with-docker-compose) for details.
    
## Usage
Download all input data and prepare as needed for grassland model simulations:

```python
from ucgrassland import prep_grassland_model_input_data

# one location only
coordinates_list = [{"lat": 51.123456, "lon": 11.987654}]
first_year = 2010
last_year = 2024
prep_grassland_model_input_data(coordinates_list, first_year, last_year)

# several locations
coordinates_list = [{"lat": 51.123456, "lon": 11.987654}, {"lat": 51.456, "lon": 11.654}, {"lat": 51.789, "lon": 11.321}]
prep_grassland_model_input_data(coordinates_list, first_year, last_year)

# use DEIMS.iD to obtain location (centroid or representative coordinates, valid DEIMS.ID required)
coordinates_list = None
deims_id = '00000000-0000-0000-0000-000000000000'
prep_grassland_model_input_data(coordinates_list, first_year, last_year, deims_id = deims_id)
```

Full function signature: 

`prep_grassland_model_input_data(coordinates_list,
    first_year,
    last_year,
    *,
    deims_id=None,
    skip_grass_check=False,
    skip_weather=False,
    skip_soil=False,
    skip_management=False)`

Parameters:
- coordinates_list (list of dict): List of dictionaries with 'lat' and 'lon' keys, or None for using DEIMS.iD to get coordinates of one location.
- first_year (int): First year of desired time period.
- last_year (int): Last year of desired time period.
- deims_id (str): DEIMS.iD to get coordinates of one location (default is None, only used if coordinates_list is None).
- skip_grass_check (bool): Skip grassland checks (default is False).
- skip_weather (bool): Skip weather data preparation (default is False).
- skip_soil (bool): Skip soil data preparation (default is False).
- skip_management (bool): Skip management data preparation (default is False).

### Usage with Docker Compose

The grassland Digital Twin can be run using Docker Compose, which handles both data preparation and model simulation.

#### Prerequisites

1. Copy `.env.example` to `.env` file in the repository root with your credentials:
```bash
# WEkEO HDA credentials (for Copernicus data access)
HDA_USER=your_wekeo_username
HDA_PASSWORD=your_wekeo_password

# CDS API key (for ERA5 weather data)
CDSAPI_KEY=your_cds_api_key

# Location parameters
LAT=51.3919
LON=11.8787
startYear=2017
endYear=2021
DEIMS=
```

**Important**: `HDA_PASSWORD` should be your actual WEkEO account password, not an API token. The HDA library will automatically obtain and manage access tokens internally.

2. Ensure you have Docker and Docker Compose installed on your system.

#### Running the Pipeline

Execute the full pipeline (data preparation + model simulation):

```bash
docker compose up
```

This will:
1. Build the Docker image with all dependencies
2. Download and prepare input data (land cover, weather, soil, management)
3. Run the grassland model simulations
4. Save all outputs to the `./output` directory

#### Output Structure

Results are saved in `./output/` with the following structure:
```
output/
├── parameters/          # Model parameter files used in the simulation
├── lat{LAT}_lon{LON}/   # Location-specific results
│   ├── scenarios/       # Input scenarios for the model
│   └── simulations/     # Model simulation outputs
```


## Developers
Developed in the BioDT project (until 2025-05) by Thomas Banitz (UFZ) with contributions by Franziska Taubert (UFZ), 
Tuomas Rossi (CSC) and Taimur Haider Khan (UFZ).

Further developed (from 2025-06) by Thomas Banitz (UFZ) with contributions by Franziska Taubert (UFZ).

## Copyright
Copyright (C) 2024
- Helmholtz Centre for Environmental Research GmbH - UFZ, Germany
- CSC - IT Center for Science Ltd., Finland

Licensed under the EUPL, Version 1.2 or - as soon they will be approved
by the European Commission - subsequent versions of the EUPL (the "Licence").
You may not use this work except in compliance with the Licence.

You may obtain a copy of the Licence at:
https://joinup.ec.europa.eu/software/page/eupl

## Funding
The BioDT project has received funding from the European Union's Horizon Europe Research and Innovation
Programme under grant agreement No 101057437 (BioDT project, https://doi.org/10.3030/101057437).
The authors acknowledge the EuroHPC Joint Undertaking and CSC - IT Center for Science Ltd., Finland
for awarding this project access to the EuroHPC supercomputer LUMI, hosted by CSC - IT Center for
Science Ltd., Finland and the LUMI consortium through a EuroHPC Development Access call.

## Data sources
Land cover maps and classifications:

- Eunis EEA habitat types (version 2012).
https://eunis.eea.europa.eu/habitats-code-browser.jsp.

- European Union's Copernicus Land Monitoring Service (2020).
High Resolution Layer (HRL) Grassland 2018 raster, Europe.
https://doi.org/10.2909/60639d5b-9164-4135-ae93-fb4132bb6d83.

- European Union's Copernicus Land Monitoring Service (2024).
Grassland 2017 - Present (raster 10m), Europe, yearly, Nov. 2024.
https://doi.org/10.2909/0b6254bb-4c7d-41d9-8eae-c43b05ab2965.

- European Union's Copernicus Land Monitoring Service (2024).
Herbaceous cover 2017 - Present (raster 10m), Europe, yearly, Nov. 2024.
https://doi.org/10.2909/9da6ca39-043a-4bdd-8d0a-41a7bed6e439.

- Pflugmacher, D., Rabe, A., Peters, M., Hostert, P. (2018).
Pan-European land cover map of 2015 based on Landsat and LUCAS data.
PANGAEA, https://doi.org/10.1594/PANGAEA.896282.

- Preidl, S., Lange, M., Doktor, D. (2020).
Land cover classification map of Germany's agricultural area based on Sentinel-2A data from 2016.
PANGAEA, https://doi.org/10.1594/PANGAEA.910837.

- Schwieder, M., Tetteh, G.O., Blickensdörfer, L., Gocht, A., Erasmi, S. (2024).
Agricultural land use (raster): National-scale crop type maps for Germany from combined time series of
Sentinel-1, Sentinel-2 and Landsat data (2017 to 2021).
Zenodo, https://zenodo.org/records/10640528.

- German ATKIS digital landscape model 2015
Bundesamt für Kartographie und Geodäsie, 2015.
Digitales Basis-Landschaftsmodell (AAA-Modellierung).
GeoBasis-DE. Geodaten der deutschen Landesvermessung.
Derived via land use maps by Lange et al. (2022), https://data.mendeley.com/datasets/m9rrv26dvf/1.

Weather data: 
- See https://github.com/BioDT/general-copernicus-weather-data.


Soil data: 
- See https://github.com/BioDT/general-soilgrids-soil-data.

Management data:
- European Union's Copernicus Land Monitoring Service (2024).
Grassland Mowing Events 2017 - Present (raster 10m), Europe, yearly, Nov. 2024.
https://doi.org/10.2909/114e8cae-1cd7-4adc-8c5f-a04863fc6af9.

- European Union's Copernicus Land Monitoring Service (2024).
Grassland Mowing Dates 2017 - Present (raster 10m), Europe, yearly – 4 layers, Nov. 2024
https://doi.org/10.2909/660d00f1-c6de-4db6-9979-0be124ceb7f0.

- Lange, M., Feilhauer, H., Kühn, I., Doktor, D. (2022).
Mapping land-use intensity of grasslands in Germany with machine learning and Sentinel-2 time series.
Remote Sensing of Environment, https://doi.org/10.1016/j.rse.2022.112888. 
Based on grassland classification according to: German ATKIS digital landscape model 2015.

- Schwieder, M., Wesemeyer, M., Frantz, D., Pfoch, K., Erasmi, S., Pickert, J., Nendel, C., Hostert, P. (2022).
Mapping grassland mowing events across Germany based on combined Sentinel-2 and Landsat 8 time series.
Remote Sensing of Environment, https://doi.org/10.1016/j.rse.2021.112795

- Blickensdörfer, L., Schwieder, M., Pflugmacher, D., Nendel, C., Erasmi, S., Hostert, P. (2021).
National-scale crop type maps for Germany from combined time series of Sentinel-1, Sentinel-2 and
Landsat 8 data (2017, 2018 and 2019).
https://zenodo.org/records/5153047.

- Filipiak, M., Gabriel, D., Kuka, K. (2022).
Simulation-based assessment of the soil organic carbon sequestration in grasslands in relation to
management and climate change scenarios.
https://doi.org/10.1016/j.heliyon.2023.e17287.

- Schmid, J. (2022).
Modeling species-rich ecosystems to understand community dynamics and structures emerging from
individual plant interactions.
PhD thesis, Chapter 4, Table C.7, https://doi.org/10.48693/160.

Plant species traits data:
- TRY categorical traits table:
    - Kattge, J., Bönisch, G., Günther, A., Wright, I., Zanne, A.E., Wirth, C., Reich, P.B. and the TRY Consortium (2012).
      TRY - Categorical Traits Dataset. Data from: TRY - a global database of plant traits.
      TRY File Archive, https://www.try-db.org/TryWeb/Data.php#3.
    - Kattge, J., Díaz, S., Lavorel, S., Prentice, I., Leadley, P., et al. (2011).
      TRY - a global database of plant traits.
      Global Change Biology, https://doi.org/10.1111/j.1365-2486.2011.02451.x.
    - Kattge, J., Bönisch, G., Díaz S., et al. (2020).
      TRY plant trait database - enhanced coverage and open access. 
      Global Change Biology, https://doi.org/10.1111/gcb.14904. 

- GBIF taxonomic backbone:
    - GBIF Secretariat (2023). GBIF Backbone Taxonomy. Checklist dataset.

- Growth form table:
    - Cornwell, W. (2019). traitecoevo/growthform v0.2.3 (v0.2.3). Zenodo. https://doi.org/10.5281/zenodo.2543013
    - Zanne, A.E., Tank, D.C., Cornwell, W.K., Eastman, J.M., Smith, S.A., et al. (2014). 
      Three keys to the radiation of angiosperms into freezing environments.
      Nature, https://doi.org/10.1038/nature12872.

Reverse geocoding:
- Nominatim (reverse geocoding):
    - URL: https://nominatim.openstreetmap.org/reverse
    - API documentation: https://nominatim.org/release-docs/develop/api/Overview/
    - Usage policy: https://operations.osmfoundation.org/policies/nominatim/
    - Terms of use: https://osmfoundation.org/wiki/Terms_of_Use
