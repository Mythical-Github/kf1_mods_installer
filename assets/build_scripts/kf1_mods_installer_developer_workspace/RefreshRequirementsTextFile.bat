@echo off

cd /d "%~dp0"

set "project_name=kf1_mods_installer"

set "base_dir=%~dp0%project_name%"

if not exist  "%~dp0/%project_name%" (
     "%~dp0/VirtualEnvironmentSetup.bat"
)

cd "%base_dir%"

set "c_one=uv pip install bs4"
set "c_two=uv pip install requests"
set "c_three=uv pip freeze | uv pip compile - -o requirements.txt"

uv venv --python 3.13.0
.venv\Scripts\activate && %c_one% && %c_two% && %c_three%

exit /b 0
