@echo off
REM ========================================
REM 文档检测与批量处理系统 - 离线安装脚本
REM ========================================

echo ========================================
echo 文档检测与批量处理系统
echo 离线部署安装
echo ========================================
echo.

REM 检查 Python 版本
echo [1/5] 检查 Python 环境...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

python --version
echo.

REM 升级 pip
echo [2/5] 升级 pip...
python -m pip install --upgrade pip --no-index --find-links=offline_packages
echo.

REM 安装依赖包
echo [3/5] 安装依赖包...
pip install --no-index --find-links=offline_packages -r requirements.txt
echo.

REM 验证核心依赖
echo [4/5] 验证核心依赖...
python -c "import fastapi; import uvicorn; import docx; import openpyxl; import pptx; print('[OK] 核心依赖安装成功')"
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 核心依赖安装失败，请检查错误信息
    pause
    exit /b 1
)

REM 验证可选依赖（PyMuPDF 和 pywin32）
echo [5/5] 验证可选依赖...
echo   - 检查 PyMuPDF (fitz)...
python -c "import fitz; print('     [OK] PyMuPDF 已安装')"
if %ERRORLEVEL% NEQ 0 (
    echo      [提示] PyMuPDF 未安装，PDF 功能将不可用
)

echo   - 检查 pywin32 (win32com)...
python -c "import win32com.client, pythoncom; print('     [OK] pywin32 已安装')"
if %ERRORLEVEL% NEQ 0 (
    echo      [提示] pywin32 未安装，旧格式(.doc/.xls/.ppt)转换将不可用
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 启动命令:
echo   python main.py
echo.
echo 访问地址:
echo   http://localhost:8000
echo   http://localhost:8000/upload
echo   http://localhost:8000/docs
echo.
echo ========================================

pause
