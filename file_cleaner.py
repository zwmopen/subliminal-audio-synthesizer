# -*- coding: utf-8 -*-
"""
Subliminal Master 文件清理模块
自动清理过期的临时文件
"""

import os
import time
import threading
from datetime import datetime, timedelta
from config import Config
from logger import logger


class FileCleaner:
    """文件清理器"""
    
    def __init__(self):
        self._running = False
        self._thread = None
    
    def cleanup_old_files(self):
        """清理过期的临时文件"""
        cleaned_count = 0
        cleaned_size = 0
        
        for folder in [Config.UPLOAD_FOLDER, Config.OUTPUT_FOLDER]:
            if not os.path.exists(folder):
                continue
            
            cutoff_time = datetime.now() - timedelta(hours=Config.FILE_CLEANUP_HOURS)
            
            for filename in os.listdir(folder):
                filepath = os.path.join(folder, filename)
                
                if not os.path.isfile(filepath):
                    continue
                
                try:
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_mtime < cutoff_time:
                        file_size = os.path.getsize(filepath)
                        os.remove(filepath)
                        cleaned_count += 1
                        cleaned_size += file_size
                        logger.debug(f"清理过期文件: {filename}")
                except Exception as e:
                    logger.warning(f"清理文件失败 {filename}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"文件清理完成: 清理了 {cleaned_count} 个文件, 释放 {cleaned_size/1024/1024:.2f}MB 空间")
        
        return cleaned_count, cleaned_size
    
    def cleanup_excess_files(self):
        """清理超出数量限制的文件"""
        for folder in [Config.UPLOAD_FOLDER, Config.OUTPUT_FOLDER]:
            if not os.path.exists(folder):
                continue
            
            files = []
            for filename in os.listdir(folder):
                filepath = os.path.join(folder, filename)
                if os.path.isfile(filepath):
                    files.append((filepath, os.path.getmtime(filepath)))
            
            files.sort(key=lambda x: x[1], reverse=True)
            
            if len(files) > Config.MAX_UPLOAD_FILES:
                for filepath, _ in files[Config.MAX_UPLOAD_FILES:]:
                    try:
                        os.remove(filepath)
                        logger.debug(f"清理超出限制文件: {os.path.basename(filepath)}")
                    except Exception as e:
                        logger.warning(f"清理文件失败: {e}")
    
    def _cleanup_loop(self):
        """清理循环"""
        while self._running:
            try:
                self.cleanup_old_files()
                self.cleanup_excess_files()
            except Exception as e:
                logger.error(f"文件清理出错: {e}")
            
            time.sleep(3600)
    
    def start(self):
        """启动自动清理"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._thread.start()
        logger.info("文件自动清理服务已启动")
    
    def stop(self):
        """停止自动清理"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("文件自动清理服务已停止")


file_cleaner = FileCleaner()
