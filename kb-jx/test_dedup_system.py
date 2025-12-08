#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试去重与清洗系统
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.dedup_store import DedupStore, compute_sha256
from services.text_pipeline import TextPipeline
from utils.logger import setup_logger

# 初始化日志
logger = setup_logger()


def test_redis_connection():
    """测试 Redis 连接"""
    print("=" * 60)
    print("测试 1: Redis 连接")
    print("=" * 60)
    
    redis_config = {
        "host": "127.0.0.1",
        "port": 6379,
        "db": 1,
        "password": "123456"
    }
    
    try:
        dedup_store = DedupStore(backend="redis", redis_config=redis_config)
        
        # 获取统计
        stats = dedup_store.get_stats()
        print(f"✓ Redis 连接成功")
        print(f"  当前统计: {stats}")
        
        return dedup_store
    except Exception as e:
        print(f"✗ Redis 连接失败: {e}")
        return None


def test_text_pipeline(dedup_store):
    """测试文本管线"""
    print("\n" + "=" * 60)
    print("测试 2: 文本清洗与去重管线")
    print("=" * 60)
    
    if dedup_store is None:
        print("跳过（Redis 未连接）")
        return
    
    # 初始化文本管线
    pipeline = TextPipeline(
        dedup_store=dedup_store,
        min_paragraph_len=10,
        simhash_distance_threshold=3,
        enable_near_duplicate=True
    )
    
    # 测试文本（包含噪声、重复段落）
    test_text = """
这是第一段测试文本。

这是第二段测试文本，包含噪声: https://example.com/test 和 email@test.com

这是第一段测试文本。

这是第三段测试文本，包含页码标记：第 3 页

这是第四段测试文本。

这是第一段测试文本。
"""
    
    print(f"\n原始文本长度: {len(test_text)} 字符")
    double_newline = '\n\n'
    print(f"原始段落数: {len([p for p in test_text.split(double_newline) if p.strip()])}")
    
    # 处理文本
    result = pipeline.process(test_text, doc_name="test_doc_1")
    
    print(f"\n处理结果:")
    print(f"  成功: {result['success']}")
    print(f"  文档去重: {result['doc_duplicate']}")
    print(f"  清洗后长度: {len(result['cleaned_text'])} 字符")
    
    stats = result['stats']
    print(f"\n详细统计:")
    print(f"  原始长度: {stats['original_length']}")
    print(f"  规范化后: {stats['normalized_length']}")
    print(f"  噪声移除: {stats['noise_removed_count']} 处")
    print(f"  原始段落: {stats['paragraphs_original']}")
    print(f"  精确重复: {stats['paragraphs_exact_dup']}")
    print(f"  近重复: {stats['paragraphs_near_dup']}")
    print(f"  过短段落: {stats['paragraphs_too_short']}")
    print(f"  最终段落: {stats['paragraphs_after_dedup']}")
    
    # 再次处理相同文本（应该命中文档去重）
    print("\n" + "-" * 60)
    print("测试文档去重（相同文本）")
    print("-" * 60)
    
    result2 = pipeline.process(test_text, doc_name="test_doc_2")
    print(f"  成功: {result2['success']}")
    print(f"  文档去重命中: {result2['doc_duplicate']}")
    print(f"  消息: {result2['message']}")


def test_dedup_store_stats(dedup_store):
    """测试去重存储统计"""
    print("\n" + "=" * 60)
    print("测试 3: 去重存储统计")
    print("=" * 60)
    
    if dedup_store is None:
        print("跳过（Redis 未连接）")
        return
    
    stats = dedup_store.get_stats()
    print(f"  文档哈希数: {stats['doc_count']}")
    print(f"  段落哈希数: {stats['para_count']}")
    print(f"  SimHash 数: {stats['simhash_count']}")


def test_dependencies():
    """测试依赖库"""
    print("\n" + "=" * 60)
    print("测试 4: 依赖库检查")
    print("=" * 60)
    
    deps = {
        "redis": "Redis 客户端",
        "ftfy": "Unicode 修复",
        "simhash": "近重复检测"
    }
    
    for module, desc in deps.items():
        try:
            __import__(module)
            print(f"  ✓ {desc} ({module})")
        except ImportError:
            print(f"  ✗ {desc} ({module}) - 未安装")


def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("文档去重与清洗系统 - 功能测试")
    print("=" * 60)
    
    # 测试依赖
    test_dependencies()
    
    # 测试 Redis 连接
    dedup_store = test_redis_connection()
    
    # 测试文本管线
    test_text_pipeline(dedup_store)
    
    # 测试统计
    test_dedup_store_stats(dedup_store)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    # 可选：清空测试数据
    if dedup_store:
        choice = input("\n是否清空测试数据？(y/n): ")
        if choice.lower() == 'y':
            dedup_store.clear_all()
            print("✓ 测试数据已清空")


if __name__ == "__main__":
    main()
