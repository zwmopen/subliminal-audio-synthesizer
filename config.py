# -*- coding: utf-8 -*-
"""
Subliminal Master 配置文件
集中管理所有配置参数
"""

import os

class Config:
    """应用配置类"""
    
    # 应用信息
    APP_NAME = "Subliminal Master"
    APP_VERSION = "3.1.0"
    APP_AUTHOR = "Dadan Technology Co., Ltd."
    
    # 服务器配置
    HOST = "0.0.0.0"
    PORT = 5000
    DEBUG = False
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB
    UPLOAD_FOLDER = "uploads"
    OUTPUT_FOLDER = "output"
    ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.aac', '.flac'}
    
    # 文件清理配置
    FILE_CLEANUP_HOURS = 24  # 24小时后清理临时文件
    MAX_UPLOAD_FILES = 100    # 最大保留上传文件数
    
    # 音频处理默认参数
    DEFAULT_CARRIER_FREQ = 17500       # 载波频率 (Hz)
    CARRIER_FREQ_MIN = 15000           # 最小载波频率
    CARRIER_FREQ_MAX = 20000           # 最大载波频率
    
    DEFAULT_SUBLIMINAL_VOLUME = -23    # 潜意识轨音量 (dB)
    SUBLIMINAL_VOLUME_MIN = -40        # 最小音量
    SUBLIMINAL_VOLUME_MAX = 0          # 最大音量
    
    DEFAULT_BACKGROUND_VOLUME = 0      # 背景音乐音量 (dB)
    BACKGROUND_VOLUME_MIN = -20        # 最小音量
    BACKGROUND_VOLUME_MAX = 10         # 最大音量
    
    # 双耳搏动参数
    DEFAULT_BINAURAL_LEFT = 430        # 左耳频率 (Hz)
    DEFAULT_BINAURAL_RIGHT = 434       # 右耳频率 (Hz) - 差值4Hz Theta波
    DEFAULT_BINAURAL_VOLUME = -15      # 双耳搏动音量 (dB)
    BINAURAL_FREQ_MIN = 200            # 最小频率
    BINAURAL_FREQ_MAX = 500            # 最大频率
    
    # 音频参数
    SAMPLE_RATE = 44100                # 采样率
    TARGET_DB = -1                     # 最终输出目标音量
    
    # 日志配置
    LOG_FOLDER = "logs"
    LOG_LEVEL = "INFO"
    LOG_MAX_BYTES = 10 * 1024 * 1024   # 10MB
    LOG_BACKUP_COUNT = 5
    
    @classmethod
    def ensure_folders(cls):
        """确保必要的文件夹存在"""
        for folder in [cls.UPLOAD_FOLDER, cls.OUTPUT_FOLDER, cls.LOG_FOLDER]:
            if not os.path.exists(folder):
                os.makedirs(folder)
    
    @classmethod
    def is_allowed_file(cls, filename):
        """检查文件扩展名是否允许"""
        if not filename:
            return False
        ext = os.path.splitext(filename)[1].lower()
        return ext in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def get_config_dict(cls):
        """获取配置字典（用于前端显示）"""
        return {
            'carrier_freq': {
                'default': cls.DEFAULT_CARRIER_FREQ,
                'min': cls.CARRIER_FREQ_MIN,
                'max': cls.CARRIER_FREQ_MAX
            },
            'subliminal_volume': {
                'default': cls.DEFAULT_SUBLIMINAL_VOLUME,
                'min': cls.SUBLIMINAL_VOLUME_MIN,
                'max': cls.SUBLIMINAL_VOLUME_MAX
            },
            'background_volume': {
                'default': cls.DEFAULT_BACKGROUND_VOLUME,
                'min': cls.BACKGROUND_VOLUME_MIN,
                'max': cls.BACKGROUND_VOLUME_MAX
            },
            'binaural': {
                'left_freq': cls.DEFAULT_BINAURAL_LEFT,
                'right_freq': cls.DEFAULT_BINAURAL_RIGHT,
                'volume': cls.DEFAULT_BINAURAL_VOLUME,
                'freq_min': cls.BINAURAL_FREQ_MIN,
                'freq_max': cls.BINAURAL_FREQ_MAX
            }
        }
