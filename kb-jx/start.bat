@echo off
chcp 65001 >nul
echo ====================================
echo 文档检测与批量处理系统 - 启动脚本
echo ====================================
echo.

echo 检查 Python 环境...
python --version
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo.
echo 检查依赖是否已安装...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 检测到依赖未安装，开始安装...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo [成功] 依赖安装完成
) else (
    echo [提示] 依赖已安装
)

echo.
echo ====================================
echo 启动服务...
echo ====================================
echo.
echo 服务地址: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo ====================================
echo.

python main.py

pause
