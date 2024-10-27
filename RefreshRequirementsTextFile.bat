@echo off

pip install uv

cd /d "%~dp0"

set "c_one=uv pip install bs4"
set "c_two=uv pip freeze | uv pip compile - -o requirements.txt"

uv venv
.venv\Scripts\activate && %c_one% && %c_two%

pause

exit /b 0
