#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
定时清理任务脚本
用于独立运行或作为定时任务执行
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.cleaner import StorageCleaner
from utils.logger import setup_logger

# 初始化日志
logger = setup_logger()


def main():
    """执行清理任务"""
    logger.info("=" * 60)
    logger.info("定时清理任务开始执行")
    logger.info("=" * 60)
    
    try:
        # 初始化清理器
        cleaner = StorageCleaner()
        
        # 执行清理（保留最近 7 天）
        days_to_keep = 0
        logger.info(f"清理参数: 保留最近 {days_to_keep} 天的文件")
        
        result = cleaner.clean_all(days=days_to_keep)
        
        # 输出结果
        logger.info("=" * 60)
        logger.info("清理结果统计:")
        logger.info(f"  批量任务: 删除 {result['batch_tasks']['deleted']} 个目录, "
                   f"释放 {result['batch_tasks']['total_size_mb']} MB")
        logger.info(f"  单文件: 删除 {result['single_files']['deleted']} 个文件, "
                   f"释放 {result['single_files']['total_size_mb']} MB")
        logger.info(f"  总计: 删除 {result['total_deleted']} 项, "
                   f"释放 {result['total_size_mb']} MB")
        logger.info(f"  错误数: {result['total_errors']}")
        logger.info("=" * 60)
        
        if result['total_deleted'] > 0:
            logger.info("✓ 清理任务成功完成")
            return 0
        else:
            logger.info("✓ 无需清理的文件")
            return 0
            
    except Exception as e:
        logger.error(f"✗ 清理任务失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
