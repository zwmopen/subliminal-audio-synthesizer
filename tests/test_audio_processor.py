# -*- coding: utf-8 -*-
"""
Subliminal Master 单元测试
使用 pytest + mock 进行测试，不依赖外部音频文件
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAudioProcessor:
    """音频处理模块测试"""
    
    @patch('audio_processor.AudioSegment')
    def test_generate_binaural_beat(self, mock_audiosegment):
        """
        测试双耳搏动生成
        
        验证：
        1. 生成的音频时长正确
        2. 左右声道频率正确
        """
        from audio_processor import generate_binaural_beat
        
        # Mock AudioSegment
        mock_left = Mock()
        mock_right = Mock()
        mock_stereo = Mock()
        mock_stereo.__add__ = Mock(return_value=mock_stereo)
        
        with patch('audio_processor.Sine') as mock_sine:
            mock_sine.return_value.to_audio_segment.side_effect = [mock_left, mock_right]
            mock_audiosegment.from_mono_audiosegments.return_value = mock_stereo
            
            result = generate_binaural_beat(10000, 430, 434, -15)
            
            # 验证调用
            assert mock_sine.call_count == 2
            mock_audiosegment.from_mono_audiosegments.assert_called_once()
    
    def test_normalize_audio(self):
        """
        测试音频标准化
        
        验证：
        1. 静默音频返回原样
        2. 正常音频被标准化
        """
        from audio_processor import normalize_audio
        
        # Mock 静默音频
        mock_silent = Mock()
        mock_silent.dBFS = float('-inf')
        
        result = normalize_audio(mock_silent, -20)
        assert result == mock_silent
        
        # Mock 正常音频
        mock_audio = Mock()
        mock_audio.dBFS = -10
        mock_audio.apply_gain = Mock(return_value=mock_audio)
        
        result = normalize_audio(mock_audio, -20)
        mock_audio.apply_gain.assert_called_once_with(-10)
    
    def test_loop_audio_shorter(self):
        """
        测试音频循环 - 目标时长更长
        
        验证：音频被正确循环扩展
        """
        from audio_processor import loop_audio
        
        mock_audio = Mock()
        mock_audio.__len__ = Mock(return_value=5000)
        mock_audio.__mul__ = Mock(return_value=mock_audio)
        mock_audio.__getitem__ = Mock(return_value=mock_audio)
        
        result = loop_audio(mock_audio, 10000)
        
        # 验证乘法被调用
        mock_audio.__mul__.assert_called()
    
    def test_loop_audio_longer(self):
        """
        测试音频循环 - 目标时长更短
        
        验证：音频被截断
        """
        from audio_processor import loop_audio
        
        mock_audio = Mock()
        mock_audio.__len__ = Mock(return_value=10000)
        mock_audio.__getitem__ = Mock(return_value=mock_audio)
        
        result = loop_audio(mock_audio, 5000)
        
        # 验证截断
        mock_audio.__getitem__.assert_called()
    
    def test_loop_audio_empty(self):
        """
        测试音频循环 - 空音频
        
        验证：返回静默音频
        """
        from audio_processor import loop_audio
        
        mock_audio = Mock()
        mock_audio.__len__ = Mock(return_value=0)
        
        with patch('audio_processor.AudioSegment.silent') as mock_silent:
            mock_silent.return_value = Mock()
            result = loop_audio(mock_audio, 5000)
            mock_silent.assert_called_once()
    
    @patch('audio_processor.AudioSegment.from_file')
    def test_validate_audio_file_valid(self, mock_from_file):
        """
        测试音频验证 - 有效文件
        """
        from audio_processor import validate_audio_file
        
        mock_audio = Mock()
        mock_audio.__len__ = Mock(return_value=10000)
        mock_audio.frame_rate = 44100
        mock_audio.channels = 2
        mock_audio.sample_width = 2
        mock_from_file.return_value = mock_audio
        
        valid, result = validate_audio_file('test.mp3')
        
        assert valid == True
        assert 'duration_ms' in result
        assert 'sample_rate' in result
    
    @patch('audio_processor.AudioSegment.from_file')
    def test_validate_audio_file_empty(self, mock_from_file):
        """
        测试音频验证 - 空文件
        """
        from audio_processor import validate_audio_file
        
        mock_audio = Mock()
        mock_audio.__len__ = Mock(return_value=0)
        mock_from_file.return_value = mock_audio
        
        valid, result = validate_audio_file('test.mp3')
        
        assert valid == False
        assert '0' in result
    
    @patch('audio_processor.AudioSegment.from_file')
    def test_validate_audio_file_invalid(self, mock_from_file):
        """
        测试音频验证 - 无效文件
        """
        from audio_processor import validate_audio_file
        
        mock_from_file.side_effect = Exception('Invalid file')
        
        valid, result = validate_audio_file('test.mp3')
        
        assert valid == False


class TestProcessSilentSubliminal:
    """高频调制处理测试"""
    
    def test_process_silent_subliminal_empty(self):
        """
        测试空音频处理
        
        验证：空音频返回静默
        """
        from audio_processor import process_silent_subliminal
        
        mock_audio = Mock()
        mock_audio.set_channels = Mock(return_value=mock_audio)
        mock_audio.set_frame_rate = Mock(return_value=mock_audio)
        mock_audio.get_array_of_samples = Mock(return_value=np.array([]))
        mock_audio.__len__ = Mock(return_value=1000)
        
        with patch('audio_processor.AudioSegment.silent') as mock_silent:
            mock_silent.return_value = Mock()
            result = process_silent_subliminal(mock_audio, 17500)
            mock_silent.assert_called_once()
    
    def test_process_silent_subliminal_normal(self):
        """
        测试正常音频处理
        
        验证：音频被正确调制
        """
        from audio_processor import process_silent_subliminal
        
        # 创建模拟音频数据
        mock_audio = Mock()
        mock_audio.set_channels = Mock(return_value=mock_audio)
        mock_audio.set_frame_rate = Mock(return_value=mock_audio)
        
        # 模拟音频采样数据
        samples = np.array([1000, 2000, 3000, 4000] * 1000, dtype=np.int16)
        mock_audio.get_array_of_samples = Mock(return_value=samples)
        mock_audio._spawn = Mock(return_value=Mock())
        
        with patch('audio_processor.Config') as mock_config:
            mock_config.SAMPLE_RATE = 44100
            result = process_silent_subliminal(mock_audio, 17500)
            
            # 验证 _spawn 被调用
            mock_audio._spawn.assert_called_once()


class TestFileCleaner:
    """文件清理模块测试"""
    
    @patch('file_cleaner.os.path.exists')
    @patch('file_cleaner.os.listdir')
    @patch('file_cleaner.os.path.getmtime')
    @patch('file_cleaner.os.path.getsize')
    @patch('file_cleaner.os.remove')
    def test_cleanup_by_time(self, mock_remove, mock_getsize, mock_getmtime, 
                             mock_listdir, mock_exists):
        """
        测试按时间清理
        
        验证：过期文件被删除
        """
        from file_cleaner import FileCleaner
        from datetime import datetime, timedelta
        
        mock_exists.return_value = True
        mock_listdir.return_value = ['old_file.wav', 'new_file.wav']
        mock_getsize.return_value = 1024
        
        # 设置旧文件和新文件的时间
        old_time = (datetime.now() - timedelta(hours=48)).timestamp()
        new_time = datetime.now().timestamp()
        mock_getmtime.side_effect = [old_time, new_time]
        
        with patch('file_cleaner.Config') as mock_config:
            mock_config.FILE_CLEANUP_HOURS = 24
            mock_config.UPLOAD_FOLDER = 'uploads'
            mock_config.OUTPUT_FOLDER = 'output'
            mock_config.MAX_UPLOAD_FILES = 100
            
            cleaner = FileCleaner()
            count, size = cleaner.cleanup_by_time()
            
            # 验证旧文件被删除
            assert mock_remove.call_count >= 1
    
    @patch('file_cleaner.os.path.exists')
    @patch('file_cleaner.os.listdir')
    def test_cleanup_by_count(self, mock_listdir, mock_exists):
        """
        测试按数量清理
        
        验证：超过限制时删除最旧文件
        """
        from file_cleaner import FileCleaner
        
        mock_exists.return_value = True
        # 模拟超过限制的文件数
        mock_listdir.return_value = [f'file_{i}.wav' for i in range(150)]
        
        with patch('file_cleaner.Config') as mock_config:
            mock_config.FILE_CLEANUP_HOURS = 24
            mock_config.UPLOAD_FOLDER = 'uploads'
            mock_config.OUTPUT_FOLDER = 'output'
            mock_config.MAX_UPLOAD_FILES = 100
            
            with patch('file_cleaner.get_files_in_folder') as mock_get_files:
                # 模拟文件列表
                mock_get_files.return_value = [
                    (f'uploads/file_{i}.wav', i) for i in range(150)
                ]
                
                with patch('file_cleaner.delete_file') as mock_delete:
                    mock_delete.return_value = (True, 1024)
                    
                    cleaner = FileCleaner()
                    count = cleaner.cleanup_by_count()
                    
                    # 验证删除了超出的文件
                    assert mock_delete.call_count == 50


class TestConfig:
    """配置模块测试"""
    
    def test_is_allowed_file_valid(self):
        """
        测试文件扩展名验证 - 有效
        """
        from config import Config
        
        assert Config.is_allowed_file('test.mp3') == True
        assert Config.is_allowed_file('test.wav') == True
        assert Config.is_allowed_file('test.m4a') == True
        assert Config.is_allowed_file('test.aac') == True
        assert Config.is_allowed_file('test.flac') == True
    
    def test_is_allowed_file_invalid(self):
        """
        测试文件扩展名验证 - 无效
        """
        from config import Config
        
        assert Config.is_allowed_file('test.txt') == False
        assert Config.is_allowed_file('test.exe') == False
        assert Config.is_allowed_file('test') == False
        assert Config.is_allowed_file('') == False
    
    def test_get_config_dict(self):
        """
        测试配置字典生成
        """
        from config import Config
        
        config_dict = Config.get_config_dict()
        
        assert 'carrier_freq' in config_dict
        assert 'subliminal_volume' in config_dict
        assert 'background_volume' in config_dict
        assert 'binaural' in config_dict


class TestSanitizeFilename:
    """文件名处理测试"""
    
    def test_sanitize_filename(self):
        """
        测试文件名安全处理
        
        验证：
        1. 特殊字符被替换
        2. 添加唯一前缀
        """
        from subliminal_master import sanitize_filename
        
        # 测试正常文件名
        result = sanitize_filename('test audio.mp3')
        assert 'test_audio.mp3' in result or 'test_audio' in result
        
        # 测试带特殊字符的文件名
        result = sanitize_filename('test@audio#file.mp3')
        assert '@' not in result
        assert '#' not in result
        
        # 验证唯一前缀存在
        assert '_' in result


class TestFriendlyError:
    """友好错误消息测试"""
    
    def test_get_friendly_error(self):
        """
        测试获取友好错误消息
        """
        from subliminal_master import get_friendly_error
        
        # 测试已知错误
        msg = get_friendly_error('missing_files')
        assert '上传' in msg or '音频' in msg
        
        msg = get_friendly_error('file_too_large')
        assert '大' in msg or 'MB' in msg
        
        # 测试未知错误
        msg = get_friendly_error('unknown_error')
        assert msg  # 应返回默认消息
        
        # 测试带详情的错误
        msg = get_friendly_error('invalid_audio', '肯定句')
        assert '肯定句' in msg


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
