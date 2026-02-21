# -*- coding: utf-8 -*-
"""
Subliminal Master 配置文件
集中管理所有配置参数，支持环境变量覆盖
"""

import os


class Config:
    """
    应用配置类
    
    支持通过环境变量覆盖默认配置，便于部署到不同环境。
    环境变量命名规则：SECTION_KEY，如 FLASK_DEBUG、SERVER_PORT
    """
    
    # 应用信息
    APP_NAME = "Subliminal Master"
    APP_VERSION = "3.2.0"
    APP_AUTHOR = "Dadan Technology Co., Ltd."
    
    # 服务器配置（支持环境变量）
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', 'output')
    ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.aac', '.flac'}
    
    # 文件清理配置
    FILE_CLEANUP_HOURS = int(os.environ.get('FILE_CLEANUP_HOURS', 24))
    MAX_UPLOAD_FILES = int(os.environ.get('MAX_UPLOAD_FILES', 100))
    
    # 音频处理默认参数
    DEFAULT_CARRIER_FREQ = 17500
    CARRIER_FREQ_MIN = 15000
    CARRIER_FREQ_MAX = 20000
    
    DEFAULT_SUBLIMINAL_VOLUME = -23
    SUBLIMINAL_VOLUME_MIN = -40
    SUBLIMINAL_VOLUME_MAX = 0
    
    DEFAULT_BACKGROUND_VOLUME = 0
    BACKGROUND_VOLUME_MIN = -20
    BACKGROUND_VOLUME_MAX = 10
    
    # 双耳搏动参数
    DEFAULT_BINAURAL_LEFT = 430
    DEFAULT_BINAURAL_RIGHT = 434
    DEFAULT_BINAURAL_VOLUME = -15
    BINAURAL_FREQ_MIN = 200
    BINAURAL_FREQ_MAX = 500
    
    # 音频参数
    SAMPLE_RATE = 44100
    TARGET_DB = -1
    
    # 日志配置
    LOG_FOLDER = os.environ.get('LOG_FOLDER', 'logs')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_MAX_BYTES = 10 * 1024 * 1024
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
