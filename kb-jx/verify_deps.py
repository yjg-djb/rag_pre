#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证依赖安装"""

print("=" * 60)
print("依赖安装验证")
print("=" * 60)

# 1. 检查 PyMuPDF
print("\n[1/3] 检查 PyMuPDF...")
try:
    import fitz
    print(f"✓ PyMuPDF 已安装 (版本: {fitz.__version__ if hasattr(fitz, '__version__') else '未知'})")
except ImportError:
    print("✗ PyMuPDF 未安装")

# 2. 检查 pywin32
print("\n[2/3] 检查 pywin32...")
try:
    import win32com.client
    import pythoncom
    print("✓ pywin32 已安装")
except ImportError as e:
    print(f"✗ pywin32 未安装: {e}")

# 3. 检查系统功能状态
print("\n[3/3] 检查系统功能...")
try:
    from services.detector import DocumentDetector
    from services.converter import DocumentConverter
    
    det = DocumentDetector()
    conv = DocumentConverter()
    
    print(f"  - Office COM 支持: {'✓ 已启用' if det._has_office_com else '✗ 未启用 (需要 Microsoft Office)'}")
    
    # 检查 PyMuPDF
    import services.detector as det_module
    has_pymupdf = hasattr(det_module, 'HAS_PYMUPDF') and det_module.HAS_PYMUPDF
    print(f"  - PDF 检测/转换: {'✓ 已启用' if has_pymupdf else '✗ 未启用 (需要安装 PyMuPDF)'}")
    
    # 检查 converter 的 fitz
    import services.converter as conv_module
    conv_has_fitz = hasattr(conv_module, 'fitz') and conv_module.fitz is not None
    print(f"  - PDF 转 DOCX: {'✓ 已启用' if conv_has_fitz else '✗ 未启用 (需要安装 PyMuPDF)'}")
    
except Exception as e:
    print(f"✗ 系统检查失败: {e}")

print("\n" + "=" * 60)
print("验证完成！")
print("=" * 60)
