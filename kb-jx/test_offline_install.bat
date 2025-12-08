@echo off
REM ========================================
REM 测试离线依赖安装
REM ========================================

echo ========================================
echo 测试 PyMuPDF 和 pywin32 离线安装
echo ========================================
echo.

REM 检查离线包
echo [1/5] 检查离线包文件...
if exist "offline_packages\PyMuPDF-1.23.8-cp310-none-win_amd64.whl" (
    echo   [✓] PyMuPDF-1.23.8 存在
) else (
    echo   [✗] PyMuPDF-1.23.8 不存在
)

if exist "offline_packages\PyMuPDFb-1.23.7-py3-none-win_amd64.whl" (
    echo   [✓] PyMuPDFb-1.23.7 存在
) else (
    echo   [✗] PyMuPDFb-1.23.7 不存在
)

if exist "offline_packages\pywin32-311-cp310-cp310-win_amd64.whl" (
    echo   [✓] pywin32-311 存在
) else (
    echo   [✗] pywin32-311 不存在
)
echo.

REM 安装 PyMuPDF
echo [2/5] 安装 PyMuPDF...
pip install --no-index --find-links=offline_packages PyMuPDF
if %ERRORLEVEL% NEQ 0 (
    echo   [✗] PyMuPDF 安装失败
    pause
    exit /b 1
)
echo   [✓] PyMuPDF 安装成功
echo.

REM 安装 pywin32
echo [3/5] 安装 pywin32...
pip install --no-index --find-links=offline_packages pywin32
if %ERRORLEVEL% NEQ 0 (
    echo   [✗] pywin32 安装失败
    pause
    exit /b 1
)
echo   [✓] pywin32 安装成功
echo.

REM 验证 fitz
echo [4/5] 验证 import fitz...
python -c "import fitz; print(f'  [✓] fitz (PyMuPDF) 导入成功')"
if %ERRORLEVEL% NEQ 0 (
    echo   [✗] fitz 导入失败
    pause
    exit /b 1
)

REM 验证 win32com 和 pythoncom
echo [5/5] 验证 win32com 和 pythoncom...
python -c "import win32com.client; import pythoncom; print('  [✓] win32com.client 和 pythoncom 导入成功')"
if %ERRORLEVEL% NEQ 0 (
    echo   [✗] win32com/pythoncom 导入失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo [✓] 所有依赖安装和验证成功！
echo ========================================
echo.
echo 现在可以在内网环境使用：
echo   - import fitz
echo   - import win32com.client
echo   - import pythoncom
echo.
echo 系统已支持：
echo   - PDF 文件检测和转换
echo   - .doc/.xls/.ppt 文件转换（需本地安装 Office）
echo.

pause
