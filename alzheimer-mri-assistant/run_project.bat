@echo off
setlocal

cd /d "%~dp0"

set "PORT=8010"
set "VENV_DIR=.venv"
set "TARGET_PYTHON="
set "TARGET_ENV_NAME="
set "FALLBACK_PYTHON="
set "FALLBACK_ENV_NAME="
set "NEED_INSTALL=1"

echo [1/6] Searching for compatible environments...

if defined VIRTUAL_ENV call :consider_env "%VIRTUAL_ENV%\Scripts\python.exe" "active venv"
if defined TARGET_PYTHON goto :env_selected

if defined CONDA_PREFIX call :consider_env "%CONDA_PREFIX%\python.exe" "active conda"
if defined TARGET_PYTHON goto :env_selected

call :consider_env "%CD%\%VENV_DIR%\Scripts\python.exe" "project .venv"
if defined TARGET_PYTHON goto :env_selected

call :consider_env "%USERPROFILE%\miniconda3\envs\ai_ten\python.exe" "conda ai_ten"
if defined TARGET_PYTHON goto :env_selected

if defined FALLBACK_PYTHON (
    set "TARGET_PYTHON=%FALLBACK_PYTHON%"
    set "TARGET_ENV_NAME=%FALLBACK_ENV_NAME%"
    set "NEED_INSTALL=1"
    goto :env_selected
)

echo [2/6] No compatible environment found. Creating %VENV_DIR%...
call :create_project_venv
if errorlevel 1 (
    echo Failed to create a compatible project environment.
    pause
    exit /b 1
)

set "TARGET_PYTHON=%CD%\%VENV_DIR%\Scripts\python.exe"
set "TARGET_ENV_NAME=new project .venv"
set "NEED_INSTALL=1"

:env_selected
echo [2/6] Using environment: %TARGET_ENV_NAME%
echo [3/6] Python: %TARGET_PYTHON%

if "%NEED_INSTALL%"=="1" (
    echo [4/6] Installing missing dependencies...
    "%TARGET_PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install requirements in %TARGET_ENV_NAME%.
        pause
        exit /b 1
    )
) else (
    echo [4/6] Dependencies already installed. Skipping install.
)

echo [5/6] Selecting available port...
call :find_free_port
if errorlevel 1 (
    echo Could not find a free port between 8010 and 8099.
    pause
    exit /b 1
)

echo Selected port: %PORT%
echo [6/6] Starting app on http://127.0.0.1:%PORT%/
start "" "http://127.0.0.1:%PORT%/"

echo Running server...
"%TARGET_PYTHON%" -m uvicorn app.main:app --app-dir "." --host 127.0.0.1 --port %PORT%
if errorlevel 1 (
    echo Uvicorn exited with an error.
    pause
    exit /b 1
)

endlocal
exit /b 0

:consider_env
set "CANDIDATE_PY=%~1"
set "CANDIDATE_NAME=%~2"

if not exist "%CANDIDATE_PY%" exit /b 0

call :is_supported "%CANDIDATE_PY%"
if errorlevel 1 exit /b 0

call :has_requirements "%CANDIDATE_PY%"
if not errorlevel 1 (
    set "TARGET_PYTHON=%CANDIDATE_PY%"
    set "TARGET_ENV_NAME=%CANDIDATE_NAME%"
    set "NEED_INSTALL=0"
    exit /b 0
)

if not defined FALLBACK_PYTHON (
    set "FALLBACK_PYTHON=%CANDIDATE_PY%"
    set "FALLBACK_ENV_NAME=%CANDIDATE_NAME%"
)

exit /b 0

:is_supported
"%~1" -V 2>nul | findstr /R /C:"^Python 3\.10\." /C:"^Python 3\.11\." >nul
exit /b %errorlevel%

:has_requirements
"%~1" -c "import fastapi,uvicorn,numpy,cv2,PIL,onnxruntime,tensorflow,multipart,pydantic" >nul 2>&1
exit /b %errorlevel%

:create_project_venv
if exist "%CD%\%VENV_DIR%\Scripts\python.exe" (
    call :is_supported "%CD%\%VENV_DIR%\Scripts\python.exe"
    if not errorlevel 1 exit /b 0

    rmdir /s /q "%CD%\%VENV_DIR%"
)

where py >nul 2>&1
if not errorlevel 1 (
    py -3.11 -V >nul 2>&1
    if not errorlevel 1 (
        py -3.11 -m venv "%VENV_DIR%"
        if not errorlevel 1 exit /b 0
    )

    py -3.10 -V >nul 2>&1
    if not errorlevel 1 (
        py -3.10 -m venv "%VENV_DIR%"
        if not errorlevel 1 exit /b 0
    )
)

if exist "%USERPROFILE%\miniconda3\envs\ai_ten\python.exe" (
    call :is_supported "%USERPROFILE%\miniconda3\envs\ai_ten\python.exe"
    if not errorlevel 1 (
        "%USERPROFILE%\miniconda3\envs\ai_ten\python.exe" -m venv "%VENV_DIR%"
        if not errorlevel 1 exit /b 0
    )
)

where python >nul 2>&1
if not errorlevel 1 (
    call :is_supported "python"
    if not errorlevel 1 (
        python -m venv "%VENV_DIR%"
        if not errorlevel 1 exit /b 0
    )
)

exit /b 1

:find_free_port
set "CANDIDATE=%PORT%"

:find_free_port_loop
netstat -ano | findstr /I /C:":%CANDIDATE% " | findstr /I /C:"LISTENING" >nul
if errorlevel 1 (
    set "PORT=%CANDIDATE%"
    exit /b 0
)

set /a CANDIDATE+=1
if %CANDIDATE% GTR 8099 exit /b 1
goto :find_free_port_loop
