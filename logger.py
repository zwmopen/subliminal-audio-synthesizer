# -*- coding: utf-8 -*-
"""
Subliminal Master 日志模块
提供统一的日志记录功能
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from config import Config

def setup_logger(name="SubliminalMaster"):
    """
    设置并返回日志记录器
    
    参数:
        name: 日志记录器名称
    
    返回:
        logging.Logger: 配置好的日志记录器
    """
    Config.ensure_folders()
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    if logger.handlers:
        return logger
    
    file_handler = RotatingFileHandler(
        os.path.join(Config.LOG_FOLDER, "app.log"),
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_processing_start(logger, affirmation_file, background_file, config):
    """记录处理开始"""
    logger.info("="*60)
    logger.info("开始处理潜意识音频")
    logger.info(f"肯定句文件: {affirmation_file}")
    logger.info(f"背景音乐文件: {background_file}")
    logger.info(f"配置参数: {config}")

def log_processing_step(logger, step, message):
    """记录处理步骤"""
    logger.info(f"[步骤{step}] {message}")

def log_processing_complete(logger, output_file, file_size, duration):
    """记录处理完成"""
    logger.info("="*60)
    logger.info(f"处理完成! 输出文件: {output_file}")
    logger.info(f"文件大小: {file_size:.2f}MB")
    logger.info(f"音频时长: {duration:.2f}秒")
    logger.info("="*60)

def log_error(logger, error, traceback=None):
    """记录错误"""
    logger.error(f"处理失败: {error}")
    if traceback:
        logger.error(traceback)

logger = setup_logger()
