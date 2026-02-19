# -*- coding: utf-8 -*-
"""
Subliminal Master - 潜意识音频合成引擎
Dadan Technology Co., Ltd.

功能：
1. 双轨道输入（肯定句音频 + 背景音乐）
2. 高频调制处理（17.5kHz-19.5kHz）
3. Theta波双耳搏动生成器（430Hz/434Hz）
4. 音量控制滑动条
5. 音轨对齐和循环功能
6. 无损WAV导出

Author: Gemini (Your AI Thought Partner)
Date: 2026-02-11

核心逻辑：
隐藏轨（处理后的肯定句）+ 显性轨（背景音乐）+ 频率诱导（可选的双耳搏动）= 最终成品
"""

import os
import sys
import subprocess
import time
import math
import json
from flask import Flask, render_template_string, request, jsonify, send_file
from werkzeug.utils import secure_filename
import numpy as np
from scipy.io import wavfile
from scipy import signal
from pydub import AudioSegment
from pydub.generators import Sine

# --- 第一步：自动环境检查与依赖安装 ---
def install_dependencies():
    """自动检测并安装缺少的Python库"""
    required_packages = ['pydub', 'numpy', 'scipy', 'flask']
    
    print("正在检查系统依赖...")
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"检测到缺失库: {package}，正在自动安装...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"{package} 安装完成。")

try:
    install_dependencies()
except Exception as e:
    print(f"环境初始化失败: {e}")
    input("按回车键退出...")
    sys.exit(1)

# --- 第二步：配置 ---

CONFIG = {
    # 高频调制参数
    'carrier_freq': 17500,  # 载波频率 (Hz)
    'carrier_freq_max': 19500,  # 最大载波频率 (Hz)
    
    # 双耳搏动参数
    'binaural_left_freq': 430,  # 左耳频率 (Hz)
    'binaural_right_freq': 434,  # 右耳频率 (Hz) - 差值4Hz Theta波
    
    # 音量默认值
    'subliminal_volume_db': -23,  # 潜意识轨默认音量 (dB)
    'background_volume_db': 0,  # 背景音乐默认音量 (dB)
    'binaural_volume_db': -15,  # 双耳搏动默认音量 (dB)
    
    # 采样率
    'sample_rate': 44100,  # 标准采样率
    
    # 文件设置
    'upload_folder': 'uploads',
    'output_folder': 'output',
    'supported_extensions': ('.mp3', '.wav', '.m4a', '.aac', '.flac')
}

# 创建Flask应用
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 最大200MB

# 确保必要的文件夹存在
for folder in [CONFIG['upload_folder'], CONFIG['output_folder']]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- 第三步：核心处理函数 ---

def generate_binaural_beat(duration_ms, left_freq, right_freq, volume_db):
    """
    生成双耳搏动立体声轨道
    
    参数:
        duration_ms: 音频时长 (毫秒)
        left_freq: 左声道频率 (Hz)
        right_freq: 右声道频率 (Hz)
        volume_db: 音量调整值 (dB)
    
    返回:
        AudioSegment: 生成的双耳搏动音频
    """
    print(f"   -> 正在生成双耳搏动 ({left_freq}Hz / {right_freq}Hz, 差频{right_freq-left_freq}Hz)...")
    
    # 生成左声道正弦波
    left_channel = Sine(left_freq).to_audio_segment(duration=duration_ms)
    # 生成右声道正弦波
    right_channel = Sine(right_freq).to_audio_segment(duration=duration_ms)
    
    # 合并为立体声
    binaural_beat = AudioSegment.from_mono_audiosegments(left_channel, right_channel)
    
    # 调整音量
    binaural_beat = binaural_beat + volume_db
    
    return binaural_beat

def process_silent_subliminal(audio_segment, carrier_freq, sample_rate=44100):
    """
    使用振幅调制 (Amplitude Modulation) 将音频移至高频段
    实现"无声潜意识"效果
    
    参数:
        audio_segment: 原始音频 (AudioSegment)
        carrier_freq: 载波频率 (Hz)
        sample_rate: 采样率
    
    返回:
        AudioSegment: 处理后的静默阈下音频
    """
    print(f"   -> 正在进行高频调制 (载波: {carrier_freq}Hz)...")
    
    # 1. 预处理：确保是单声道，并统一采样率
    audio = audio_segment.set_channels(1).set_frame_rate(sample_rate)
    
    # 2. 转换为 Numpy 数组进行数学运算
    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    
    # 3. 生成载波 (Carrier Wave)
    duration_sec = len(samples) / sample_rate
    t = np.linspace(0, duration_sec, len(samples), endpoint=False)
    carrier = np.sin(2 * np.pi * carrier_freq * t)
    
    # 4. 振幅调制 (AM): 原始信号 * 载波
    # 这会将频谱搬移到 载波频率 ± 原始频率 的位置
    modulated_signal = samples * carrier
    
    # 5. 标准化防止爆音
    max_val = np.max(np.abs(modulated_signal))
    if max_val > 0:
        modulated_signal = (modulated_signal / max_val) * (2**15 - 1)
    
    # 6. 转回 AudioSegment
    modulated_samples = modulated_signal.astype(np.int16)
    processed_audio = audio._spawn(modulated_samples.tobytes())
    
    return processed_audio

def normalize_audio(audio_segment, target_db=-20):
    """
    标准化音频到目标dB
    
    参数:
        audio_segment: 音频片段
        target_db: 目标音量 (dB)
    
    返回:
        AudioSegment: 标准化后的音频
    """
    change_in_dB = target_db - audio_segment.dBFS
    return audio_segment.apply_gain(change_in_dB)

def loop_audio(audio_segment, target_duration_ms):
    """
    循环音频到目标时长
    
    参数:
        audio_segment: 原始音频
        target_duration_ms: 目标时长 (毫秒)
    
    返回:
        AudioSegment: 循环后的音频
    """
    current_duration = len(audio_segment)
    
    if current_duration >= target_duration_ms:
        return audio_segment[:target_duration_ms]
    
    # 计算需要循环多少次
    loops_needed = math.ceil(target_duration_ms / current_duration)
    
    # 循环音频
    looped_audio = audio_segment
    for _ in range(loops_needed - 1):
        looped_audio = looped_audio + audio_segment
    
    # 裁剪到目标时长
    return looped_audio[:target_duration_ms]

def mix_subliminal_audio(affirmation_path, background_path, config):
    """
    混合潜意识音频
    
    参数:
        affirmation_path: 肯定句音频路径
        background_path: 背景音乐路径
        config: 配置参数
    
    返回:
        tuple: (成功标志, 输出路径或错误信息)
    """
    try:
        print("="*60)
        print("开始处理潜意识音频...")
        print("="*60)
        
        # 1. 加载音频文件
        print("1. 加载音频文件...")
        affirmation_audio = AudioSegment.from_file(affirmation_path)
        background_audio = AudioSegment.from_file(background_path)
        
        print(f"   -> 肯定句时长: {len(affirmation_audio)/1000:.2f}秒")
        print(f"   -> 背景音乐时长: {len(background_audio)/1000:.2f}秒")
        
        # 2. 处理潜意识轨（高频调制）
        print("2. 处理潜意识轨（高频调制）...")
        subliminal_audio = process_silent_subliminal(
            affirmation_audio, 
            config['carrier_freq'],
            CONFIG['sample_rate']
        )
        
        # 标准化
        subliminal_audio = normalize_audio(subliminal_audio)
        
        # 调整音量
        subliminal_audio = subliminal_audio + config['subliminal_volume_db']
        print(f"   -> 潜意识轨音量: {config['subliminal_volume_db']}dB")
        
        # 3. 处理背景音乐
        print("3. 处理背景音乐...")
        background_audio = background_audio + config['background_volume_db']
        print(f"   -> 背景音乐音量: {config['background_volume_db']}dB")
        
        # 4. 音轨对齐（循环到相同长度）
        print("4. 音轨对齐...")
        max_duration = max(len(subliminal_audio), len(background_audio))
        print(f"   -> 目标时长: {max_duration/1000:.2f}秒")
        
        # 循环潜意识轨
        if len(subliminal_audio) < max_duration:
            print("   -> 循环潜意识轨...")
            subliminal_audio = loop_audio(subliminal_audio, max_duration)
        
        # 循环背景音乐
        if len(background_audio) < max_duration:
            print("   -> 循环背景音乐...")
            background_audio = loop_audio(background_audio, max_duration)
        
        # 5. 生成双耳搏动（如果启用）
        final_mix = background_audio
        if config.get('enable_binaural', False):
            print("5. 生成双耳搏动...")
            binaural_beat = generate_binaural_beat(
                max_duration,
                config['binaural_left_freq'],
                config['binaural_right_freq'],
                config['binaural_volume_db']
            )
            print(f"   -> 双耳搏动音量: {config['binaural_volume_db']}dB")
        else:
            print("5. 跳过双耳搏动生成（未启用）")
            binaural_beat = None
        
        # 6. 混合所有音轨
        print("6. 混合音轨...")
        
        # 将潜意识轨转换为立体声
        subliminal_stereo = AudioSegment.from_mono_audiosegments(
            subliminal_audio, subliminal_audio
        )
        
        # 混合背景音乐和潜意识轨
        final_mix = background_audio.overlay(subliminal_stereo)
        
        # 混合双耳搏动
        if binaural_beat:
            final_mix = final_mix.overlay(binaural_beat)
        
        # 7. 标准化最终混音
        print("7. 标准化最终混音...")
        final_mix = normalize_audio(final_mix, -1)
        
        # 8. 导出
        print("8. 导出音频文件...")
        output_filename = f"Subliminal_Master_{int(time.time())}.wav"
        output_path = os.path.join(CONFIG['output_folder'], output_filename)
        
        # 导出为无损WAV格式（使用scipy避免ffmpeg依赖）
        # 确保是立体声
        if final_mix.channels == 1:
            final_mix = AudioSegment.from_mono_audiosegments(final_mix, final_mix)
        
        # 转换为numpy数组
        samples = np.array(final_mix.get_array_of_samples())
        
        # 重塑为立体声格式
        if final_mix.channels == 2:
            samples = samples.reshape((-1, 2))
        
        # 使用scipy导出WAV
        wavfile.write(output_path, final_mix.frame_rate, samples.astype(np.int16))
        
        print("="*60)
        print(f"✅ 处理完成! 输出文件: {output_filename}")
        print(f"   -> 文件大小: {os.path.getsize(output_path)/1024/1024:.2f}MB")
        print(f"   -> 时长: {len(final_mix)/1000:.2f}秒")
        print("="*60)
        
        return True, output_path
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

# --- 第四步：Web界面 ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subliminal Master - 潜意识音频合成引擎</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: #e0e5ec;
            min-height: 100vh;
            padding: 30px;
            color: #2d3436;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: #e0e5ec;
            border-radius: 30px;
            padding: 50px;
            box-shadow: 
                20px 20px 60px #b8bec7,
                -20px -20px 60px #ffffff;
        }
        
        h1 {
            text-align: center;
            color: #6c5ce7;
            margin-bottom: 10px;
            font-size: 2.5em;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(108, 92, 231, 0.2);
        }
        
        .subtitle {
            text-align: center;
            color: #636e72;
            margin-bottom: 40px;
            font-size: 1.1em;
            font-weight: 400;
        }
        
        .section {
            background: #e0e5ec;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 
                8px 8px 20px #b8bec7,
                -8px -8px 20px #ffffff;
        }
        
        .section-title {
            font-size: 1.3em;
            color: #6c5ce7;
            margin-bottom: 20px;
            font-weight: 600;
            display: flex;
            align-items: center;
        }
        
        .section-title span {
            margin-right: 12px;
            font-size: 1.4em;
        }
        
        .upload-area {
            border: none;
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: #e0e5ec;
            margin-bottom: 15px;
            box-shadow: 
                6px 6px 12px #b8bec7,
                -6px -6px 12px #ffffff;
        }
        
        .upload-area:hover {
            box-shadow: 
                8px 8px 16px #b8bec7,
                -8px -8px 16px #ffffff;
            transform: translateY(-2px);
        }
        
        .upload-area:active {
            box-shadow: 
                inset 4px 4px 8px #b8bec7,
                inset -4px -4px 8px #ffffff;
        }
        
        .upload-area.dragover {
            box-shadow: 
                inset 4px 4px 8px #b8bec7,
                inset -4px -4px 8px #ffffff;
        }
        
        .upload-area.has-file {
            box-shadow: 
                inset 4px 4px 8px #b8bec7,
                inset -4px -4px 8px #ffffff;
        }
        
        .upload-area strong {
            color: #6c5ce7;
            font-size: 1.1em;
        }
        
        .file-info {
            margin-top: 15px;
            padding: 15px 20px;
            background: #e0e5ec;
            border-radius: 15px;
            display: none;
            box-shadow: 
                inset 3px 3px 6px #b8bec7,
                inset -3px -3px 6px #ffffff;
        }
        
        .file-info.show {
            display: block;
        }
        
        .param-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
        }
        
        .param-item {
            display: flex;
            flex-direction: column;
        }
        
        .param-item label {
            color: #2d3436;
            font-weight: 500;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            font-size: 0.95em;
        }
        
        .param-item label span {
            color: #6c5ce7;
            font-weight: 700;
            font-size: 1.1em;
        }
        
        .slider-container {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .slider {
            flex: 1;
            -webkit-appearance: none;
            width: 100%;
            height: 10px;
            border-radius: 10px;
            background: #e0e5ec;
            outline: none;
            box-shadow: 
                inset 4px 4px 8px #b8bec7,
                inset -4px -4px 8px #ffffff;
        }
        
        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: #6c5ce7;
            cursor: pointer;
            box-shadow: 
                4px 4px 8px #b8bec7,
                -4px -4px 8px #ffffff;
            transition: all 0.2s ease;
        }
        
        .slider::-webkit-slider-thumb:hover {
            transform: scale(1.1);
            box-shadow: 
                6px 6px 12px #b8bec7,
                -6px -6px 12px #ffffff;
        }
        
        .slider::-moz-range-thumb {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: #6c5ce7;
            cursor: pointer;
            border: none;
            box-shadow: 
                4px 4px 8px #b8bec7,
                -4px -4px 8px #ffffff;
        }
        
        .slider-value {
            min-width: 65px;
            text-align: right;
            font-weight: 700;
            color: #6c5ce7;
            font-size: 1.1em;
        }
        
        .checkbox-container {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 20px;
            background: #e0e5ec;
            border-radius: 15px;
            margin-top: 15px;
            box-shadow: 
                4px 4px 8px #b8bec7,
                -4px -4px 8px #ffffff;
        }
        
        .checkbox-container input[type="checkbox"] {
            width: 22px;
            height: 22px;
            cursor: pointer;
            accent-color: #6c5ce7;
        }
        
        .checkbox-container label {
            cursor: pointer;
            color: #2d3436;
            font-weight: 500;
            font-size: 1em;
        }
        
        .btn {
            background: #e0e5ec;
            border: none;
            padding: 18px 35px;
            border-radius: 15px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            color: #2d3436;
            box-shadow: 
                6px 6px 12px #b8bec7,
                -6px -6px 12px #ffffff;
            transition: all 0.3s ease;
        }
        
        .btn:hover {
            box-shadow: 
                8px 8px 16px #b8bec7,
                -8px -8px 16px #ffffff;
            transform: translateY(-2px);
        }
        
        .btn:active {
            box-shadow: 
                inset 4px 4px 8px #b8bec7,
                inset -4px -4px 8px #ffffff;
            transform: translateY(0);
        }
        
        .btn-primary {
            background: linear-gradient(145deg, #7c6df2, #5c4bd7);
            color: white;
            box-shadow: 
                6px 6px 12px #b8bec7,
                -6px -6px 12px #ffffff;
        }
        
        .btn-success {
            background: linear-gradient(145deg, #00d2a3, #00a882);
            color: white;
            box-shadow: 
                6px 6px 12px #b8bec7,
                -6px -6px 12px #ffffff;
        }
        
        .button-group {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-top: 30px;
        }
        
        .progress-container {
            margin-top: 25px;
            display: none;
        }
        
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e0e5ec;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 
                inset 4px 4px 8px #b8bec7,
                inset -4px -4px 8px #ffffff;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #6c5ce7, #a29bfe);
            width: 0%;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 0.9em;
        }
        
        .status-text {
            text-align: center;
            margin-top: 15px;
            color: #6c5ce7;
            font-weight: 600;
            font-size: 1.1em;
        }
        
        .result-container {
            margin-top: 25px;
            display: none;
        }
        
        .result-item {
            background: #e0e5ec;
            padding: 30px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 
                8px 8px 16px #b8bec7,
                -8px -8px 16px #ffffff;
        }
        
        .result-item .filename {
            color: #6c5ce7;
            font-weight: 700;
            font-size: 1.3em;
            margin-bottom: 20px;
        }
        
        .download-btn {
            background: linear-gradient(145deg, #6c5ce7, #5c4bd7);
            color: white;
            text-decoration: none;
            padding: 15px 35px;
            border-radius: 15px;
            font-weight: 600;
            display: inline-block;
            font-size: 1.1em;
            box-shadow: 
                6px 6px 12px #b8bec7,
                -6px -6px 12px #ffffff;
            transition: all 0.3s ease;
        }
        
        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 
                8px 8px 16px #b8bec7,
                -8px -8px 16px #ffffff;
        }
        
        .alert {
            padding: 18px 25px;
            border-radius: 15px;
            margin-bottom: 25px;
            display: none;
            font-weight: 500;
        }
        
        .alert-success {
            background: #e0e5ec;
            color: #00b894;
            box-shadow: 
                4px 4px 8px #b8bec7,
                -4px -4px 8px #ffffff;
        }
        
        .alert-error {
            background: #e0e5ec;
            color: #e17055;
            box-shadow: 
                4px 4px 8px #b8bec7,
                -4px -4px 8px #ffffff;
        }
        
        .info-box {
            background: #e0e5ec;
            padding: 18px;
            border-radius: 15px;
            margin-top: 15px;
            font-size: 0.9em;
            color: #636e72;
            box-shadow: 
                inset 3px 3px 6px #b8bec7,
                inset -3px -3px 6px #ffffff;
        }
        
        .info-box strong {
            color: #6c5ce7;
        }
        
        @media (max-width: 600px) {
            body {
                padding: 15px;
            }
            
            .container {
                padding: 25px;
                border-radius: 20px;
            }
            
            h1 {
                font-size: 1.8em;
            }
            
            .section {
                padding: 20px;
            }
            
            .button-group {
                flex-direction: column;
            }
            
            .btn {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎧 Subliminal Master</h1>
        <p class="subtitle">潜意识音频合成引擎 - 一键生成专业潜意识音频</p>
        
        <div id="alertBox" class="alert"></div>
        
        <!-- 输入模块 -->
        <div class="section">
            <div class="section-title"><span>📁</span> 输入模块 - 上传音频文件</div>
            
            <!-- Track A: 肯定句音频 -->
            <div class="upload-area" id="affirmationArea">
                <p><strong>Track A: 肯定句音频</strong></p>
                <p style="color: #636e72; margin-top: 10px;">点击或拖拽上传您的肯定句录音（TTS生成的语音）</p>
                <p style="color: #636e72; font-size: 0.9em;">支持格式: MP3, WAV, M4A, AAC, FLAC</p>
                <input type="file" id="affirmationInput" accept=".mp3,.wav,.m4a,.aac,.flac" style="display: none;">
            </div>
            <div class="file-info" id="affirmationInfo">
                <strong>已选择:</strong> <span id="affirmationName"></span>
            </div>
            
            <!-- Track B: 背景音乐 -->
            <div class="upload-area" id="backgroundArea">
                <p><strong>Track B: 背景音乐</strong></p>
                <p style="color: #636e72; margin-top: 10px;">点击或拖拽上传冥想音乐、白噪音或大自然声音</p>
                <p style="color: #636e72; font-size: 0.9em;">支持格式: MP3, WAV, M4A, AAC, FLAC</p>
                <input type="file" id="backgroundInput" accept=".mp3,.wav,.m4a,.aac,.flac" style="display: none;">
            </div>
            <div class="file-info" id="backgroundInfo">
                <strong>已选择:</strong> <span id="backgroundName"></span>
            </div>
        </div>
        
        <!-- 处理参数 -->
        <div class="section">
            <div class="section-title"><span>⚙️</span> 处理参数 - 高频调制设置</div>
            
            <div class="param-grid">
                <!-- 载波频率 -->
                <div class="param-item">
                    <label>
                        载波频率 (Hz)
                        <span id="carrierValue">17500</span>
                    </label>
                    <div class="slider-container">
                        <input type="range" class="slider" id="carrierFreq" 
                               min="15000" max="20000" value="17500" step="100">
                    </div>
                    <div class="info-box">
                        <strong>说明:</strong> 将人声调制到此频率，使其变得"听不见"<br>
                        建议范围: 17500-19500Hz
                    </div>
                </div>
                
                <!-- 潜意识轨音量 -->
                <div class="param-item">
                    <label>
                        潜意识轨音量 (dB)
                        <span id="subliminalValue">-23</span>
                    </label>
                    <div class="slider-container">
                        <input type="range" class="slider" id="subliminalVolume" 
                               min="-40" max="0" value="-23" step="1">
                    </div>
                    <div class="info-box">
                        <strong>推荐值:</strong> -23dB（黄金值）<br>
                        过大会被听到，过小效果减弱
                    </div>
                </div>
                
                <!-- 背景音乐音量 -->
                <div class="param-item">
                    <label>
                        背景音乐音量 (dB)
                        <span id="backgroundValue">0</span>
                    </label>
                    <div class="slider-container">
                        <input type="range" class="slider" id="backgroundVolume" 
                               min="-20" max="10" value="0" step="1">
                    </div>
                    <div class="info-box">
                        <strong>说明:</strong> 背景音乐的音量<br>
                        0dB = 原始音量
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Theta波增强 -->
        <div class="section">
            <div class="section-title"><span>🧠</span> Theta波增强 - 双耳搏动生成器</div>
            
            <div class="checkbox-container">
                <input type="checkbox" id="enableBinaural" checked>
                <label for="enableBinaural">开启 Theta 波增强（推荐）</label>
            </div>
            
            <div id="binauralParams" style="margin-top: 15px;">
                <div class="param-grid">
                    <!-- 左耳频率 -->
                    <div class="param-item">
                        <label>
                            左耳频率 (Hz)
                            <span id="leftFreqValue">430</span>
                        </label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="leftFreq" 
                                   min="200" max="500" value="430" step="1">
                        </div>
                    </div>
                    
                    <!-- 右耳频率 -->
                    <div class="param-item">
                        <label>
                            右耳频率 (Hz)
                            <span id="rightFreqValue">434</span>
                        </label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="rightFreq" 
                                   min="200" max="500" value="434" step="1">
                        </div>
                    </div>
                    
                    <!-- 双耳搏动音量 -->
                    <div class="param-item">
                        <label>
                            双耳搏动音量 (dB)
                            <span id="binauralVolValue">-15</span>
                        </label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="binauralVolume" 
                                   min="-30" max="0" value="-15" step="1">
                        </div>
                    </div>
                </div>
                
                <div class="info-box" style="margin-top: 15px;">
                    <strong>Theta波说明:</strong><br>
                    当前差频: <span id="thetaDiff">4</span>Hz<br>
                    Theta波 (4-8Hz) 有助于放松、冥想和潜意识接收<br>
                    差频 = 右耳频率 - 左耳频率
                </div>
            </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="button-group">
            <button class="btn btn-primary" id="processBtn" onclick="startProcessing()">
                🎵 开始合成
            </button>
            <button class="btn" onclick="resetAll()">
                🔄 重置
            </button>
        </div>
        
        <!-- 进度显示 -->
        <div class="progress-container" id="progressContainer">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <p class="status-text" id="statusText">准备处理...</p>
        </div>
        
        <!-- 结果显示 -->
        <div class="result-container" id="resultContainer">
            <div class="result-item">
                <div class="filename" id="resultFilename"></div>
                <a href="#" id="downloadLink" class="download-btn">📥 下载音频文件</a>
            </div>
        </div>
        
        <!-- 使用说明 -->
        <div class="section" style="margin-top: 30px;">
            <div class="section-title"><span>💡</span> 使用说明</div>
            <div class="info-box">
                <strong>核心逻辑:</strong><br>
                隐藏轨（处理后的肯定句）+ 显性轨（背景音乐）+ 频率诱导（可选的双耳搏动）= 最终成品<br><br>
                
                <strong>重要提示:</strong><br>
                • 导出格式为无损WAV，保证高频信息不被压缩损失<br>
                • 请勿转换为MP3，否则17.5kHz以上的高频信号会被删除<br>
                • 建议使用高质量耳机聆听，获得最佳双耳搏动效果<br>
                • 每天聆听1-2次，每次15-30分钟，持续66天效果最佳
            </div>
        </div>
    </div>
    
    <script>
        let affirmationFile = null;
        let backgroundFile = null;
        
        // 文件上传处理
        function setupUploadArea(areaId, inputId, infoId, nameId, fileVar) {
            const area = document.getElementById(areaId);
            const input = document.getElementById(inputId);
            const info = document.getElementById(infoId);
            const name = document.getElementById(nameId);
            
            area.addEventListener('click', () => input.click());
            
            area.addEventListener('dragover', (e) => {
                e.preventDefault();
                area.classList.add('dragover');
            });
            
            area.addEventListener('dragleave', () => {
                area.classList.remove('dragover');
            });
            
            area.addEventListener('drop', (e) => {
                e.preventDefault();
                area.classList.remove('dragover');
                if (e.dataTransfer.files.length > 0) {
                    handleFile(e.dataTransfer.files[0], area, info, name, fileVar);
                }
            });
            
            input.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    handleFile(e.target.files[0], area, info, name, fileVar);
                }
            });
        }
        
        function handleFile(file, area, info, name, fileVar) {
            if (fileVar === 'affirmation') {
                affirmationFile = file;
            } else {
                backgroundFile = file;
            }
            
            area.classList.add('has-file');
            info.classList.add('show');
            name.textContent = file.name;
        }
        
        setupUploadArea('affirmationArea', 'affirmationInput', 'affirmationInfo', 'affirmationName', 'affirmation');
        setupUploadArea('backgroundArea', 'backgroundInput', 'backgroundInfo', 'backgroundName', 'background');
        
        // 滑动条值更新
        function setupSlider(sliderId, valueId, suffix = '') {
            const slider = document.getElementById(sliderId);
            const value = document.getElementById(valueId);
            
            slider.addEventListener('input', () => {
                value.textContent = slider.value + suffix;
            });
        }
        
        setupSlider('carrierFreq', 'carrierValue');
        setupSlider('subliminalVolume', 'subliminalValue');
        setupSlider('backgroundVolume', 'backgroundValue');
        setupSlider('leftFreq', 'leftFreqValue');
        setupSlider('rightFreq', 'rightFreqValue');
        setupSlider('binauralVolume', 'binauralVolValue');
        
        // Theta波差频计算
        function updateThetaDiff() {
            const left = parseInt(document.getElementById('leftFreq').value);
            const right = parseInt(document.getElementById('rightFreq').value);
            document.getElementById('thetaDiff').textContent = Math.abs(right - left);
        }
        
        document.getElementById('leftFreq').addEventListener('input', updateThetaDiff);
        document.getElementById('rightFreq').addEventListener('input', updateThetaDiff);
        
        // 双耳搏动开关
        document.getElementById('enableBinaural').addEventListener('change', (e) => {
            document.getElementById('binauralParams').style.display = e.target.checked ? 'block' : 'none';
        });
        
        // 显示提示
        function showAlert(message, type) {
            const alertBox = document.getElementById('alertBox');
            alertBox.textContent = message;
            alertBox.className = `alert alert-${type}`;
            alertBox.style.display = 'block';
            
            setTimeout(() => {
                alertBox.style.display = 'none';
            }, 5000);
        }
        
        // 重置
        function resetAll() {
            affirmationFile = null;
            backgroundFile = null;
            
            document.getElementById('affirmationArea').classList.remove('has-file');
            document.getElementById('backgroundArea').classList.remove('has-file');
            document.getElementById('affirmationInfo').classList.remove('show');
            document.getElementById('backgroundInfo').classList.remove('show');
            document.getElementById('progressContainer').style.display = 'none';
            document.getElementById('resultContainer').style.display = 'none';
            
            // 重置滑动条
            document.getElementById('carrierFreq').value = 17500;
            document.getElementById('carrierValue').textContent = '17500';
            document.getElementById('subliminalVolume').value = -23;
            document.getElementById('subliminalValue').textContent = '-23';
            document.getElementById('backgroundVolume').value = 0;
            document.getElementById('backgroundValue').textContent = '0';
            document.getElementById('leftFreq').value = 430;
            document.getElementById('leftFreqValue').textContent = '430';
            document.getElementById('rightFreq').value = 434;
            document.getElementById('rightFreqValue').textContent = '434';
            document.getElementById('binauralVolume').value = -15;
            document.getElementById('binauralVolValue').textContent = '-15';
            document.getElementById('thetaDiff').textContent = '4';
        }
        
        // 开始处理
        async function startProcessing() {
            if (!affirmationFile || !backgroundFile) {
                showAlert('请先上传肯定句音频和背景音乐！', 'error');
                return;
            }
            
            const processBtn = document.getElementById('processBtn');
            const progressContainer = document.getElementById('progressContainer');
            const progressFill = document.getElementById('progressFill');
            const statusText = document.getElementById('statusText');
            const resultContainer = document.getElementById('resultContainer');
            
            processBtn.disabled = true;
            progressContainer.style.display = 'block';
            resultContainer.style.display = 'none';
            
            const config = {
                carrier_freq: parseInt(document.getElementById('carrierFreq').value),
                subliminal_volume_db: parseInt(document.getElementById('subliminalVolume').value),
                background_volume_db: parseInt(document.getElementById('backgroundVolume').value),
                enable_binaural: document.getElementById('enableBinaural').checked,
                binaural_left_freq: parseInt(document.getElementById('leftFreq').value),
                binaural_right_freq: parseInt(document.getElementById('rightFreq').value),
                binaural_volume_db: parseInt(document.getElementById('binauralVolume').value)
            };
            
            // 模拟进度
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += Math.random() * 10;
                if (progress > 90) progress = 90;
                progressFill.style.width = progress + '%';
                progressFill.textContent = Math.round(progress) + '%';
            }, 500);
            
            statusText.textContent = '正在上传文件...';
            
            const formData = new FormData();
            formData.append('affirmation', affirmationFile);
            formData.append('background', backgroundFile);
            formData.append('config', JSON.stringify(config));
            
            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                clearInterval(progressInterval);
                
                if (result.success) {
                    progressFill.style.width = '100%';
                    progressFill.textContent = '100%';
                    statusText.textContent = '✅ 处理完成!';
                    
                    resultContainer.style.display = 'block';
                    document.getElementById('resultFilename').textContent = result.output_filename;
                    document.getElementById('downloadLink').href = '/download/' + result.output_filename;
                    
                    showAlert('潜意识音频合成成功！', 'success');
                } else {
                    statusText.textContent = '❌ 处理失败';
                    showAlert('处理失败: ' + result.error, 'error');
                }
            } catch (error) {
                clearInterval(progressInterval);
                statusText.textContent = '❌ 处理失败';
                showAlert('处理失败: ' + error.message, 'error');
            }
            
            processBtn.disabled = false;
        }
    </script>
</body>
</html>
"""

# --- 第五步：Flask路由 ---

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/process', methods=['POST'])
def process():
    """处理音频文件"""
    try:
        affirmation_file = request.files['affirmation']
        background_file = request.files['background']
        config = json.loads(request.form['config'])
        
        # 保存上传的文件
        affirmation_path = os.path.join(CONFIG['upload_folder'], secure_filename(affirmation_file.filename))
        background_path = os.path.join(CONFIG['upload_folder'], secure_filename(background_file.filename))
        
        affirmation_file.save(affirmation_path)
        background_file.save(background_path)
        
        # 处理音频
        success, result = mix_subliminal_audio(affirmation_path, background_path, config)
        
        if success:
            return jsonify({
                'success': True,
                'output_filename': os.path.basename(result)
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/download/<filename>')
def download(filename):
    """下载处理后的文件"""
    try:
        return send_file(
            os.path.join(CONFIG['output_folder'], filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return str(e), 404

# --- 第六步：主程序 ---

if __name__ == '__main__':
    print("="*60)
    print(" 🚀 Subliminal Master - 潜意识音频合成引擎 启动")
    print("="*60)
    print("\n请在浏览器中打开: http://localhost:5000")
    print("\n按 Ctrl+C 停止服务器\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
