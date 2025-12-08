@echo off
REM ========================================
REM kb-jx 内网部署完整性检查脚本
REM ========================================

echo.
echo ========================================
echo kb-jx 内网部署完整性检查
echo ========================================
echo.

set ERROR_COUNT=0

REM ============================================
REM 1. 检查 Python 环境
REM ============================================
echo [1/10] 检查 Python 环境...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   [失败] Python 未安装或未添加到 PATH
    set /a ERROR_COUNT+=1
) else (
    python --version
    echo   [通过] Python 环境正常
)
echo.

REM ============================================
REM 2. 检查核心文件
REM ============================================
echo [2/10] 检查核心文件...
set FILES_OK=1

if not exist "main.py" (
    echo   [缺失] main.py
    set FILES_OK=0
)
if not exist "config.py" (
    echo   [缺失] config.py
    set FILES_OK=0
)
if not exist "requirements.txt" (
    echo   [缺失] requirements.txt
    set FILES_OK=0
)
if not exist ".env" (
    echo   [缺失] .env
    set FILES_OK=0
)
if not exist "api\v1\endpoints.py" (
    echo   [缺失] api\v1\endpoints.py
    set FILES_OK=0
)
if not exist "services\converter.py" (
    echo   [缺失] services\converter.py
    set FILES_OK=0
)
if not exist "utils\logger.py" (
    echo   [缺失] utils\logger.py
    set FILES_OK=0
)

if %FILES_OK%==1 (
    echo   [通过] 核心文件齐全
) else (
    echo   [失败] 存在缺失文件
    set /a ERROR_COUNT+=1
)
echo.

REM ============================================
REM 3. 检查离线依赖包
REM ============================================
echo [3/10] 检查离线依赖包...
if not exist "offline_packages" (
    echo   [失败] offline_packages 目录不存在
    set /a ERROR_COUNT+=1
) else (
    for /f %%i in ('dir /b offline_packages\*.whl ^| find /c /v ""') do set WHL_COUNT=%%i
    echo   [信息] 找到 %WHL_COUNT% 个 wheel 包 (预期: 38)
    if %WHL_COUNT% LSS 30 (
        echo   [警告] 依赖包数量可能不足
        set /a ERROR_COUNT+=1
    ) else (
        echo   [通过] 离线依赖包齐全
    )
)
echo.

REM ============================================
REM 4. 检查 LibreOffice 便携版
REM ============================================
echo [4/10] 检查 LibreOffice 便携版...
if not exist "tool\LibreOfficePortable\App\libreoffice\program\soffice.exe" (
    echo   [失败] LibreOffice 便携版未找到
    echo   [提示] 旧格式文档(.doc/.xls/.ppt)转换将不可用
    set /a ERROR_COUNT+=1
) else (
    echo   [通过] LibreOffice 便携版已安装
    REM 尝试获取版本
    "tool\LibreOfficePortable\App\libreoffice\program\soffice.exe" --version 2>nul
)
echo.

REM ============================================
REM 5. 检查 Redis 配置（可选）
REM ============================================
echo [5/10] 检查 Redis 配置...
findstr "REDIS_ENABLED=true" .env >nul 2>&1
if %ERRORLEVEL%==0 (
    echo   [信息] Redis 已启用
    netstat -ano | findstr ":6379" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo   [警告] Redis 服务未运行（端口 6379 未监听）
        echo   [提示] 系统将使用内存模式，重启后去重记录丢失
    ) else (
        echo   [通过] Redis 服务正在运行
    )
) else (
    echo   [信息] Redis 已禁用，将使用内存模式
)
echo.

REM ============================================
REM 6. 检查端口占用
REM ============================================
echo [6/10] 检查端口占用...
for /f "tokens=2 delims==" %%i in ('findstr "^APP_PORT=" .env 2^>nul') do set PORT=%%i
if "%PORT%"=="" set PORT=8000

netstat -ano | findstr ":%PORT%" | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo   [警告] 端口 %PORT% 已被占用
    netstat -ano | findstr ":%PORT%" | findstr "LISTENING"
    echo   [提示] 需要修改 .env 中的 APP_PORT 或停止占用进程
) else (
    echo   [通过] 端口 %PORT% 可用
)
echo.

REM ============================================
REM 7. 检查磁盘空间
REM ============================================
echo [7/10] 检查磁盘空间...
for %%i in ("%CD%") do set DRIVE=%%~di
for /f "tokens=3" %%a in ('dir /-c %DRIVE%\ ^| findstr "bytes free"') do set FREE_BYTES=%%a
set FREE_BYTES=%FREE_BYTES:,=%
set /a FREE_MB=%FREE_BYTES:~0,-6%
echo   [信息] 可用空间: %FREE_MB% MB
if %FREE_MB% LSS 1000 (
    echo   [警告] 磁盘空间不足 1 GB
    set /a ERROR_COUNT+=1
) else (
    echo   [通过] 磁盘空间充足
)
echo.

REM ============================================
REM 8. 检查必需目录权限
REM ============================================
echo [8/10] 检查目录权限...
set PERM_OK=1

REM 尝试创建临时目录
if not exist "storage" mkdir storage 2>nul
if not exist "storage\temp" mkdir storage\temp 2>nul
if not exist "logs" mkdir logs 2>nul

REM 测试写入权限
echo test > storage\temp\_test.txt 2>nul
if exist "storage\temp\_test.txt" (
    del storage\temp\_test.txt
    echo   [通过] storage 目录可写
) else (
    echo   [失败] storage 目录无写入权限
    set PERM_OK=0
    set /a ERROR_COUNT+=1
)

echo test > logs\_test.txt 2>nul
if exist "logs\_test.txt" (
    del logs\_test.txt
) else (
    echo   [失败] logs 目录无写入权限
    set PERM_OK=0
    set /a ERROR_COUNT+=1
)

if %PERM_OK%==1 (
    if not exist "storage\temp\_test.txt" (
        REM 上面已删除
    )
)
echo.

REM ============================================
REM 9. 检查 Python 依赖（如已安装）
REM ============================================
echo [9/10] 检查 Python 依赖（如已安装）...
python -c "import sys; sys.exit(0)" 2>nul
if %ERRORLEVEL%==0 (
    python -c "import fastapi; print('  [OK] FastAPI 已安装 -', fastapi.__version__)" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo   [提示] 依赖未安装，请运行 install_offline.bat
    )
    
    python -c "import uvicorn; print('  [OK] Uvicorn 已安装 -', uvicorn.__version__)" 2>nul
    python -c "import docx; print('  [OK] python-docx 已安装 -', docx.__version__)" 2>nul
    python -c "import fitz; print('  [OK] PyMuPDF 已安装 -', fitz.version)" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo   [警告] PyMuPDF 未安装，PDF 功能将不可用
    )
    
    python -c "import win32com.client; print('  [OK] pywin32 已安装')" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo   [提示] pywin32 未安装，但有 LibreOffice 作为后备
    )
)
echo.

REM ============================================
REM 10. 检查配置文件有效性
REM ============================================
echo [10/10] 检查配置文件有效性...
python -c "from config import config; assert config.validate(), 'Config validation failed'; print('  [通过] 配置文件有效')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo   [失败] 配置文件验证失败
    python -c "from config import config; config.validate()" 2>&1
    set /a ERROR_COUNT+=1
) else (
    python -c "from config import config; config.validate()" 2>nul
)
echo.

REM ============================================
REM 总结
REM ============================================
echo ========================================
if %ERROR_COUNT%==0 (
    echo 检查结果: 全部通过 ^(0 个错误^)
    echo ========================================
    echo.
    echo [下一步操作]
    echo 1. 如依赖未安装，运行: install_offline.bat
    echo 2. 如需验证安装，运行: verify_install.bat
    echo 3. 启动服务: start.bat
    echo 4. 访问页面: http://localhost:%PORT%/upload
    echo.
) else (
    echo 检查结果: 发现 %ERROR_COUNT% 个问题
    echo ========================================
    echo.
    echo [修复建议]
    echo 1. 查看上方错误提示
    echo 2. 补充缺失文件或依赖
    echo 3. 重新运行此脚本验证
    echo.
)

echo ========================================
echo 详细部署指南请查看: 内网部署完整检查清单.md
echo ========================================
echo.

pause
