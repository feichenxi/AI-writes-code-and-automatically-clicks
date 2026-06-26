#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动点击工具 v4.0
功能：通过图像识别自动点击"运行"、"仍要运行"、"继续"等按钮
"""

import time
import threading
import logging
import os
import glob
import random
from logging.handlers import RotatingFileHandler
import pyautogui

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'auto_click.log',
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


class AutoClicker:
    """自动点击器"""
    
    def __init__(self):
        self.is_running = False
        self.monitor_thread = None
        self.image_files = self._discover_button_images()
    
    def _discover_button_images(self):
        """自动发现ocr文件夹下所有按钮图片"""
        ocr_dir = "ocr"
        
        # 确保ocr文件夹存在
        if not os.path.exists(ocr_dir):
            os.makedirs(ocr_dir)
            logger.warning(f"⚠️  创建了 {ocr_dir} 文件夹，请将按钮图片放入该文件夹")
            return []
        
        # 查找ocr文件夹下所有png图片
        all_images = glob.glob(os.path.join(ocr_dir, "*.png"))
        
        if all_images:
            logger.info(f"📷 在 {ocr_dir} 文件夹中发现 {len(all_images)} 个按钮图片:")
            for img in all_images:
                logger.info(f"   - {os.path.basename(img)}")
        else:
            logger.warning(f"⚠️  {ocr_dir} 文件夹中未发现任何图片！请将需要识别的按钮截图放入该文件夹")
        
        return all_images
    
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
    
    def find_any_button_position(self):
        """查找所有匹配的按钮，随机返回一个位置"""
        matched_buttons = []
        
        # 扫描所有图片，找出所有匹配的按钮
        for image_file in self.image_files:
            position = self.find_image_position(image_file)
            if position:
                matched_buttons.append((image_file, position))
                logger.info(f"🎯 发现匹配按钮: {os.path.basename(image_file)} 在 {position}")
        
        if matched_buttons:
            # 随机选择一个按钮
            selected = random.choice(matched_buttons)
            logger.info(f"🎲 随机选择点击: {os.path.basename(selected[0])}")
            return selected[1]
        
        logger.debug("未找到任何按钮图像")
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
        """持续监控并点击按钮"""
        logger.info("╔" + "═" * 58 + "╗")
        logger.info("║" + self.pad_to_width("  ⚡ [MONITOR SYSTEM] 自动点击监控已启动") + "     ║")
        logger.info("║" + self.pad_to_width(f"  🔍 扫描间隔: {interval}秒") + "  ║")
        logger.info("║" + self.pad_to_width("  📍 识别方式: 图像识别") + "  ║")
        logger.info("║" + self.pad_to_width(f"  📷 加载图片: {len(self.image_files)} 张") + "  ║")
        logger.info("║" + self.pad_to_width("  ⌨️  停止监控: [Ctrl+C]") + " ║")
        logger.info("╚" + "═" * 58 + "╝")
        
        self.is_running = True
        
        try:
            while self.is_running:
                # 查找按钮位置
                position = self.find_any_button_position()
                
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
    print("║" + " " * 12 + "自动点击工具 v4.0" + " " * 22 + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
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
    """主函数 - 直接启动监控模式"""
    print_header()
    
    # 检查依赖
    if not check_dependencies():
        input("\n按回车键退出...")
        return
    
    clicker = AutoClicker()
    
    print("\n正在启动自动点击监控...")
    print("监控将持续运行，按 Ctrl+C 停止\n")
    
    # 直接启动监控
    try:
        clicker.monitor_and_click(interval=1)
    except KeyboardInterrupt:
        clicker.stop_monitor()
    
    print("\n监控已停止")
    print("\n感谢使用！")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已退出")
    except Exception as e:
        logger.error(f"程序发生错误: {e}")
        print(f"\n程序发生错误: {e}")
