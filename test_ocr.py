#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试OCR识别能力"""

import pyautogui

print("测试pyautogui的文本识别功能...")
print()

try:
    # 尝试使用locateOnText
    result = pyautogui.locateOnText("继续", confidence=0.7)
    if result:
        print(f"✅ OCR识别成功！找到'继续'位置: {result}")
    else:
        print("❌ OCR识别失败：未找到'继续'文本")
except Exception as e:
    print(f"❌ OCR识别发生错误: {e}")
    print()
    print("可能的原因：")
    print("  1. Tesseract OCR未安装")
    print("  2. Tesseract未添加到系统PATH")
    print("  3. pyautogui找不到Tesseract可执行文件")
    print()
    print("解决方案：")
    print("  方案1：安装Tesseract OCR")
    print("    - 下载地址：https://github.com/UB-Mannheim/tesseract/wiki")
    print("    - 安装后添加到PATH环境变量")
    print("  方案2：使用图像识别（locateOnScreen）代替文本识别")
