@echo off

cd /d %~dp0

set "project_exe=%CD%/kf1_mods_installer.exe"
set "project_exe_arg=download_and_install_mods"

"%project_exe%" %project_exe_arg%

rem pause

exit /b 0