@echo off

set "project_name=kf1_mods_installer"

if not exist  "%~dp0/%project_name%" (
     "%~dp0/VirtualEnvironmentSetup.bat"
)

cd /d "%~dp0/%project_name%"

.venv\Scripts\activate && uv run "%CD%/src/%project_name%/__main__.py"

exit /b 0
