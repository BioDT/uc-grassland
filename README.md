# BioDT - pDT Grassland
Main repository for workflows belonging to the grassland Digital Twin.

## Installation
The current development version can be installed as:

    pip install git+https://github.com/BioDT/uc-grassland.git@main
    
It requires also installing the following packages:

    pip install git+https://github.com/BioDT/general-copernicus-weather-data.git@main
    pip install git+https://github.com/BioDT/general-soilgrids-soil-data.git@main
    
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
    skip_management=False
)`

Parameters:
- coordinates_list (list of dict): List of dictionaries with 'lat' and 'lon' keys, or None for using DEIMS.iD to get coordinates of one location.
- first_year (int): First year of desired time period.
- last_year (int): Last year of desired time period.
- deims_id (str): DEIMS.iD to get coordinates of one location (default is None, only used if coordinates_list is None).
- skip_grass_check (bool): Skip grassland checks (default is False).
- skip_weather (bool): Skip weather data preparation (default is False).
- skip_soil (bool): Skip soil data preparation (default is False).
- skip_management (bool): Skip management data preparation (default is False).


## Developers
Developed in the BioDT project by Thomas Banitz (UFZ) with contributions by Franziska Taubert (UFZ), 
Tuomas Rossi (CSC) and Taimur Haider Khan (UFZ).

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
This project has received funding from the European Union's Horizon Europe Research and Innovation
Programme under grant agreement No 101057437 (BioDT project, https://doi.org/10.3030/101057437).
The authors acknowledge the EuroHPC Joint Undertaking and CSC - IT Center for Science Ltd., Finland
for awarding this project access to the EuroHPC supercomputer LUMI, hosted by CSC - IT Center for
Science Ltd., Finland and the LUMI consortium through a EuroHPC Development Access call.

## Data sources
Land cover maps and classifications:

- Eunis EEA habitat types (version 2012).
https://eunis.eea.europa.eu/habitats-code-browser.jsp

- European Union's Copernicus Land Monitoring Service information (2020).
High Resolution Layer (HRL) Grassland 2018 raster, Europe.
https://doi.org/10.2909/60639d5b-9164-4135-ae93-fb4132bb6d83

- Pflugmacher, D., Rabe, A., Peters, M., Hostert, P. (2018).
Pan-European land cover map of 2015 based on Landsat and LUCAS data.
PANGAEA, https://doi.org/10.1594/PANGAEA.896282

- Preidl, S., Lange, M., Doktor, D. (2020).
Land cover classification map of Germany's agricultural area based on Sentinel-2A data from 2016.
PANGAEA, https://doi.org/10.1594/PANGAEA.910837

- Schwieder, M., Tetteh, G.O., Blickensdörfer, L., Gocht, A., Erasmi, S. (2024).
Agricultural land use (raster): National-scale crop type maps for Germany from combined time series of
Sentinel-1, Sentinel-2 and Landsat data (2017 to 2021).
Zenodo, https://zenodo.org/records/10640528

- German ATKIS digital landscape model 2015
Bundesamt für Kartographie und Geodäsie, 2015.
Digitales Basis-Landschaftsmodell (AAA-Modellierung).
GeoBasis-DE. Geodaten der deutschen Landesvermessung.
Derived via land use maps by Lange et al. (2022), https://data.mendeley.com/datasets/m9rrv26dvf/1.

Weather data: 
- see https://github.com/BioDT/general-copernicus-weather-data


Soil data: 
- see https://github.com/BioDT/general-soilgrids-soil-data

Management data:
- Lange, M., Feilhauer, H., Kühn, I., Doktor, D. (2022).
Mapping land-use intensity of grasslands in Germany with machine learning and Sentinel-2 time series,
Remote Sensing of Environment, https://doi.org/10.1016/j.rse.2022.112888. 
Based on grassland classification according to: German ATKIS digital landscape model 2015.

- Schwieder, M., Wesemeyer, M., Frantz, D., Pfoch, K., Erasmi, S., Pickert, J., Nendel, C., Hostert, P. (2022).
Mapping grassland mowing events across Germany based on combined Sentinel-2 and Landsat 8 time series,
Remote Sensing of Environment, https://doi.org/10.1016/j.rse.2021.112795

- Blickensdörfer, L., Schwieder, M., Pflugmacher, D., Nendel, C., Erasmi, S., Hostert, P. (2021).
National-scale crop type maps for Germany from combined time series of Sentinel-1, Sentinel-2 and
Landsat 8 data (2017, 2018 and 2019), https://zenodo.org/records/5153047.

- Filipiak, M., Gabriel, D., Kuka, K. (2022).
Simulation-based assessment of the soil organic carbon sequestration in grasslands in relation to
management and climate change scenarios, https://doi.org/10.1016/j.heliyon.2023.e17287

- Schmid, J. (2022).
Modeling species-rich ecosystems to understand community dynamics and structures emerging from
individual plant interactions, PhD thesis, Chapter 4, Table C.7, https://doi.org/10.48693/160

Plant species traits data:
- TRY categorical traits table:
    - Kattge, J., Bönisch, G., Günther, A., Wright, I., Zanne, A.E., Wirth, C., Reich, P.B. and the TRY Consortium (2012).
      TRY - Categorical Traits Dataset. Data from: TRY - a global database of plant traits.
      TRY File Archive. https://www.try-db.org/TryWeb/Data.php#3
    - Kattge, J., Díaz, S., Lavorel, S., Prentice, I., Leadley, P., et al. (2011).
      TRY - a global database of plant traits.
      Global Change Biology 17: 2905-2935. https://doi.org/10.1111/j.1365-2486.2011.02451.x
    - Kattge, J., Bönisch, G., Díaz S., et al. (2020).
      TRY plant trait database - enhanced coverage and open access. 
      Global Change Biology 26: 119-188. https://doi.org/10.1111/gcb.14904 

- GBIF taxonomic backbone:
    - GBIF Secretariat (2023). GBIF Backbone Taxonomy. Checklist dataset.

- Growth form table:
    - Cornwell, W. (2019). traitecoevo/growthform v0.2.3 (v0.2.3). Zenodo. https://doi.org/10.5281/zenodo.2543013
    - Zanne, A.E., Tank, D.C., Cornwell, W.K., Eastman, J.M., Smith, S.A., et al. (2014). 
      Three keys to the radiation of angiosperms into freezing environments.
      Nature 506: 89-92. https://doi.org/10.1038/nature12872
