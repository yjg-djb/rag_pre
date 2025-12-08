@echo off
REM ========================================
REM 安装 PDF 和旧格式支持（PyMuPDF + pywin32）
REM ========================================

echo ========================================
echo 安装 PDF 和旧格式 Office 文件支持
echo ========================================
echo.

echo 此脚本将安装：
echo   1. PyMuPDF - 用于 PDF 文件检测和转换
echo   2. pywin32  - 用于 .doc/.xls/.ppt 文件转换
echo.

REM 检查离线包
echo [检查] 验证离线包文件...
set PKG_MISSING=0

if not exist "offline_packages\PyMuPDF-1.23.8-cp310-none-win_amd64.whl" (
    echo   [错误] PyMuPDF-1.23.8 wheel 文件不存在
    set PKG_MISSING=1
)

if not exist "offline_packages\pywin32-311-cp310-cp310-win_amd64.whl" (
    echo   [错误] pywin32-311 wheel 文件不存在
    set PKG_MISSING=1
)

if %PKG_MISSING%==1 (
    echo.
    echo [失败] 离线包文件不完整，请重新下载
    pause
    exit /b 1
)

echo   [确认] 所有离线包文件存在
echo.

REM 安装 PyMuPDF
echo [1/2] 正在安装 PyMuPDF...
pip install --no-index --find-links=offline_packages PyMuPDF
if %ERRORLEVEL% NEQ 0 (
    echo   [失败] PyMuPDF 安装失败
    pause
    exit /b 1
)
echo   [成功] PyMuPDF 安装完成
echo.

REM 安装 pywin32
echo [2/2] 正在安装 pywin32...
pip install --no-index --find-links=offline_packages pywin32
if %ERRORLEVEL% NEQ 0 (
    echo   [失败] pywin32 安装失败
    pause
    exit /b 1
)
echo   [成功] pywin32 安装完成
echo.

REM 验证安装
echo ========================================
echo 验证安装结果
echo ========================================
echo.

echo [验证 1/2] 测试 import fitz...
python -c "import fitz; print('  [成功] fitz (PyMuPDF) 可以正常导入')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo   [失败] fitz 导入失败
    pause
    exit /b 1
)

echo [验证 2/2] 测试 import win32com.client 和 pythoncom...
python -c "import win32com.client, pythoncom; print('  [成功] win32com.client 和 pythoncom 可以正常导入')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo   [失败] win32com/pythoncom 导入失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo [成功] 所有依赖安装并验证成功！
echo ========================================
echo.
echo 现在系统支持：
echo   ✓ PDF 文件检测和转换
echo   ✓ .doc/.xls/.ppt 文件转换（需本地安装 Microsoft Office）
echo.
echo 可以正常使用：
echo   - import fitz
echo   - import win32com.client
echo   - import pythoncom
echo.

pause
