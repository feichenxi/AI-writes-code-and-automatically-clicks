#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动点击"继续"按钮工具 v3.0
功能：通过图像识别"继续"按钮位置并自动点击
"""

import time
import threading
import logging
from logging.handlers import RotatingFileHandler
import pyautogui

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'continue_click.log', 
            maxBytes=1*1024*1024, 
            backupCount=1, 
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 禁用pyautogui的安全检查
pyautogui.FAILSAFE = False


class ContinueClicker:
    """继续按钮自动点击器"""
    
    def __init__(self):
        self.is_running = False
        self.monitor_thread = None
    
    def get_display_width(self, text):
        """计算字符串的显示宽度"""
        width = 0
        i = 0
        while i < len(text):
            char = text[i]
            code = ord(char)
            
            if 0xFE00 <= code <= 0xFE0F or code == 0x200D:
                i += 1
                continue
                
            if (0x4E00 <= code <= 0x9FFF or
                0x3000 <= code <= 0x303F or
                0xFF00 <= code <= 0xFFEF or
                0x3400 <= code <= 0x4DBF):
                width += 2
            elif (0x1F000 <= code <= 0x1FFFF or
                  0x2600 <= code <= 0x27BF or
                  0x2300 <= code <= 0x23FF):
                width += 2
            elif char == '\t':
                width += 4
            else:
                width += 1
            
            i += 1
        
        return width
    
    def pad_to_width(self, text, target_width=58):
        """将文本填充到指定宽度"""
        current_width = self.get_display_width(text)
        if current_width < target_width:
            return text + ' ' * (target_width - current_width)
        return text
    
    def find_image_position(self, image_path, confidence=0.8):
        """在屏幕上查找图像位置"""
        try:
            position = pyautogui.locateOnScreen(image_path, confidence=confidence)
            
            if position:
                center_x = position.left + position.width // 2
                center_y = position.top + position.height // 2
                return (center_x, center_y)
            
            return None
        except Exception as e:
            logger.debug(f"查找图像 '{image_path}' 失败: {e}")
            return None
    
    def find_continue_button_position(self):
        """查找"继续"按钮的位置"""
        image_files = [
            "continue_button.png",
            "continue_button1.png",
            "continue_button2.png",
            "continue_button3.png"
        ]
        
        for image_file in image_files:
            position = self.find_image_position(image_file)
            if position:
                logger.info(f"🎯 [FOUND] 找到按钮 '{image_file}' 位置: {position}")
                return position
        
        logger.debug("未找到任何'继续'按钮图像")
        return None
    
    def click_position(self, x, y):
        """点击指定坐标"""
        try:
            # 移动鼠标到目标位置
            pyautogui.moveTo(x, y, duration=0.1)
            time.sleep(0.05)
            
            # 点击
            pyautogui.click(x, y)
            
            logger.info(f"✅ [CLICKED] 已点击坐标 ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"❌ [FAILED] 点击失败: {e}")
            return False
    
    def monitor_and_click(self, interval=1):
        """持续监控并点击"继续"按钮"""
        logger.info("╔" + "═" * 58 + "╗")
        logger.info("║" + self.pad_to_width("  ⚡ [MONITOR SYSTEM] 继续按钮监控已启动") + "     ║")
        logger.info("║" + self.pad_to_width(f"  🔍 扫描间隔: {interval}秒") + "  ║")
        logger.info("║" + self.pad_to_width("  📍 识别方式: 图像识别") + "  ║")
        logger.info("║" + self.pad_to_width("  ⌨️  停止监控: [Ctrl+C]") + " ║")
        logger.info("╚" + "═" * 58 + "╝")
        
        self.is_running = True
        
        try:
            while self.is_running:
                # 查找"继续"按钮位置
                position = self.find_continue_button_position()
                
                if position:
                    x, y = position
                    # 点击该位置
                    self.click_position(x, y)
                    # 等待一段时间，避免重复点击
                    time.sleep(2)
                else:
                    # 未找到，继续监控
                    time.sleep(interval)
                    
        except KeyboardInterrupt:
            logger.info("\n🛑 [SIGNAL] 收到停止信号，正在安全退出监控...")
        except Exception as e:
            logger.error(f"❌ [ERROR] 监控线程发生错误: {e}")
        finally:
            self.is_running = False
            logger.info("✅ [STOPPED] 监控线程已安全停止")
    
    def start_monitor(self, interval=1):
        """启动监控线程"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            logger.warning("监控线程已在运行中")
            return
        
        self.monitor_thread = threading.Thread(
            target=self.monitor_and_click,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitor(self):
        """停止监控线程"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)


def print_header():
    """打印程序头部"""
    print("\n╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + " " * 10 + "自动点击'继续'按钮工具 v3.0" + " " * 14 + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print()


def print_menu():
    """打印菜单"""
    print("\n" + "=" * 60)
    print("请选择操作：")
    print("=" * 60)
    print("  1. 截取'继续'按钮图片（首次使用必须）")
    print("  2. 启动继续按钮监控")
    print("  3. 退出程序")
    print("=" * 60)
    print()


def check_dependencies():
    """检查依赖库"""
    print("正在检查依赖库...")
    
    missing = []
    
    try:
        import pyautogui
        print("  ✓ pyautogui 已安装")
    except ImportError:
        print("  ✗ pyautogui 未安装")
        missing.append("pyautogui")
    
    if missing:
        print(f"\n请安装缺失的依赖库:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    print("\n所有必需依赖库已就绪！")
    return True


def main():
    """主函数"""
    print_header()
    
    # 检查依赖
    if not check_dependencies():
        input("\n按回车键退出...")
        return
    
    clicker = ContinueClicker()
    
    while True:
        print_menu()
        choice = input("请输入选项 (1-3): ").strip()
        
        if choice == '1':
            print("\n启动截图工具...")
            import subprocess
            subprocess.run(["python", "截图工具.py"])
            
        elif choice == '2':
            print("\n正在启动继续按钮监控...")
            clicker.start_monitor(interval=1)
            
            # 等待监控线程结束
            try:
                while clicker.monitor_thread and clicker.monitor_thread.is_alive():
                    time.sleep(0.5)
            except KeyboardInterrupt:
                clicker.stop_monitor()
            
            print("\n监控已停止")
            break
            
        elif choice == '3':
            print("\n感谢使用！")
            break
            
        else:
            print("\n无效选项，请重新输入！")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已退出")
    except Exception as e:
        logger.error(f"程序发生错误: {e}")
        print(f"\n程序发生错误: {e}")
