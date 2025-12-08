@echo off
REM Windows 定时清理脚本
REM 说明：此脚本用于定时调用清理 API

echo ======================================
echo 文档检测系统 - 存储清理任务
echo ======================================
echo 执行时间: %date% %time%
echo.

REM 设置 API 地址和参数
set API_URL=http://localhost:8000/api/v1/storage/clean
set DAYS=7

echo 正在清理 %DAYS% 天前的文件...
echo API 地址: %API_URL%?days=%DAYS%
echo.

REM 调用清理 API
curl -X POST "%API_URL%?days=%DAYS%" -H "Content-Type: application/json"

echo.
echo ======================================
echo 清理任务完成
echo ======================================
echo.

REM 可选：记录日志
echo [%date% %time%] 清理任务执行完成 >> clean_storage.log

pause
