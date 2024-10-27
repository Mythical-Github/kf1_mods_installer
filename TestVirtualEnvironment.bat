@echo off

cd /d "%~dp0"


.venv\Scripts\activate && uv run "%CD%/__main__.py"

exit /b 0
