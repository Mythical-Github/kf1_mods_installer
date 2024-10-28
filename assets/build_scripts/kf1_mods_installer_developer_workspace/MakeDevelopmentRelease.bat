@echo off

set "project_name=kf1_mods_installer"

set "MainDir=%~dp0%project_name%"
set "DevelopmentDirToZip=%MainDir%\assets\build_scripts\%project_name%_developer_workspace"
set "FinalZipLocation=%~dp0Development.zip"

if not exist  "%~dp0/%project_name%" (
     "%~dp0/VirtualEnvironmentSetup.bat"
)

cd /d "%MainDir%"

echo Creating zip file from %DevelopmentDirToZip% to %FinalZipLocation%
powershell -Command "Compress-Archive -Path '%DevelopmentDirToZip%' -DestinationPath '%FinalZipLocation%' -Force"
