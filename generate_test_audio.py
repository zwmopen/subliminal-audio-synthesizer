# -*- coding: utf-8 -*-
"""
测试音频文件生成器
生成用于测试Subliminal Master的音频文件
"""

import numpy as np
from scipy.io import wavfile
import os

def generate_test_audio(filename, duration_sec, sample_rate=44100, freq=440):
    """
    生成测试音频文件
    
    参数:
        filename: 输出文件名
        duration_sec: 时长（秒）
        sample_rate: 采样率
        freq: 频率 (Hz)
    """
    # 生成时间轴
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    
    # 生成正弦波
    audio = np.sin(2 * np.pi * freq * t)
    
    # 标准化到16位范围
    audio = (audio * 32767).astype(np.int16)
    
    # 保存为WAV文件
    wavfile.write(filename, sample_rate, audio)
    print(f"已生成: {filename} (时长: {duration_sec}秒, 频率: {freq}Hz)")

# 创建测试文件夹
test_folder = "test_audio"
if not os.path.exists(test_folder):
    os.makedirs(test_folder)

# 生成肯定句测试音频（短）
print("生成肯定句测试音频...")
generate_test_audio(
    os.path.join(test_folder, "affirmation_test.wav"),
    duration_sec=5,
    freq=440  # A4音符
)

# 生成背景音乐测试音频（长）
print("生成背景音乐测试音频...")
generate_test_audio(
    os.path.join(test_folder, "background_test.wav"),
    duration_sec=10,
    freq=220  # A3音符，更低的频率模拟背景音乐
)

print("\n测试音频文件生成完成！")
print(f"文件位置: {os.path.abspath(test_folder)}")
