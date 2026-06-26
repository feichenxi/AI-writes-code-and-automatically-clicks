#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""截图工具 - 用于截取"继续"按钮图片"""

import pyautogui
import time

print("╔" + "═" * 58 + "╗")
print("║" + " " * 58 + "║")
print("║" + " " * 15 + "继续按钮截图工具" + " " * 19 + "║")
print("║" + " " * 58 + "║")
print("╚" + "═" * 58 + "╝")
print()

print("使用说明：")
print("  1. 程序启动后，会等待5秒")
print("  2. 请在这5秒内将鼠标移动到'继续'按钮上")
print("  3. 程序会自动截取按钮周围的区域")
print("  4. 保存为 continue_button.png")
print()

input("准备好后按回车键开始...")

print()
print("5秒后开始截图，请将鼠标移动到'继续'按钮上...")
for i in range(5, 0, -1):
    print(f"  {i}...")
    time.sleep(1)

# 获取鼠标位置
x, y = pyautogui.position()
print(f"\n当前鼠标位置: ({x}, {y})")

# 截取按钮周围区域（假设按钮大小约为 100x40）
button_width = 100
button_height = 40
left = x - button_width // 2
top = y - button_height // 2

# 确保不超出屏幕边界
screen_width, screen_height = pyautogui.size()
left = max(0, left)
top = max(0, top)
right = min(screen_width, left + button_width)
bottom = min(screen_height, top + button_height)

# 截图
screenshot = pyautogui.screenshot(region=(left, top, right - left, bottom - top))
screenshot.save("continue_button.png")

print(f"\n✅ 截图已保存到: continue_button.png")
print(f"   截图区域: ({left}, {top}, {right}, {bottom})")
print(f"   鼠标位置: ({x}, {y})")
print()
print("现在可以运行'继续点击.py'来使用这个截图进行识别")
