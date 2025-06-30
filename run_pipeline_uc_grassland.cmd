REM ####################################
REM ### User variables either inserted directly by a user or derived from the BioDT Shiny App ########
REM ####################################

SET /a endYear=%date:~-4%-1
SET /a startYear=%date:~-4%-3
SET LAT=51.391900
SET LON=11.878700
SET DEIMS=102ae489-04e3-481d-97df-45905837dc1a
REM comment: if LAT and LON is provided, DEIMS can also be set to NaN (as it has no effect on the simulations)

REM ####################################
REM ####### get model source code ######
REM ####################################

if exist uc-grassland-model (
	cd uc-grassland-model 
	git pull
) else (
	git clone https://github.com/BioDT/uc-grassland-model.git
	cd uc-grassland-model
)

REM ####################################
REM ####### create input data ##########
REM ####################################

pip uninstall --yes ucgrassland
pip uninstall --yes soilgrids
pip uninstall --yes copernicus

pip install git+https://github.com/BioDT/uc-grassland.git@main
pip install git+https://github.com/BioDT/general-copernicus-weather-data.git@main
pip install git+https://github.com/BioDT/general-soilgrids-soil-data.git@main


cd scenarios
python -c "from ucgrassland import prep_grassland_model_input_data; prep_grassland_model_input_data([{'lat': %LAT%, 'lon': %LON%}], %startYear%, %endYear%)"

cd ..
xcopy scenarios\grasslandModelInputFiles\lat%LAT%_lon%LON% scenarios\lat%LAT%_lon%LON% /E /Y

del /f /s /q scenarios\grasslandModelInputFiles 1>nul
rmdir /s /q scenarios\grasslandModelInputFiles

REM ####################################
REM ## create & modify config ##########
REM ####################################

cd simulations
mkdir project_%LAT%_%LON%
copy project_template\latLAT_lonLON__startYear-01-01_endYear-12-31__configuration__generic_v1.txt project_%LAT%_%LON%\latLAT_lonLON__startYear-01-01_endYear-12-31__configuration__generic_v1.txt
copy project_template\latLAT_lonLON__startYear-01-01_endYear-12-31__outputWritingDates.txt project_%LAT%_%LON%\latLAT_lonLON__startYear-01-01_endYear-12-31__outputWritingDates.txt
copy project_template\runSimulation.cmd project_%LAT%_%LON%\runSimulation.cmd /Y

cd project_%LAT%_%LON%
SET configDir=%CD%
ren %configDir%\latLAT_lonLON__startYear-01-01_endYear-12-31__configuration__generic_v1.txt lat%LAT%_lon%LON%__%startYear%-01-01_%endYear%-12-31__configuration__generic_v1.txt
ren %configDir%\latLAT_lonLON__startYear-01-01_endYear-12-31__outputWritingDates.txt lat%LAT%_lon%LON%__%startYear%-01-01_%endYear%-12-31__outputWritingDates.txt

python ..\\modifyConfig.py %LAT% %LON% %startYear% %endYear% %DEIMS%

REM ####################################
REM ####### run the simulation #########
REM ####################################

python ..\\runReplicatedSimulations.py %LAT% %LON% %startYear% %endYear%







