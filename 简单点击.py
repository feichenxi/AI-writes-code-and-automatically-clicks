#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单点击工具 - 直接点击指定坐标
"""

import time
import pyautogui

print("╔" + "═" * 58 + "╗")
print("║" + " " * 58 + "║")
print("║" + " " * 18 + "简单点击工具" + " " * 22 + "║")
print("║" + " " * 58 + "║")
print("╚" + "═" * 58 + "╝")
print()

print("使用说明：")
print("  1. 将鼠标移动到'继续'按钮上")
print("  2. 查看鼠标坐标（程序会显示）")
print("  3. 输入坐标开始自动点击")
print()

print("移动鼠标到目标位置，按回车键查看坐标...")
input()

x, y = pyautogui.position()
print(f"\n当前鼠标坐标: ({x}, {y})")
print()

while True:
    print("=" * 60)
    print("请选择操作：")
    print("=" * 60)
    print(f"  当前坐标: ({x}, {y})")
    print("  1. 测试点击当前坐标")
    print("  2. 修改坐标")
    print("  3. 开始自动监控点击")
    print("  4. 退出")
    print("=" * 60)
    
    choice = input("\n请输入选项 (1-4): ").strip()
    
    if choice == '1':
        print(f"\n正在点击 ({x}, {y})...")
        pyautogui.click(x, y)
        print("✅ 点击完成！")
        
    elif choice == '2':
        new_x = input(f"输入X坐标 (当前: {x}): ").strip()
        new_y = input(f"输入Y坐标 (当前: {y}): ").strip()
        
        if new_x:
            x = int(new_x)
        if new_y:
            y = int(new_y)
        print(f"\n坐标已更新为: ({x}, {y})")
        
    elif choice == '3':
        interval = input("输入扫描间隔（秒，默认1）: ").strip()
        interval = float(interval) if interval else 1
        
        print(f"\n开始监控点击 ({x}, {y})，间隔 {interval} 秒")
        print("按 Ctrl+C 停止")
        print()
        
        try:
            while True:
                pyautogui.click(x, y)
                print(f"[{time.strftime('%H:%M:%S')}] ✅ 点击 ({x}, {y})")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n已停止监控")
            
    elif choice == '4':
        print("\n再见！")
        break
        
    else:
        print("\n无效选项！")
