@echo off

pip install uv

cd /d "%~dp0"

set "c_one=uv pip install bs4"
set "c_two=uv pip install requests"
set "c_three=uv pip freeze | uv pip compile - -o requirements.txt"

uv venv
.venv\Scripts\activate && %c_one% && %c_two% && %c_three%

pause

exit /b 0
