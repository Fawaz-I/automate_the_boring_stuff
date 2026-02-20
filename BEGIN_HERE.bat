@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PYTHON_CMD="

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=py -3"
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set "PYTHON_CMD=python"
  )
)

if "%PYTHON_CMD%"=="" (
  echo Python 3 is required but was not found.
  echo Install Python 3 from https://www.python.org/downloads/ and run this file again.
  pause
  exit /b 1
)

%PYTHON_CMD% "%SCRIPT_DIR%build_offline_bundle.py"
if %errorlevel% neq 0 (
  echo Build failed. Please review the messages above, then try again.
  pause
  exit /b 1
)

if exist "%SCRIPT_DIR%offline_content\index.html" (
  start "" "%SCRIPT_DIR%offline_content\index.html"
)

endlocal
