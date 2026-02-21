# -*- coding: utf-8 -*-
"""
Subliminal Master 音频处理核心模块
包含所有音频处理相关的核心函数
"""

import os
import math
import time
import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment
from pydub.generators import Sine
from config import Config
from logger import logger, log_processing_step


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
    logger.debug(f"生成双耳搏动: {left_freq}Hz / {right_freq}Hz, 差频{right_freq-left_freq}Hz")
    
    left_channel = Sine(left_freq).to_audio_segment(duration=duration_ms)
    right_channel = Sine(right_freq).to_audio_segment(duration=duration_ms)
    
    binaural_beat = AudioSegment.from_mono_audiosegments(left_channel, right_channel)
    binaural_beat = binaural_beat + volume_db
    
    return binaural_beat


def process_silent_subliminal(audio_segment, carrier_freq, sample_rate=None):
    """
    使用振幅调制 (Amplitude Modulation) 将音频移至高频段
    实现"无声潜意识"效果
    
    数学原理：
    调制信号 = 原始信号 × 载波信号
    s(t) = m(t) × cos(2πfc×t)
    其中 fc 为载波频率（17500Hz），m(t) 为原始音频信号
    
    参数:
        audio_segment: 原始音频 (AudioSegment)
        carrier_freq: 载波频率 (Hz)
        sample_rate: 采样率 (可选)
    
    返回:
        AudioSegment: 处理后的静默阈下音频
    """
    if sample_rate is None:
        sample_rate = Config.SAMPLE_RATE
    
    logger.debug(f"高频调制处理: 载波频率 {carrier_freq}Hz")
    
    audio = audio_segment.set_channels(1).set_frame_rate(sample_rate)
    
    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    
    if len(samples) == 0:
        logger.warning("音频为空，返回静默音频")
        return AudioSegment.silent(duration=len(audio_segment), frame_rate=sample_rate)
    
    duration_sec = len(samples) / sample_rate
    t = np.linspace(0, duration_sec, len(samples), endpoint=False)
    carrier = np.sin(2 * np.pi * carrier_freq * t)
    
    modulated_signal = samples * carrier
    
    max_val = np.max(np.abs(modulated_signal))
    if max_val > 0:
        modulated_signal = (modulated_signal / max_val) * (2**15 - 1)
    else:
        modulated_signal = np.zeros_like(modulated_signal)
    
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
    if audio_segment.dBFS == float('-inf'):
        return audio_segment
    change_in_dB = target_db - audio_segment.dBFS
    return audio_segment.apply_gain(change_in_dB)


def loop_audio(audio_segment, target_duration_ms):
    """
    循环音频到目标时长（优化版）
    
    使用乘法代替循环拼接，时间复杂度从 O(n²) 降低到 O(n)
    
    参数:
        audio_segment: 原始音频
        target_duration_ms: 目标时长 (毫秒)
    
    返回:
        AudioSegment: 循环后的音频
    """
    current_duration = len(audio_segment)
    
    if current_duration >= target_duration_ms:
        return audio_segment[:target_duration_ms]
    
    if current_duration == 0:
        return AudioSegment.silent(duration=target_duration_ms)
    
    loops_needed = math.ceil(target_duration_ms / current_duration)
    
    looped_audio = audio_segment * loops_needed
    
    return looped_audio[:target_duration_ms]


def validate_audio_file(file_path):
    """
    验证音频文件是否有效
    
    参数:
        file_path: 音频文件路径
    
    返回:
        tuple: (是否有效, 错误信息或音频信息)
    """
    try:
        audio = AudioSegment.from_file(file_path)
        
        if len(audio) == 0:
            return False, "音频时长为0"
        
        if audio.frame_rate == 0:
            return False, "采样率无效"
        
        info = {
            'duration_ms': len(audio),
            'duration_sec': len(audio) / 1000,
            'channels': audio.channels,
            'sample_rate': audio.frame_rate,
            'sample_width': audio.sample_width
        }
        return True, info
    except Exception as e:
        return False, str(e)


def mix_subliminal_audio(affirmation_path, background_path, config, progress_callback=None):
    """
    混合潜意识音频
    
    参数:
        affirmation_path: 肯定句音频路径
        background_path: 背景音乐路径
        config: 配置参数字典
        progress_callback: 进度回调函数 (可选)
    
    返回:
        tuple: (成功标志, 输出路径或错误信息)
    """
    try:
        def report_progress(step, total, message):
            if progress_callback:
                progress_callback(step, total, message)
            log_processing_step(logger, step, message)
        
        report_progress(1, 8, "加载音频文件...")
        
        affirmation_audio = AudioSegment.from_file(affirmation_path)
        background_audio = AudioSegment.from_file(background_path)
        
        if len(affirmation_audio) == 0:
            return False, "肯定句音频为空"
        if len(background_audio) == 0:
            return False, "背景音乐为空"
        
        logger.info(f"肯定句时长: {len(affirmation_audio)/1000:.2f}秒")
        logger.info(f"背景音乐时长: {len(background_audio)/1000:.2f}秒")
        
        report_progress(2, 8, "处理潜意识轨（高频调制）...")
        
        carrier_freq = config.get('carrier_freq', Config.DEFAULT_CARRIER_FREQ)
        subliminal_audio = process_silent_subliminal(
            affirmation_audio, 
            carrier_freq,
            Config.SAMPLE_RATE
        )
        
        subliminal_audio = normalize_audio(subliminal_audio)
        
        subliminal_volume = config.get('subliminal_volume_db', Config.DEFAULT_SUBLIMINAL_VOLUME)
        subliminal_audio = subliminal_audio + subliminal_volume
        logger.info(f"潜意识轨音量: {subliminal_volume}dB")
        
        report_progress(3, 8, "处理背景音乐...")
        
        background_volume = config.get('background_volume_db', Config.DEFAULT_BACKGROUND_VOLUME)
        background_audio = background_audio + background_volume
        logger.info(f"背景音乐音量: {background_volume}dB")
        
        report_progress(4, 8, "音轨对齐...")
        
        max_duration = max(len(subliminal_audio), len(background_audio))
        logger.info(f"目标时长: {max_duration/1000:.2f}秒")
        
        if len(subliminal_audio) < max_duration:
            subliminal_audio = loop_audio(subliminal_audio, max_duration)
        
        if len(background_audio) < max_duration:
            background_audio = loop_audio(background_audio, max_duration)
        
        report_progress(5, 8, "生成双耳搏动...")
        
        binaural_beat = None
        if config.get('enable_binaural', True):
            left_freq = config.get('binaural_left_freq', Config.DEFAULT_BINAURAL_LEFT)
            right_freq = config.get('binaural_right_freq', Config.DEFAULT_BINAURAL_RIGHT)
            binaural_volume = config.get('binaural_volume_db', Config.DEFAULT_BINAURAL_VOLUME)
            
            binaural_beat = generate_binaural_beat(
                max_duration,
                left_freq,
                right_freq,
                binaural_volume
            )
            logger.info(f"双耳搏动: {left_freq}Hz/{right_freq}Hz, 音量{binaural_volume}dB")
        else:
            logger.info("跳过双耳搏动生成（未启用）")
        
        report_progress(6, 8, "混合音轨...")
        
        subliminal_stereo = AudioSegment.from_mono_audiosegments(
            subliminal_audio, subliminal_audio
        )
        
        final_mix = background_audio.overlay(subliminal_stereo)
        
        if binaural_beat:
            final_mix = final_mix.overlay(binaural_beat)
        
        report_progress(7, 8, "标准化最终混音...")
        
        final_mix = normalize_audio(final_mix, Config.TARGET_DB)
        
        report_progress(8, 8, "导出音频文件...")
        
        output_filename = f"Subliminal_Master_{int(time.time())}.wav"
        output_path = os.path.join(Config.OUTPUT_FOLDER, output_filename)
        
        if final_mix.channels == 1:
            final_mix = AudioSegment.from_mono_audiosegments(final_mix, final_mix)
        
        samples = np.array(final_mix.get_array_of_samples())
        
        if final_mix.channels == 2:
            samples = samples.reshape((-1, 2))
        
        wavfile.write(output_path, final_mix.frame_rate, samples.astype(np.int16))
        
        file_size_mb = os.path.getsize(output_path) / 1024 / 1024
        duration_sec = len(final_mix) / 1000
        
        logger.info(f"处理完成! 输出: {output_filename}")
        logger.info(f"文件大小: {file_size_mb:.2f}MB, 时长: {duration_sec:.2f}秒")
        
        return True, {
            'output_path': output_path,
            'output_filename': output_filename,
            'file_size_mb': file_size_mb,
            'duration_sec': duration_sec
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"处理失败: {e}")
        logger.error(error_trace)
        # 不返回详细错误信息，避免泄露敏感路径
        return False, "音频处理过程中发生错误"
