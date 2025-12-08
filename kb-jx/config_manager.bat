@echo off
REM ========================================
REM 配置管理脚本
REM ========================================

echo ========================================
echo 文档检测系统 - 配置管理
echo ========================================
echo.

:menu
echo 请选择操作：
echo   1. 查看当前配置
echo   2. 验证配置
echo   3. 生成环境变量文件
echo   4. 退出
echo.
set /p choice=请输入选项 (1-4): 

if "%choice%"=="1" goto view_config
if "%choice%"=="2" goto validate_config
if "%choice%"=="3" goto generate_env
if "%choice%"=="4" goto end
echo 无效选项，请重新选择
echo.
goto menu

:view_config
echo.
echo [查看当前配置]
python config.py
echo.
pause
goto menu

:validate_config
echo.
echo [验证配置]
python -c "from config import config; result = config.validate(); print('✓ 配置验证通过' if result else '✗ 配置验证失败')"
echo.
pause
goto menu

:generate_env
echo.
echo [生成环境变量文件]
if exist .env (
    echo .env 文件已存在，是否覆盖？(y/n^)
    set /p overwrite=
    if not "%overwrite%"=="y" (
        echo 已取消
        pause
        goto menu
    )
)
copy .env.example .env
echo ✓ 已生成 .env 文件，请根据实际情况修改
echo.
pause
goto menu

:end
echo.
echo 再见！
