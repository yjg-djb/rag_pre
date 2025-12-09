import json
import os
import requests
import logging
import base64  # 新增：用于base64编码
from typing import List, Optional, Tuple  # 新增：Tuple类型
# third_ocr_caseA.py
# -------------------------- 可配置参数（后续修改集中在这里） --------------------------
# 第三方OCR单张接口URL（需替换为实际地址）
THIRD_OCR_SINGLE_URL = "http://25.18.122.72:10000/OCR04"
# 第三方接口接收的参数名（需确认：base64字段名/名称字段名，此处为通用占位符）
THIRD_OCR_BASE64_PARAM = "base64"  # 新增：第三方接收base64的参数名
THIRD_OCR_NAME_PARAM = "fileName"      # 新增：第三方接收名称的参数名
# 第三方接口成功返回的retMsg（明确为"success"）
THIRD_OCR_RETMSG_SUCCESS = "success"
# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ocr_logs.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# -------------------------- 单张图片OCR调用（核心逻辑） --------------------------
# 修改点1：新增img_name参数
def _call_single_ocr(img_path: str, img_name: str) -> List:
    """
    调用第三方单张OCR接口（base64+名称传参），适配情况A：无generalTextList字段即视为无文本
    :param img_path: 单张图片路径
    :param img_name: 单张图片名称（传给第三方接口）
    :return: 单张图片的适配结果（[[坐标, [文本]], ...]），无结果则返回空列表
    """
    # 1. 读取图片二进制（处理图片读取错误）
    if not os.path.exists(img_path):
        logger.error(f"图片路径不存在：{img_path}")
        return []
    try:
        with open(img_path, "rb") as f:
            img_bytes = f.read()
        # 修改点2：二进制转base64（去除前缀，仅保留编码）
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    except Exception as e:
        logger.error(f"读取图片/转base64失败：{img_path}，错误原因：{str(e)}")
        return []

    # 2. 调用第三方OCR接口（处理接口请求错误）
    try:
        # 修改点3：构造json参数（替代原files参数）
        json_data = {
            THIRD_OCR_NAME_PARAM: img_name,    # 图片名称
            THIRD_OCR_BASE64_PARAM: img_base64 # 图片base64编码
        }
        # 修改点4：post请求改为json传参
        response = requests.post(
            THIRD_OCR_SINGLE_URL,
            json=json_data,  # 替代files=...
            timeout=30
        )
        response.raise_for_status()


        third_result = json.loads(response.json())
        print(f"{type(third_result)}")
        # third_result = response.json()
        # print(f"报错钱{type(third_result)}")
    except requests.exceptions.RequestException as e:
        logger.error(f"调用第三方OCR接口失败：{img_path}，错误原因：{str(e)}")
        return []

    # 3. 解析第三方结果（后续逻辑与原版本一致，无修改）
    img_adapted = []
    ret_list = third_result.get("sysHead", {}).get("ret", [])
    if not ret_list:
        logger.error(f"第三方OCR返回格式异常：{img_path}，sysHead.ret列表为空")
        return []
    ret_msg = ret_list[0].get("retMsg", "")
    ret_code = ret_list[0].get("retCode", "未知错误码")

    if ret_msg != THIRD_OCR_RETMSG_SUCCESS:
        error_msg = ret_list[0].get("retMsg", "未知错误")
        logger.error(f"第三方OCR识别失败：{img_path}，错误码：{ret_code}，错误信息：{error_msg}")
        return []

    body_data = third_result.get("body", {}).get("data", [{}])[0]
    if "generalTextList" not in body_data:
        logger.info(f"图片无文本识别结果（情况A）：{img_path}")
        return []

    general_text_list = body_data.get("generalTextList", [])
    for text_block in general_text_list:
        coords = text_block.get("coords", [])
        if len(coords) != 4:
            logger.warning(f"图片{img_path}的文本块坐标异常，跳过：{coords}")
            continue
        try:
            converted_coords = [[int(c["x"]), int(c["y"])] for c in coords]
        except (KeyError, ValueError) as e:
            logger.warning(f"图片{img_path}的坐标格式错误，跳过：{coords}，错误：{str(e)}")
            continue
        text = text_block.get("value", "").strip()
        if not text:
            logger.warning(f"图片{img_path}的文本块为空，跳过")
            continue
        img_adapted.append([converted_coords, [text]])
    return img_adapted

# -------------------------- 批量图片OCR调用（串行循环） --------------------------
# 修改点5：入参改为(路径, 名称)元组列表
def batch_ocr(img_info_list: List[Tuple[str, str]]) -> List[List]:
    """
    批量处理图片OCR（base64+名称传参）
    :param img_info_list: 图片信息列表，每个元素为(图片路径, 图片名称)元组
    :return: 批量适配结果（外层列表=图片列表，内层=单张图片结果）
    """
    if not isinstance(img_info_list, list) or len(img_info_list) == 0:
        logger.error("批量OCR输入错误：图片信息列表为空或非列表类型")
        return []

    batch_result = []
    logger.info(f"开始批量OCR识别，共{len(img_info_list)}张图片")
    for idx, (img_path, img_name) in enumerate(img_info_list, 1):  # 修改点6：解包元组
        logger.info(f"正在处理第{idx}/{len(img_info_list)}张图片：路径={img_path}，名称={img_name}")
        # 修改点7：调用单张函数时传入名称
        single_result = _call_single_ocr(img_path, img_name)
        batch_result.append(single_result)
    logger.info(f"批量OCR识别完成，共{len(img_info_list)}张图片")
    return batch_result

if __name__ == '__main__':
    # 测试代码（可临时添加到脚本末尾）
    if __name__ == "__main__":
        test_img_path = "path/to/你的测试图片.png"  # 替换为实际图片路径
        test_img_name = "测试图片.png"
        result = _call_single_ocr(test_img_path, test_img_name)
        print("OCR识别结果：", result)