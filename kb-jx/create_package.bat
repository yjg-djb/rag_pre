@echo off
REM ========================================
REM ???????
REM ========================================

echo ========================================
echo ???????
echo ========================================
echo.

SET PACKAGE_NAME=kb-jx-offline-deploy
SET EXCLUDE_DIRS=storage logs __pycache__ .git test_files .gitignore

echo [1/3] ??????...
rd /s /q storage 2>nul
rd /s /q logs 2>nul
del /s /q *.pyc 2>nul
echo ??
echo.

echo [2/3] ??????...
if exist %PACKAGE_NAME% rd /s /q %PACKAGE_NAME%
mkdir %PACKAGE_NAME%
echo ??
echo.

echo [3/3] ????...
xcopy /E /I /Y api %PACKAGE_NAME%\api
xcopy /E /I /Y models %PACKAGE_NAME%\models
xcopy /E /I /Y services %PACKAGE_NAME%\services
xcopy /E /I /Y utils %PACKAGE_NAME%\utils
xcopy /E /I /Y static %PACKAGE_NAME%\static
xcopy /E /I /Y offline_packages %PACKAGE_NAME%\offline_packages

copy main.py %PACKAGE_NAME%\
copy requirements.txt %PACKAGE_NAME%\
copy install_offline.bat %PACKAGE_NAME%\
copy README_OFFLINE.txt %PACKAGE_NAME%\
copy start.bat %PACKAGE_NAME%\ 2>nul
copy clean_storage.bat %PACKAGE_NAME%\ 2>nul
copy clean_task.py %PACKAGE_NAME%\ 2>nul

echo ??
echo.

echo ========================================
echo ?????
echo ========================================
echo.
echo ?????: %PACKAGE_NAME%
echo.
echo ????
echo   1. ?? %PACKAGE_NAME% ??? ZIP ??
echo   2. ????????
echo   3. ????? install_offline.bat
echo.
echo ========================================

pause
