# -*- coding: utf-8 -*-
"""
Subliminal Master 文件清理模块

自动清理过期的临时文件，防止磁盘空间被占满。
支持按时间和数量两种清理策略。

功能：
- 按时间清理：删除超过指定小时数的文件
- 按数量清理：当文件数超过限制时删除最旧的文件
- 后台自动运行：每小时检查一次
"""

import os
import time
import threading
from datetime import datetime, timedelta
from typing import List, Tuple
from config import Config
from logger import logger


def get_files_in_folder(folder: str) -> List[Tuple[str, float]]:
    """
    获取文件夹中的所有文件及其修改时间
    
    参数:
        folder: 文件夹路径
    
    返回:
        List[Tuple[str, float]]: (文件路径, 修改时间) 列表
    """
    if not os.path.exists(folder):
        return []
    
    files = []
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath):
            try:
                mtime = os.path.getmtime(filepath)
                files.append((filepath, mtime))
            except OSError:
                continue
    
    return files


def delete_file(filepath: str) -> Tuple[bool, int]:
    """
    安全删除文件
    
    参数:
        filepath: 文件路径
    
    返回:
        Tuple[bool, int]: (是否成功, 文件大小)
    """
    try:
        file_size = os.path.getsize(filepath)
        os.remove(filepath)
        return True, file_size
    except Exception as e:
        logger.warning(f"删除文件失败 {filepath}: {e}")
        return False, 0


class FileCleaner:
    """
    文件清理器
    
    自动清理过期的临时文件，支持两种清理策略：
    1. 按时间清理：删除超过 FILE_CLEANUP_HOURS 小时的文件
    2. 按数量清理：当文件数超过 MAX_UPLOAD_FILES 时删除最旧的文件
    
    使用方法：
        cleaner = FileCleaner()
        cleaner.start()  # 启动后台清理
        # ...
        cleaner.stop()   # 停止清理
    """
    
    def __init__(self):
        """初始化文件清理器"""
        self._running = False
        self._thread = None
        self._cleanup_interval = 3600  # 清理间隔（秒）
    
    def cleanup_by_time(self) -> Tuple[int, int]:
        """
        按时间清理过期文件
        
        删除修改时间早于 FILE_CLEANUP_HOURS 小时的文件
        
        返回:
            Tuple[int, int]: (清理文件数, 释放字节数)
        """
        cleaned_count = 0
        cleaned_size = 0
        cutoff_time = datetime.now() - timedelta(hours=Config.FILE_CLEANUP_HOURS)
        
        for folder in [Config.UPLOAD_FOLDER, Config.OUTPUT_FOLDER]:
            files = get_files_in_folder(folder)
            
            for filepath, mtime in files:
                file_time = datetime.fromtimestamp(mtime)
                
                if file_time < cutoff_time:
                    success, size = delete_file(filepath)
                    if success:
                        cleaned_count += 1
                        cleaned_size += size
                        logger.debug(f"清理过期文件: {os.path.basename(filepath)}")
        
        if cleaned_count > 0:
            logger.info(f"时间清理完成: {cleaned_count} 个文件, {cleaned_size/1024/1024:.2f}MB")
        
        return cleaned_count, cleaned_size
    
    def cleanup_by_count(self) -> int:
        """
        按数量清理文件
        
        当文件数超过 MAX_UPLOAD_FILES 时，删除最旧的文件
        
        返回:
            int: 清理文件数
        """
        cleaned_count = 0
        
        for folder in [Config.UPLOAD_FOLDER, Config.OUTPUT_FOLDER]:
            files = get_files_in_folder(folder)
            
            if len(files) <= Config.MAX_UPLOAD_FILES:
                continue
            
            files.sort(key=lambda x: x[1], reverse=True)
            
            for filepath, _ in files[Config.MAX_UPLOAD_FILES:]:
                success, _ = delete_file(filepath)
                if success:
                    cleaned_count += 1
                    logger.debug(f"清理超限文件: {os.path.basename(filepath)}")
        
        if cleaned_count > 0:
            logger.info(f"数量清理完成: {cleaned_count} 个文件")
        
        return cleaned_count
    
    def cleanup_all(self) -> Tuple[int, int]:
        """
        执行所有清理操作
        
        返回:
            Tuple[int, int]: (总清理文件数, 总释放字节数)
        """
        count1, size = self.cleanup_by_time()
        count2 = self.cleanup_by_count()
        return count1 + count2, size
    
    def _cleanup_loop(self):
        """清理循环（内部方法）"""
        while self._running:
            try:
                self.cleanup_all()
            except Exception as e:
                logger.error(f"文件清理出错: {e}")
            
            time.sleep(self._cleanup_interval)
    
    def start(self):
        """启动自动清理服务"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._thread.start()
        logger.info("文件自动清理服务已启动")
    
    def stop(self):
        """停止自动清理服务"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("文件自动清理服务已停止")


file_cleaner = FileCleaner()
