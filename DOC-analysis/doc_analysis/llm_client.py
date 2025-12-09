# llm_client.py
import requests
from config import LLM_CONFIG  # 从配置文件导入大模型参数
from log import logger      # 从日志模块导入logger

def optimize_ocr_with_llm(ocr_text: str, img_name: str) -> tuple[str, bool]:
    """
    调用大模型优化OCR识别结果
    :param ocr_text: OCR原始文本
    :param img_name: 图片文件名（用于日志）
    :return: (优化后的文本, 是否调用失败)
    """
    if not ocr_text.strip():
        return ocr_text, False  # 空文本无需调用

    try:
        # 构造请求
        payload = {"question": ocr_text}
        response = requests.post(
            url=LLM_CONFIG["api_url"],
            headers=LLM_CONFIG["headers"],
            json=payload,
            timeout=LLM_CONFIG["timeout"]
        )
        response.raise_for_status()  # 触发HTTP错误

        # 解析响应（严格按返回格式提取）
        result = response.json()
        optimized_text = result.get("json", {}).get("answer", ocr_text)
        logger.info(f"大模型优化成功：{img_name}")
        return optimized_text, False

    except Exception as e:
        error_msg = str(e)
        logger.warning(f"大模型调用失败（{error_msg}），使用原始OCR结果：{img_name}")
        return ocr_text, True