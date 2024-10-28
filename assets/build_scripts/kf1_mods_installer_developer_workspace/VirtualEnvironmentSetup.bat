@echo off

set "project_name=kf1_mods_installer"

:: Change to the directory where the script is located
cd /d "%~dp0"

:: Define the base directory
set "base_dir=%~dp0%project_name%"

:: Install uv if not already installed
pip install uv

:: Remove the existing directory if it exists
if not exist "%base_dir%" (
    git clone -b dev https://github.com/Mythical-Github/%project_name%.git "%base_dir%"
)

:: Change to the base directory
cd "%base_dir%"

:: Set the run application command
set command=uv run "%base_dir%/src/%project_name%/__main__.py"

:: Create and activate the virtual environment, then install requirements, then run the application, then pause
uv venv --python 3.13.0
.venv\Scripts\activate && uv pip install -r requirements.txt && %command%