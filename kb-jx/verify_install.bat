@echo off
REM ========================================
REM ??????
REM ========================================

echo ========================================
echo ?????? - ????
echo ========================================
echo.

echo [1/5] ?? Python ??...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo [??] Python ???
    goto :error
)
echo [??] Python ????
echo.

echo [2/5] ??????...
python -c "import fastapi; print(''FastAPI:'', fastapi.__version__)"
if %ERRORLEVEL% NEQ 0 (
    echo [??] FastAPI ???
    goto :error
)

python -c "import uvicorn; print(''Uvicorn:'', uvicorn.__version__)"
if %ERRORLEVEL% NEQ 0 (
    echo [??] Uvicorn ???
    goto :error
)
echo [??] ??????
echo.

echo [3/5] ???????...
python -c "import docx; print(''python-docx:'', docx.__version__)"
python -c "import openpyxl; print(''openpyxl:'', openpyxl.__version__)"
python -c "import pptx; print(''python-pptx:'', pptx.__version__)"
python -c "import fitz; print(''PyMuPDF:'', fitz.version)"
if %ERRORLEVEL% NEQ 0 (
    echo [??] ??????????
    goto :error
)
echo [??] ???????
echo.

echo [4/5] ?? Office COM ??...
python -c "try: import win32com.client; print(''[??] Office COM ?????''); except: print(''[??] Office COM ????.doc/.xls/.ppt ?????'')"
echo.

echo [5/5] ??????...
if not exist main.py (
    echo [??] ???????
    goto :error
)
if not exist api\v1\endpoints.py (
    echo [??] API ????
    goto :error
)
if not exist services\detector.py (
    echo [??] ??????
    goto :error
)
echo [??] ??????
echo.

echo ========================================
echo ?????????????
echo ========================================
echo.
echo ????: python main.py
echo ???: start.bat
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo ??????????
echo ========================================
echo.
echo ??:
echo 1. ?? install_offline.bat ????
echo 2. ?? Python ?? ^>= 3.10
echo 3. ?? offline_packages ????
echo.
pause
exit /b 1
