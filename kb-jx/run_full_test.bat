@echo off
REM ========================================
REM 完整功能测试
REM ========================================

echo ========================================
echo 文档检测系统 - 完整功能测试
echo ========================================
echo.

echo [测试 1/6] Python 环境...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo   [失败] Python 未安装
    pause
    exit /b 1
)
echo   [成功]
echo.

echo [测试 2/6] 核心依赖...
python -c "import fastapi, uvicorn, docx, openpyxl, pptx; print('  [成功] 核心依赖正常')"
if %ERRORLEVEL% NEQ 0 (
    echo   [失败] 请先运行 install_offline.bat
    pause
    exit /b 1
)
echo.

echo [测试 3/6] PyMuPDF (fitz)...
python -c "import fitz; print('  [成功] PyMuPDF 已安装')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo   [提示] PyMuPDF 未安装，PDF 功能不可用
    echo          运行 install_pdf_support.bat 安装
) else (
    echo   [成功] PDF 功能可用
)
echo.

echo [测试 4/6] pywin32 (win32com)...
python -c "import win32com.client, pythoncom; print('  [成功] pywin32 已安装')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo   [提示] pywin32 未安装，旧格式转换不可用
    echo          运行 install_pdf_support.bat 安装
) else (
    echo   [成功] 旧格式转换功能可用
)
echo.

echo [测试 5/6] 导入检测器和转换器...
python -c "from services.detector import DocumentDetector; from services.converter import DocumentConverter; print('  [成功] 核心模块导入正常')"
if %ERRORLEVEL% NEQ 0 (
    echo   [失败] 核心模块导入失败
    pause
    exit /b 1
)
echo.

echo [测试 6/6] 功能状态检查...
python verify_deps.py
echo.

echo ========================================
echo 测试完成
echo ========================================
echo.
echo 下一步：
echo   启动服务: python main.py
echo   访问地址: http://localhost:8000/upload
echo.

pause
