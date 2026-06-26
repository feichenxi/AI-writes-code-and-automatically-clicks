#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows错误完全处理工具 v2.0
功能：
1. 注册表系统级错误抑制（从源头禁用错误报告）
2. 常驻进程窗口级抑制（实时监控并自动关闭错误窗口）
3. 注册表恢复功能（隐藏功能）
"""

import os
import subprocess
import winreg
import time
import threading
import ctypes
from ctypes import wintypes
import logging
from logging.handlers import RotatingFileHandler
import msvcrt
import sys

# 配置日志（文件最大1MB，超过自动清理）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'error_handler.log', 
            maxBytes=1*1024*1024,  # 1MB
            backupCount=1,  # 保留1个备份文件
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_display_width(text):
    """精确计算字符串的显示宽度（考虑中文、emoji等）"""
    width = 0
    i = 0
    while i < len(text):
        char = text[i]
        code = ord(char)
        
        # 跳过零宽度字符（变体选择器等）
        if 0xFE00 <= code <= 0xFE0F or code == 0x200D:  # 变体选择器和零宽连接符
            i += 1
            continue
            
        # CJK统一汉字、CJK符号、全角字符
        if (0x4E00 <= code <= 0x9FFF or      # CJK统一汉字
            0x3000 <= code <= 0x303F or      # CJK符号和标点
            0xFF00 <= code <= 0xFFEF or      # 全角ASCII
            0x3400 <= code <= 0x4DBF or      # CJK扩展A
            0x20000 <= code <= 0x2A6DF or    # CJK扩展B
            0x2A700 <= code <= 0x2B73F or    # CJK扩展C
            0x2B740 <= code <= 0x2B81F or    # CJK扩展D
            0x2B820 <= code <= 0x2CEAF):     # CJK扩展E
            width += 2
        # Emoji和特殊符号（宽字符）
        elif (0x1F000 <= code <= 0x1FFFF or  # 各种符号和象形文字
              0x2600 <= code <= 0x27BF or     # 杂项符号和装饰符号
              0x2300 <= code <= 0x23FF or     # 杂项技术符号
              0x2B00 <= code <= 0x2BFF or     # 杂项符号和箭头
              0x1F900 <= code <= 0x1F9FF):    # 补充符号和象形文字
            width += 2
            # 检查是否有变体选择器跟随
            if i + 1 < len(text) and 0xFE00 <= ord(text[i + 1]) <= 0xFE0F:
                i += 1  # 跳过变体选择器
        # 制表符
        elif char == '\t':
            width += 4
        # 普通半角字符
        else:
            width += 1
        
        i += 1
    
    return width


def pad_to_width(text, target_width=58):
    """将文本填充到指定宽度，右侧用空格补齐"""
    current_width = get_display_width(text)
    if current_width < target_width:
        return text + ' ' * (target_width - current_width)
    return text


class RegistryErrorSuppressor:
    """注册表错误抑制器 - 系统级抑制"""
    
    def __init__(self):
        self.requires_admin = True
        
    def is_admin(self):
        """检查是否以管理员权限运行"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def set_registry_value(self, key_path, value_name, value_data, value_type=winreg.REG_DWORD):
        """设置注册表值"""
        try:
            if "HKEY_LOCAL_MACHINE" in key_path:
                root = winreg.HKEY_LOCAL_MACHINE
                key_path = key_path.replace("HKEY_LOCAL_MACHINE\\", "")
            else:
                root = winreg.HKEY_CURRENT_USER
                key_path = key_path.replace("HKEY_CURRENT_USER\\", "")
            
            key = winreg.CreateKey(root, key_path)
            winreg.SetValueEx(key, value_name, 0, value_type, value_data)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            logger.warning(f"设置注册表失败: {e}")
            return False
    
    def disable_windows_error_reporting(self):
        """禁用Windows错误报告"""
        settings = {
            # 完全禁用Windows错误报告
            r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\Windows Error Reporting": [
                ("Disabled", 1, winreg.REG_DWORD),
                ("DontShowUI", 1, winreg.REG_DWORD),
                ("DontSendAdditionalData", 1, winreg.REG_DWORD),
            ],
            # 禁用特定程序的错误报告
            r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\Windows Error Reporting\Consent": [
                ("DefaultConsent", 2, winreg.REG_DWORD)  # 2 = 从不发送报告
            ],
            # 用户级设置
            r"HKEY_CURRENT_USER\Software\Microsoft\Windows\Windows Error Reporting": [
                ("Disabled", 1, winreg.REG_DWORD),
                ("DontShowUI", 1, winreg.REG_DWORD)
            ],
            r"HKEY_CURRENT_USER\Software\Microsoft\Windows\Windows Error Reporting\Consent": [
                ("DefaultConsent", 2, winreg.REG_DWORD)
            ]
        }
        
        success_count = 0
        for key_path, values in settings.items():
            for value_name, value_data, value_type in values:
                if self.set_registry_value(key_path, value_name, value_data, value_type):
                    success_count += 1
                    logger.info(f"  ✓ 已设置: {value_name}")
        
        return success_count
    
    def suppress_vc_runtime_errors(self):
        """屏蔽VC++运行时错误"""
        settings = {
            # 禁用Visual C++运行时错误对话框（64位）
            r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AeDebug": [
                ("Auto", 0, winreg.REG_DWORD),  # 禁用自动调试
            ],
            # 针对32位程序的设置
            r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\AeDebug": [
                ("Auto", 0, winreg.REG_DWORD),
            ]
        }
        
        success_count = 0
        for key_path, values in settings.items():
            for value_name, value_data, value_type in values:
                if self.set_registry_value(key_path, value_name, value_data, value_type):
                    success_count += 1
                    logger.info(f"  ✓ 已设置: {value_name}")
        
        return success_count
    
    def suppress_for_common_modules(self):
        """为常见运行库模块添加错误抑制"""
        common_modules = [
            "MSVCR100.dll", "MSVCR110.dll", "MSVCR120.dll", 
            "MSVCR140.dll", "MSVCR150.dll", "VCRUNTIME140.dll", 
            "MSVCP100.dll", "MSVCP110.dll", "MSVCP120.dll", "MSVCP140.dll",
            "api-ms-win-crt-runtime-l1-1-0.dll",
            "ucrtbase.dll", "concrt140.dll", "vccorlib140.dll"
        ]
        
        base_path = r"SOFTWARE\Microsoft\Windows\Windows Error Reporting\ExcludedApplications"
        success_count = 0
        
        for module in common_modules:
            try:
                # 尝试HKEY_LOCAL_MACHINE
                try:
                    key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, base_path)
                    winreg.SetValueEx(key, module, 0, winreg.REG_DWORD, 1)
                    winreg.CloseKey(key)
                    success_count += 1
                except:
                    # 尝试HKEY_CURRENT_USER
                    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_path)
                    winreg.SetValueEx(key, module, 0, winreg.REG_DWORD, 1)
                    winreg.CloseKey(key)
                    success_count += 1
            except:
                pass
        
        logger.info(f"  ✓ 已为 {success_count} 个运行库模块添加抑制")
        return success_count
    
    def stop_error_reporting_service(self):
        """停止Windows错误报告服务"""
        try:
            # 停止服务
            subprocess.run(
                ["sc", "stop", "WerSvc"], 
                capture_output=True, 
                timeout=10,
                text=True
            )
            
            # 禁用服务
            subprocess.run(
                ["sc", "config", "WerSvc", "start=", "disabled"], 
                capture_output=True, 
                timeout=10,
                text=True
            )
            
            logger.info("  ✓ 已停止并禁用Windows错误报告服务")
            return True
        except:
            return False
    
    def apply_all_suppressions(self):
        """应用所有错误抑制设置"""
        logger.info("=" * 60)
        logger.info("开始应用系统级错误抑制...")
        logger.info("=" * 60)
        
        if not self.is_admin():
            logger.error("⚠ 需要管理员权限！请右键选择'以管理员身份运行'")
            return False
        
        total_success = 0
        
        logger.info("\n1. 禁用Windows错误报告...")
        total_success += self.disable_windows_error_reporting()
        
        logger.info("\n2. 屏蔽VC++运行时错误...")
        total_success += self.suppress_vc_runtime_errors()
        
        logger.info("\n3. 为常见运行库模块添加抑制...")
        total_success += self.suppress_for_common_modules()
        
        logger.info("\n4. 停止错误报告服务...")
        self.stop_error_reporting_service()
        
        logger.info("\n" + "=" * 60)
        logger.info(f"系统级抑制完成！成功应用 {total_success} 项设置")
        logger.info("建议重启系统以确保所有设置完全生效")
        logger.info("=" * 60)
        
        return total_success > 0

    def restore_defaults(self):
        """恢复默认设置"""
        logger.info("=" * 60)
        logger.info("开始恢复注册表默认设置...")
        logger.info("=" * 60)
        
        if not self.is_admin():
            logger.error("⚠ 需要管理员权限！请右键选择'以管理员身份运行'")
            return False
        
        restore_settings = {
            r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\Windows Error Reporting": [
                ("Disabled", 0, winreg.REG_DWORD),
                ("DontShowUI", 0, winreg.REG_DWORD)
            ],
            r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\Windows Error Reporting\Consent": [
                ("DefaultConsent", 1, winreg.REG_DWORD)  # 1 = 每次都询问
            ],
            r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AeDebug": [
                ("Auto", 1, winreg.REG_DWORD),
            ],
            r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\AeDebug": [
                ("Auto", 1, winreg.REG_DWORD),
            ]
        }
        
        success_count = 0
        for key_path, values in restore_settings.items():
            for value_name, value_data, value_type in values:
                if self.set_registry_value(key_path, value_name, value_data, value_type):
                    success_count += 1
                    logger.info(f"  ✓ 已恢复: {value_name}")
        
        # 重新启用错误报告服务
        try:
            subprocess.run(
                ["sc", "config", "WerSvc", "start=", "demand"], 
                capture_output=True, 
                timeout=10
            )
            logger.info("  ✓ 已重新启用Windows错误报告服务")
        except:
            pass
        
        logger.info("\n" + "=" * 60)
        logger.info(f"恢复完成！成功恢复 {success_count} 项设置")
        logger.info("建议重启系统以确保设置完全恢复")
        logger.info("=" * 60)
        
        return success_count


class WindowsErrorHandler:
    """Windows错误处理器 - 窗口级抑制"""
    
    def __init__(self):
        self.is_running = False
        self.monitor_thread = None
        
        # Windows API常量
        self.IDOK = 1
        self.IDCANCEL = 2
        self.IDYES = 6
        self.IDNO = 7
        self.BM_CLICK = 0x00F5
        
        # 加载必要的Windows API
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
    
    def enum_windows_callback(self, hwnd, lParam):
        """窗口枚举回调函数"""
        if not self.user32.IsWindowVisible(hwnd):
            return True
        
        # 获取窗口标题
        length = self.user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
            
        buffer = ctypes.create_unicode_buffer(length + 1)
        self.user32.GetWindowTextW(hwnd, buffer, length + 1)
        window_title = buffer.value
        
        # 获取窗口类名
        class_buffer = ctypes.create_unicode_buffer(256)
        self.user32.GetClassNameW(hwnd, class_buffer, 256)
        class_name = class_buffer.value
        
        # 黑名单：排除已知的正常窗口类名
        blacklist_classes = [
            'SunAwtFrame',  # Java应用窗口
            'Chrome_WidgetWin',  # Chrome浏览器
            'MozillaWindowClass',  # Firefox浏览器
            'ApplicationFrameWindow',  # UWP应用
            'Windows.UI.Core.CoreWindow',  # Windows应用
            'Notepad',  # 记事本
            'CabinetWClass',  # 资源管理器
            'ConsoleWindowClass',  # 命令行窗口
        ]
        
        # 如果是黑名单中的窗口类，直接跳过
        if any(bl_class in class_name for bl_class in blacklist_classes):
            return True
        
        # 检测常见错误窗口的标题关键词（包含关系，已去除冗余）
        error_keywords = [
            'visual',
            'c++',
            'runtime',
            'library',
            'host',              # Host相关窗口
        ]
        
        window_title_lower = window_title.lower()
        
        # 检查窗口标题是否包含错误关键词
        has_error_keyword = any(keyword in window_title_lower for keyword in error_keywords)
        
        # 检查是否是标准对话框（Windows对话框通常使用#32770类名）
        is_standard_dialog = '#32770' in class_name
        
        # 只有同时满足以下条件才处理：
        # 1. 是标准对话框类（#32770）
        # 2. 标题包含错误关键词
        if is_standard_dialog and has_error_keyword:
            logger.info(f"🎯 [DETECTED] 捕获错误窗口: '{window_title}' | 类名: {class_name}")
            self.click_ok_button(hwnd, window_title)
        
        return True
    
    def click_ok_button(self, parent_hwnd, window_title):
        """在指定窗口中查找并点击确认按钮"""
        try:
            # 常见按钮文本（针对Runtime Library错误窗口，确定按钮通常是第一个）
            button_texts = ['确定', 'OK', 'ok', '是', 'Yes', '关闭', 'Close']
            
            # 方法1: 通过按钮文本查找
            child_hwnd = None
            for button_text in button_texts:
                child_hwnd = self.user32.FindWindowExW(
                    parent_hwnd, None, None, button_text
                )
                if child_hwnd:
                    logger.info(f"  🔍 [FOUND] 按钮定位成功: '{button_text}'")
                    # 点击按钮
                    self.user32.SendMessageW(child_hwnd, self.BM_CLICK, 0, 0)
                    logger.info(f"  ✅ [CLICKED] 已自动点击 '{button_text}' | 窗口: '{window_title}'")
                    return True
            
            # 方法2: 通过按钮类名查找（Button控件）
            logger.info("  🔄 [FALLBACK-1] 启用备用方案 - 扫描Button控件...")
            child_hwnd = self.user32.FindWindowExW(parent_hwnd, None, "Button", None)
            if child_hwnd:
                # 获取按钮文本
                length = self.user32.GetWindowTextLengthW(child_hwnd)
                if length > 0:
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    self.user32.GetWindowTextW(child_hwnd, buffer, length + 1)
                    button_text = buffer.value
                    logger.info(f"  🔍 [FOUND] Button控件: '{button_text}'")
                
                self.user32.SendMessageW(child_hwnd, self.BM_CLICK, 0, 0)
                logger.info(f"  ✅ [CLICKED] 已执行点击操作 | 窗口: '{window_title}'")
                return True
            
            # 方法3: 发送回车键（作为最后的备选方案）
            logger.info("  🔄 [FALLBACK-2] 启用终极方案 - 发送回车键...")
            self.user32.SetForegroundWindow(parent_hwnd)
            time.sleep(0.1)
            
            # 发送回车键（VK_RETURN = 0x0D）
            keybd_event = ctypes.windll.user32.keybd_event
            VK_RETURN = 0x0D
            keybd_event(VK_RETURN, 0, 0, 0)  # 按下
            keybd_event(VK_RETURN, 0, 2, 0)  # 释放
            
            logger.info(f"  ⌨️  [SENT] 回车键已发送 | 窗口: '{window_title}'")
            return True
                
        except Exception as e:
            logger.error(f"  ❌ [FAILED] 操作失败: {e}")
            return False
    
    def monitor_error_windows(self, interval=2):
        """持续监控并自动关闭错误窗口"""
        logger.info("╔" + "═" * 58 + "╗")
        logger.info("║" + pad_to_width("  ⚡ [MONITOR SYSTEM] 窗口级错误监控已启动") + "     ║")
        logger.info("║" + pad_to_width(f"  🔍 扫描间隔: {interval}秒") + "  ║")
        logger.info("║" + pad_to_width("  ⌨️  停止监控: [Ctrl+C]") + " ║")
        logger.info("╚" + "═" * 58 + "╝")
        
        self.is_running = True
        
        # 定义回调函数类型
        EnumWindowsProc = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HWND,
            wintypes.LPARAM
        )
        
        callback = EnumWindowsProc(self.enum_windows_callback)
        
        try:
            while self.is_running:
                # 枚举所有顶层窗口
                self.user32.EnumWindows(callback, 0)
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("\n🛑 [SIGNAL] 收到停止信号，正在安全退出监控...")
        except Exception as e:
            logger.error(f"❌ [ERROR] 监控线程发生错误: {e}")
        finally:
            self.is_running = False
            logger.info("✅ [STOPPED] 监控线程已安全停止")
    
    def start_monitor(self, interval=2):
        """启动监控线程"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            logger.warning("监控线程已在运行中")
            return
        
        self.monitor_thread = threading.Thread(
            target=self.monitor_error_windows,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitor(self):
        """停止监控线程"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)


def check_admin_privileges():
    """检查是否有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def print_header():
    """打印程序头部"""
    print("\n╔" + "═" * 58 + "╗")
    print("║" + pad_to_width("") + "║")
    print("║" + pad_to_width("    ██╗    ██╗██╗███╗   ██╗    ███████╗██████╗ ██████╗") + "║")
    print("║" + pad_to_width("    ██║    ██║██║████╗  ██║    ██╔════╝██╔══██╗██╔══██╗") + "║")
    print("║" + pad_to_width("    ██║ █╗ ██║██║██╔██╗ ██║    █████╗  ██████╔╝██████╔╝") + "║")
    print("║" + pad_to_width("    ██║███╗██║██║██║╚██╗██║    ██╔══╝  ██╔══██╗██╔══██╗") + "║")
    print("║" + pad_to_width("    ╚███╔███╔╝██║██║ ╚████║    ███████╗██║  ██║██║  ██║") + "║")
    print("║" + pad_to_width("     ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝") + "║")
    print("║" + pad_to_width("") + "║")
    print("║" + pad_to_width("           ⚡ Windows Error Suppressor v2.0 ⚡") + "║")
    print("║" + pad_to_width("                  [ Powered by X.D ]") + "║")
    print("║" + pad_to_width("") + "║")
    print("╚" + "═" * 58 + "╝")


def print_admin_status():
    """打印管理员状态"""
    is_admin = check_admin_privileges()
    print()
    print("┌" + "─" * 58 + "┐")
    if is_admin:
        print("│" + pad_to_width("  🔐 系统权限: ████████████████████ [ADMIN - 100%]") + "│")
        print("│" + pad_to_width("  ✅ 状态: 完全访问模式 - 所有功能已解锁") + "│")
    else:
        print("│" + pad_to_width("  🔓 系统权限: ██████░░░░░░░░░░░░░░ [USER - 30%]") + "│")
        print("│" + pad_to_width("  ⚠️  状态: 受限访问模式 - 部分功能需要提升权限") + "│")
        print("│" + pad_to_width("  💡 提示: [选项1]=需要ADMIN | [选项2]=无需权限") + "│")
    print("└" + "─" * 58 + "┘")
    print()


def input_with_timeout(prompt, timeout=3, default="2"):
    """带超时的输入函数（Windows专用）"""
    print(prompt, end='', flush=True)
    
    start_time = time.time()
    input_chars = []
    
    while True:
        # 检查是否超时
        if time.time() - start_time > timeout:
            print(f"\n🕐 [TIMEOUT] 自动加载选项 [{default}] - MONITOR MODE 已激活")
            return default
        
        # 检查是否有按键
        if msvcrt.kbhit():
            char = msvcrt.getwche()  # 读取字符并回显
            
            if char == '\r':  # 回车键
                print()
                if input_chars:
                    return ''.join(input_chars)
                else:
                    print(f"⚡ 默认选择 [{default}] - MONITOR MODE")
                    return default
            elif char == '\x08':  # 退格键
                if input_chars:
                    input_chars.pop()
                    sys.stdout.write('\b \b')  # 删除显示的字符
                    sys.stdout.flush()
            else:
                input_chars.append(char)
        
        time.sleep(0.05)  # 避免CPU占用过高


def main():
    """主函数"""
    print_header()
    print_admin_status()
    
    # 显示菜单
    print("╭" + "─" * 58 + "╮")
    print("│" + pad_to_width("  🎯 功能选择模块 [AUTO-SELECT IN 3s]") + "│")
    print("├" + "─" * 58 + "┤")
    print("│" + pad_to_width("") + "│")
    print("│" + pad_to_width("  [1] 🛡️  REGISTRY MODE - 注册表系统级抑制") + "│")
    print("│" + pad_to_width("      ├─ 从源头禁用错误报告") + "│")
    print("│" + pad_to_width("      ├─ 永久生效，重启后依然有效") + "│")
    print("│" + pad_to_width("      └─ 需要管理员权限 [ADMIN REQUIRED]") + "│")
    print("│" + pad_to_width("") + "│")
    print("│" + pad_to_width("  [2] ⚡ MONITOR MODE - 常驻进程窗口级抑制 [RECOMMENDED]") + "│")
    print("│" + pad_to_width("      ├─ 实时监控错误窗口") + "│")
    print("│" + pad_to_width("      ├─ 自动点击关闭按钮") + "│")
    print("│" + pad_to_width("      └─ 无需管理员权限 [NO ADMIN]") + "│")
    print("│" + pad_to_width("") + "│")
    print("╰" + "─" * 58 + "╯")
    print()
    
    choice = input_with_timeout("⌨️  >>> 请输入选择 [1/2]: ", timeout=3, default="2").strip()
    
    # 隐藏的恢复功能
    if choice == "987789":
        print()
        print("╔" + "═" * 58 + "╗")
        print("║" + pad_to_width("  🔓 [HIDDEN MODE] 系统恢复模式已激活") + "║")
        print("╚" + "═" * 58 + "╝")
        logger.info("\n检测到隐藏指令：注册表恢复")
        suppressor = RegistryErrorSuppressor()
        suppressor.restore_defaults()
        print("\n" + "─" * 60)
        print("⏸️  按 [ENTER] 键退出程序...")
        input()
        return
    
    if choice == "1":
        # 注册表系统级抑制
        print()
        print("┌" + "─" * 58 + "┐")
        print("│" + pad_to_width("  🛡️  [REGISTRY MODE] 正在初始化系统级抑制...") + "│")
        print("└" + "─" * 58 + "┘")
        print()
        suppressor = RegistryErrorSuppressor()
        success = suppressor.apply_all_suppressions()
        
        if success:
            print()
            print("╔" + "═" * 58 + "╗")
            print("║" + pad_to_width("  ✅ [SUCCESS] 系统级抑制设置完成！") + "║")
            print("╠" + "═" * 58 + "╣")
            print("║" + pad_to_width("  📋 执行建议:") + "║")
            print("║" + pad_to_width("     1️⃣  重启系统以确保所有设置完全生效") + "║")
            print("║" + pad_to_width("     2️⃣  如需更彻底的保护，可再运行选项2启动窗口监控") + "║")
            print("╚" + "═" * 58 + "╝")
        else:
            print()
            print("╔" + "═" * 58 + "╗")
            print("║" + pad_to_width("  ❌ [FAILED] 设置失败！") + "║")
            print("║" + pad_to_width("  ⚠️  请以管理员身份运行本程序") + "║")
            print("╚" + "═" * 58 + "╝")
        
        print("\n" + "─" * 60)
        print("⏸️  按 [ENTER] 键退出程序...")
        input()
        
    elif choice == "2":
        # 常驻进程窗口级抑制
        print()
        print("┌" + "─" * 58 + "┐")
        print("│" + pad_to_width("  ⚡ [MONITOR MODE] 正在启动实时监控系统...") + "│")
        print("└" + "─" * 58 + "┘")
        print()
        interval = 1.0  # 默认1秒检查间隔
        
        handler = WindowsErrorHandler()
        
        try:
            # 启动监控
            handler.monitor_error_windows(interval)
        except KeyboardInterrupt:
            print()
            print("╔" + "═" * 58 + "╗")
            print("║" + pad_to_width("  🛑 [STOPPED] 监控已停止") + "║")
            print("╚" + "═" * 58 + "╝")
        
    else:
        print()
        print("╔" + "═" * 58 + "╗")
        print("║" + pad_to_width("  ❌ [ERROR] 无效的选择！") + "║")
        print("╚" + "═" * 58 + "╝")
        time.sleep(2)
    
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + pad_to_width("  👋 感谢使用 Windows Error Suppressor!") + "║")
    print("║" + pad_to_width("  🌟 Stay Safe, Stay Secure!") + "║")
    print("╚" + "═" * 58 + "╝")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print("╔" + "═" * 58 + "╗")
        print("║" + pad_to_width("  ⚠️  [INTERRUPTED] 程序被用户中断") + "║")
        print("╚" + "═" * 58 + "╝")
    except Exception as e:
        logger.error(f"\n程序运行出错: {e}")
        print()
        print("╔" + "═" * 58 + "╗")
        print("║" + pad_to_width("  ❌ [FATAL ERROR] 程序运行出错") + "║")
        print("║" + pad_to_width("  📝 错误信息: " + str(e)[:35]) + "║")
        print("╚" + "═" * 58 + "╝")
        print("\n⏸️  按 [ENTER] 键退出程序...")
        input()
